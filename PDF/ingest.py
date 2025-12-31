import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

# print("Working directory:", os.getcwd()) 
# print("File exists:", os.path.exists("PDF/document.pdf"))

# 1. Load PDF
loader = PyPDFLoader("PDF/document.pdf")
documents = loader.load()

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
)
chunks = splitter.split_documents(documents)

# 3. Embeddings (1024‑dim, high‑quality)
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/e5-large-v2" #sentence-transformers/all-mpnet-base-v2
)

# 4. Build FAISS index
faiss_index = FAISS.from_documents(chunks, embeddings)

# 5. Save locally
faiss_index.save_local(os.environ["FAISS_INDEX"])

print("Ingestion complete. FAISS index saved to ./faiss_index")
