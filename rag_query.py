import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

load_dotenv()

# 1. Embeddings (must match Pinecone index dimension)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

# 2. Vectorstore + retriever
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=os.environ["INDEX_NAME"],
    embedding=embeddings,
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)

# 3. Format retrieved docs
def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

format_docs_runnable = RunnableLambda(format_docs)

# 4. Prompt template (modern)
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are a precise assistant. Use ONLY the provided context to answer. "
            "If the answer is not in the context, say you don't know.\n\n"
            "Context:\n{context}"
        )
    ),
    ("human", "{question}")
])

# 5. LLM (Groq)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.environ["GROQ_API_KEY"]
)

# 6. Output parser
parser = StrOutputParser()

# 7. Build LCEL RAG pipeline (best practice)
rag_chain = (
    {
        "context": retriever | format_docs_runnable,
        "question": RunnableLambda(lambda x: x)
    }
    | prompt
    | llm
    | parser
)

# 8. Helper function
def answer_question(question: str) -> str:
    return rag_chain.invoke(question)

if __name__ == "__main__":
    q = input("Ask a question: ")
    print("\n--- Answer ---\n")
    print(answer_question(q))
    print("\n--------------\n")
