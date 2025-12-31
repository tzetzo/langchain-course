# this file is used for the Ingestion - converting text into vectors and saving them in Pinecone!
# rag_query.py is used for the Query!
# article used to embed in Pinecone: https://medium.com/@EjiroOnose/vector-database-what-is-it-and-why-you-should-know-it-ae7e7dca82a4
# to verify the LLM is using Pinecone when answering user questions ask it a question exactly as it appears in the article - it should provide 1:1 answer (start rag_query.py for this purpose)!!!

import os
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# 1. Load document
loader = TextLoader("mediumblog1.txt", encoding="utf-8")
documents = loader.load()

# 2. Split into chunks (modern splitter)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
)
chunks = text_splitter.split_documents(documents)

# 3. Use modern, free, local embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

# 4. Store in Pinecone
vectorstore = PineconeVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    index_name=os.environ["INDEX_NAME"]
)

print("Ingestion complete.")
