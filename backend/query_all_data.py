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
    
    print("Loading vector store from disk...")
    
    # Must use the SAME embedding model as training
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'mps'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Load existing ChromaDB
    vectorstore = Chroma(
        persist_directory="./chroma_db_all",
        embedding_function=embeddings,
        collection_name="cve_all_collection"
    )
    
    # Get collection info
    collection = vectorstore._collection
    count = collection.count()
    
    print(f"✓ Vector store loaded successfully!")
    print(f"  Total CVEs in database: {count:,}")
    
    return vectorstore

def create_qa_chain(vectorstore):
    """Create a QA chain with LLM"""
    
    print("Initializing ChatGPT for responses...")
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 5}  # Return top 5 most relevant CVEs
    )
    
    template = """You are a cybersecurity expert assistant specializing in vulnerability analysis. 

Answer the user's question based on the following CVE vulnerability information from the National Vulnerability Database:

Context: {context}

Question: {question}

Provide a clear, accurate, and helpful answer. If the information isn't in the context, say so.

Answer:"""
    
    prompt = PromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("✓ QA Chain ready!\n")
    return qa_chain, retriever

def query_with_sources(qa_chain, retriever, query):
    """Query and display answer with sources"""
    
    print("\n" + "="*70)
    print(f"QUERY: {query}")
    print("="*70)
    
    # Get answer
    answer = qa_chain.invoke(query)
    
    # Get source documents
    source_docs = retriever.invoke(query)
    
    print("\nANSWER:")
    print("-"*70)
    print(answer)
    
    print("\n" + "="*70)
    print("SOURCE CVEs (Most Relevant):")
    print("="*70)
    for i, doc in enumerate(source_docs, 1):
        print(f"\n[{i}] {doc.metadata['cve_id']}")
        print(f"    Severity: {doc.metadata['cvss_severity']} (Score: {doc.metadata['cvss_score']})")
        print(f"    Status: {doc.metadata['vulnStatus']}")
        print(f"    Published: {doc.metadata['published'][:10]}")
    print("="*70)

def interactive_mode(qa_chain, retriever):
    """Interactive query mode - like a chatbot"""
    
    print("\n" + "="*70)
    print("🤖 CYBERRAG CHATBOT - Interactive Mode")
    print("="*70)
    print("\nAsk questions about CVE vulnerabilities!")
    print("Examples:")
    print("  - What are the most critical vulnerabilities in 2024?")
    print("  - Tell me about SQL injection vulnerabilities")
    print("  - What CVEs affect Windows Server?")
    print("  - Show me authentication bypass vulnerabilities")
    print("\nType 'exit', 'quit', or 'q' to stop")
    print("="*70 + "\n")
    
    while True:
        query = input("💬 You: ").strip()
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Goodbye!\n")
            break
        
        if not query:
            continue
        
        try:
            print("\n🤔 Thinking...\n")
            query_with_sources(qa_chain, retriever, query)
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print("\n")

if __name__ == "__main__":
    print("="*70)
    print("🔒 CYBERRAG - CVE Query System")
    print("="*70 + "\n")
    
    # Load vector store
    vectorstore = load_vectorstore()
    
    # Create QA chain
    qa_chain, retriever = create_qa_chain(vectorstore)
    
    # Run some example queries
    print("="*70)
    print("EXAMPLE QUERIES:")
    print("="*70)
    
    example_queries = [
        "What are the most critical vulnerabilities from 2024?",
        "Tell me about remote code execution vulnerabilities in Apache",
        "What CVEs have a CVSS score above 9.5?"
    ]
    
    for query in example_queries:
        query_with_sources(qa_chain, retriever, query)
        print("\n")
    
    # Enter interactive mode
    interactive_mode(qa_chain, retriever)