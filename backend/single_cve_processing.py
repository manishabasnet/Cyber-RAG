import os
import requests
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv('../.env')

#Fetching only one CVE from NVD API
def fetch_single_cve():
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {
        "pubStartDate": "2025-01-01T00:00:00.000",
        "pubEndDate": "2025-01-31T23:59:59.999",
        "resultsPerPage": 1
    }
    
    print("Fetching CVE from NVD API.")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('vulnerabilities'):
            cve = data['vulnerabilities'][0]['cve']
            print(f"Fetched CVE: {cve['id']}")
            return cve
        else:
            print("No CVE found in the response")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

# Converting CVE to LangChain Document
def cve_to_document(cve):
    """Convert one CVE JSON object to a LangChain Document"""
    
    # Extract the English description
    description = ""
    for desc in cve.get('descriptions', []):
        if desc['lang'] == 'en':
            description = desc['value']
            break
    
    # Extract CVSS score if available
    cvss_score = "N/A"
    cvss_severity = "N/A"
    
    metrics = cve.get('metrics', {})
    if 'cvssMetricV31' in metrics and len(metrics['cvssMetricV31']) > 0:
        cvss_data = metrics['cvssMetricV31'][0]['cvssData']
        cvss_score = cvss_data.get('baseScore', 'N/A')
        cvss_severity = cvss_data.get('baseSeverity', 'N/A')
    elif 'cvssMetricV2' in metrics and len(metrics['cvssMetricV2']) > 0:
        cvss_score = metrics['cvssMetricV2'][0]['cvssData'].get('baseScore', 'N/A')
        cvss_severity = metrics['cvssMetricV2'][0].get('baseSeverity', 'N/A')
    
    # Creating the document content
    content = f"""CVE ID: {cve['id']}
Status: {cve.get('vulnStatus', 'Unknown')}
Severity: {cvss_severity} (Score: {cvss_score})

Description:
{description}
"""
    
    # Create metadata (vulnerability attributes exvluding the embeddings above)
    metadata = {
        "cve_id": cve['id'],
        "published": cve['published'],
        "lastModified": cve['lastModified'],
        "vulnStatus": cve.get('vulnStatus', 'Unknown'),
        "cvss_score": str(cvss_score),
        "cvss_severity": cvss_severity,
        "source": "NVD"
    }
    
    # Creating LangChain Document
    doc = Document(
        page_content=content,
        metadata=metadata
    )
    
    print(f"Created document for {cve['id']}")
    return doc

#Embedding and store in ChromaDB
def embed_and_store(document):
    """Embedding the document and store in ChromaDB"""
    
    print("Initializing OpenAI embeddings...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )
    
    print("Creating ChromaDB vector store...")
    vectorstore = Chroma.from_documents(
        documents=[document],
        embedding=embeddings,
        persist_directory="./chroma_db",
        collection_name="cve_collection"
    )
    
    print("Document embedded and stored in ChromaDB!")
    return vectorstore

#Creating QA Chain with LLM
def create_qa_chain(vectorstore):
    """Create a QA chain with LLM for natural language responses"""
    
    print("Initializing ChatGPT for natural language responses...")
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    template = """Answer the question based on the following context about vulnerabilities:

Context: {context}

Question: {question}

Answer:"""
    
    prompt = PromptTemplate.from_template(template)
    
    # Create simple chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("✓ QA Chain created!")
    return qa_chain, retriever

# Updating the test_query function to use the QA chain
def test_query_with_llm(qa_chain, retriever, query):
    """Test querying with natural language response"""
    
    print(f"\nTesting query: '{query}'")
    
    # Get answer
    answer = qa_chain.invoke(query)
    
    # Get source docs
    source_docs = retriever.invoke(query)
    
    print("\n" + "="*60)
    print("NATURAL LANGUAGE RESPONSE:")
    print("="*60)
    print(answer)
    print("\n" + "="*60)
    print("SOURCE DOCUMENTS:")
    print("="*60)
    for i, doc in enumerate(source_docs, 1):
        print(f"\n[Source {i}] CVE ID: {doc.metadata['cve_id']}")
        print(f"Severity: {doc.metadata['cvss_severity']} (Score: {doc.metadata['cvss_score']})")
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("TESTING SINGLE CVE EMBEDDING WITH LLM")
    print("="*60 + "\n")
    
    cve = fetch_single_cve()
    
    if cve:
        document = cve_to_document(cve)
        vectorstore = embed_and_store(document)
        qa_chain, retriever = create_qa_chain(vectorstore)

        print("\n" + "="*60)
        print("TESTING NATURAL LANGUAGE RESPONSES")
        print("="*60)
        
        test_query_with_llm(qa_chain, retriever, "What vulnerabilities were published in 2025?")
        test_query_with_llm(qa_chain, retriever, "Tell me about CVE-2024-21675")
        test_query_with_llm(qa_chain, retriever, "Is this vulnerability critical?")
        
        print("\nTest completed successfully!")
    else:
        print("Failed to fetch CVE. Check your API connection.")