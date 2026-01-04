import os
from dotenv import load_dotenv
from urllib.parse import urlparse

from apify_client import ApifyClient
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# -----------------------------------------------------------------------------
# 1. Crawl LangChain docs via sitemap (faster + cleaner)
# -----------------------------------------------------------------------------

client = ApifyClient(os.environ["APIFY_API_TOKEN"])
actor_id = os.environ.get("APIFY_RAG_ACTOR_ID", "apify/website-content-crawler") # the string is a default value if APIFY_RAG_ACTOR_ID is not set

crawl_url = os.environ["CRAWL_URL"]
sitemap_url = os.environ.get("CRAWL_SITEMAP")

print(f"Crawling documentation from: {crawl_url}")
if sitemap_url:
    print(f"Using sitemap: {sitemap_url}")

parsed = urlparse(crawl_url)
domain = f"{parsed.scheme}://{parsed.netloc}"
include_pattern = rf"^{domain}/.*"
exclude_patterns = [
    rf"^{domain}/.*tag.*",
    rf"^{domain}/.*search.*",
]

run_input = {
    "startUrls": [{"url": crawl_url}],
    "sitemapUrls": [sitemap_url] if sitemap_url else [],
    # "sitemapUrls": [], # for testing purposes
    # "maxCrawlPages": 15, # useless when there is sitemap urls
    "maxRequestsPerCrawl": 5, # hard limit; Comment this option to scrape the full website.
    "crawlerType": "cheerio", # fast for static docs
    "includeHtml": False,
    "includeMarkdown": True,
    "includeText": True,
    "proxyConfiguration": {"useApifyProxy": True},
    "additionalUrlPatterns": [include_pattern],
    "excludeUrlPatterns": exclude_patterns, 
}

run = client.actor(actor_id).call(run_input=run_input)
items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
print(f"Fetched {len(items)} pages from Apify")

# -----------------------------------------------------------------------------
# 2. Extract Markdown and deduplicate by URL
# -----------------------------------------------------------------------------

seen_urls = set()
docs_text = []

for item in items:
    url = item.get("url")
    if url in seen_urls:
        continue
    seen_urls.add(url)

    md = item.get("markdown") or item.get("text") or ""
    if isinstance(md, str) and md.strip():
        docs_text.append(md)

full_text = "\n\n".join(docs_text)
print(f"Total characters collected: {len(full_text)} from {len(docs_text)} unique pages")

# -----------------------------------------------------------------------------
# 3. Split into chunks
# -----------------------------------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    # chunk_size=5000, # for testing purposes
    # chunk_overlap=0, # for testing purposes
    chunk_size=1000, # prod ready
    chunk_overlap=150, # prod ready
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
)

chunks = splitter.split_text(full_text)
print(f"Total chunks created: {len(chunks)}")

# -----------------------------------------------------------------------------
# 4. Embeddings (parallel batch mode)
# -----------------------------------------------------------------------------

embedding_model = os.environ["EMBEDDING_MODEL"]
embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

# BATCH_SIZE = 32 # for testing purposes
# MAX_WORKERS = 2 # for testing purposes
BATCH_SIZE = 256          # larger batch for speed
MAX_WORKERS = 1           # tune based on your CPU + RAM

def embed_batch(batch_texts):
    return embeddings.embed_documents(batch_texts)

def generate_batches(data, batch_size):
    for i in range(0, len(data), batch_size):
        yield i, data[i : i + batch_size]

print("Embedding chunks in parallel...")

embedded_batches = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(embed_batch, batch_texts): (start_idx, batch_texts)
        for start_idx, batch_texts in generate_batches(chunks, BATCH_SIZE)
    }

    for future in tqdm(as_completed(futures), total=len(futures), desc="Embedding"):
        start_idx, batch_texts = futures[future]
        batch_embeddings = future.result()
        embedded_batches.append((start_idx, batch_texts, batch_embeddings))

# Sort batches to preserve order (optional, but nice)
embedded_batches.sort(key=lambda x: x[0])

# Flatten back to aligned lists
all_texts = []
all_embeddings = []
for _, batch_texts, batch_embeddings in embedded_batches:
    all_texts.extend(batch_texts)
    all_embeddings.extend(batch_embeddings)

print(f"Total embeddings computed: {len(all_embeddings)}")

# -----------------------------------------------------------------------------
# 5. Pinecone setup (create index if missing)
# -----------------------------------------------------------------------------

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index_name = os.environ["PINECONE_INDEX_NAME"]
env = os.environ["PINECONE_ENVIRONMENT"]

existing_indexes = pc.list_indexes().names()
if index_name not in existing_indexes:
    print(f"Creating Pinecone index: {index_name}")
    pc.create_index(
        name=index_name,
        dimension=1024,           # e5-large-v2 dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=env),
    )

index = pc.Index(index_name)

# -----------------------------------------------------------------------------
# 6. Batch upload to Pinecone (large batches + progress)
# -----------------------------------------------------------------------------

UPSERT_BATCH_SIZE = 256

print("Uploading vectors to Pinecone...")

def upsert_batch(start_idx, texts, vectors):
    payload = [
        {
            "id": f"chunk-{start_idx + j}",
            "values": vectors[j],
            "metadata": {"text": texts[j]},
        }
        for j in range(len(texts))
    ]
    index.upsert(vectors=payload)

total = len(all_texts)
with tqdm(total=total, desc="Upserting", unit="vec") as pbar:
    for start in range(0, total, UPSERT_BATCH_SIZE):
        end = min(start + UPSERT_BATCH_SIZE, total)
        batch_texts = all_texts[start:end]
        batch_vecs = all_embeddings[start:end]

        upsert_batch(start, batch_texts, batch_vecs)
        pbar.update(len(batch_texts))

print("Ingestion complete. All vectors uploaded to Pinecone.")
