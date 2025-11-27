import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Disable tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

load_dotenv('../.env')

def load_vectorstore():
    """Load the existing ChromaDB vector store"""
    
    print("Loading existing vector store...")
    
    # Initialize the SAME embeddings model used for training
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'mps'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Load existing ChromaDB
    vectorstore = Chroma(
        persist_directory="./chroma_db_2024",
        embedding_function=embeddings,
        collection_name="cve_2024_collection"
    )
    
    print("✓ Vector store loaded successfully!")
    return vectorstore

def create_qa_chain(vectorstore):
    """Create a QA chain with LLM"""
    
    print("Initializing ChatGPT...")
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 5}  # Return top 5 most relevant CVEs
    )
    
    template = """You are a cybersecurity expert assistant. Answer the question based on the following vulnerability information:

Context: {context}

Question: {question}

Provide a clear and concise answer:"""
    
    prompt = PromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("✓ QA Chain ready!")
    return qa_chain, retriever

def query_with_sources(qa_chain, retriever, query):
    """Query the vector store and show sources"""
    
    print("\n" + "="*60)
    print(f"QUERY: {query}")
    print("="*60)
    
    # Get answer
    answer = qa_chain.invoke(query)
    
    # Get source documents
    source_docs = retriever.invoke(query)
    
    print("\nANSWER:")
    print("-"*60)
    print(answer)
    
    print("\n" + "="*60)
    print("SOURCE CVEs:")
    print("="*60)
    for i, doc in enumerate(source_docs, 1):
        print(f"\n[{i}] {doc.metadata['cve_id']}")
        print(f"    Severity: {doc.metadata['cvss_severity']} (Score: {doc.metadata['cvss_score']})")
        print(f"    Status: {doc.metadata['vulnStatus']}")
        print(f"    Published: {doc.metadata['published'][:10]}")
    print("="*60)

def interactive_mode(qa_chain, retriever):
    """Interactive query mode"""
    
    print("\n" + "="*60)
    print("INTERACTIVE MODE - Ask questions about 2024 CVEs")
    print("Type 'exit' or 'quit' to stop")
    print("="*60 + "\n")
    
    while True:
        query = input("Your question: ").strip()
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("\nGoodbye!")
            break
        
        if not query:
            continue
        
        try:
            query_with_sources(qa_chain, retriever, query)
        except Exception as e:
            print(f"\n✗ Error: {e}")
        
        print("\n")

if __name__ == "__main__":
    print("="*60)
    print("CVE 2024 DATA QUERY SYSTEM")
    print("="*60 + "\n")
    
    # Load vector store
    vectorstore = load_vectorstore()
    
    # Create QA chain
    qa_chain, retriever = create_qa_chain(vectorstore)
    
    # Example queries (you can comment these out)
    print("\n" + "="*60)
    print("EXAMPLE QUERIES:")
    print("="*60)
    
    query_with_sources(qa_chain, retriever, "What are the most critical vulnerabilities in 2024?")
    query_with_sources(qa_chain, retriever, "Tell me about Microsoft vulnerabilities")
    query_with_sources(qa_chain, retriever, "What vulnerabilities affect Linux?")
    
    # Interactive mode
    interactive_mode(qa_chain, retriever)