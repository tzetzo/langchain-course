from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
#from langchain_openai import ChatOpenAI
# from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama ### ChatOllama is client for http://localhost:11434

load_dotenv()

def main():
    # print("Hello from langchain-course!")
    prompt = PromptTemplate(
    template="What is the capital of {country}?",
    input_variables=["country"],
    )
    
    llm = ChatOllama(model="gemma3:270m", temperature=0.0)   # gemma3:270m is installed locally along with ollama
    # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    # llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.0)

    chain = prompt | llm

    result = chain.invoke({"country": "France"})
    print(result)


if __name__ == "__main__":
    main()
