import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Disable tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

load_dotenv('../.env')

# Fetch CVEs for a specific month
def fetch_cves_for_month(year, month):
    """Fetch all CVEs published in a specific month"""
    
    # Determine the last day of the month
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    # Create date strings
    start_date = f"{year}-{month:02d}-01T00:00:00.000"
    end_date = f"{next_year}-{next_month:02d}-01T00:00:00.000"
    
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # Get NVD API key
    nvd_api_key = os.getenv('NVD_API_KEY')
    headers = {}
    if nvd_api_key:
        headers['apiKey'] = nvd_api_key
    
    all_cves = []
    start_index = 0
    results_per_page = 2000  # Maximum allowed
    
    month_name = datetime(year, month, 1).strftime('%B')
    print(f"\n{'='*60}")
    print(f"Fetching CVEs for {month_name} {year}")
    print(f"{'='*60}")
    
    while True:
        params = {
            "pubStartDate": start_date,
            "pubEndDate": end_date,
            "resultsPerPage": results_per_page,
            "startIndex": start_index
        }
        
        print(f"Fetching results {start_index} to {start_index + results_per_page}...")
        
        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get('vulnerabilities', [])
                
                if not vulnerabilities:
                    break
                
                # Extract CVE objects
                for vuln in vulnerabilities:
                    all_cves.append(vuln['cve'])
                
                total_results = data.get('totalResults', 0)
                print(f"  ✓ Fetched {len(vulnerabilities)} CVEs (Total available: {total_results})")
                
                # Check if we've fetched all results
                if start_index + len(vulnerabilities) >= total_results:
                    break
                
                start_index += results_per_page
                
                # Rate limiting: sleep to avoid hitting API limits
                # With API key: 50 requests per 30 seconds
                # Without: 5 requests per 30 seconds
                if nvd_api_key:
                    time.sleep(0.6)  # Safe rate with API key
                else:
                    time.sleep(6)    # Safe rate without API key
                
            else:
                print(f"  ✗ Error: {response.status_code}")
                break
                
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            break
    
    print(f"✓ Total CVEs fetched for {month_name} {year}: {len(all_cves)}")
    return all_cves

# Convert CVE to Document
def cve_to_document(cve):
    """Convert a CVE JSON object to a LangChain Document"""
    
    # Extract English description
    description = ""
    for desc in cve.get('descriptions', []):
        if desc['lang'] == 'en':
            description = desc['value']
            break
    
    # Extract CVSS score
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
    
    # Create document content
    content = f"""CVE ID: {cve['id']}
Status: {cve.get('vulnStatus', 'Unknown')}
Severity: {cvss_severity} (Score: {cvss_score})

Description:
{description}
"""
    
    # Create metadata
    metadata = {
        "cve_id": cve['id'],
        "published": cve['published'],
        "lastModified": cve['lastModified'],
        "vulnStatus": cve.get('vulnStatus', 'Unknown'),
        "cvss_score": str(cvss_score),
        "cvss_severity": cvss_severity,
        "source": "NVD"
    }
    
    return Document(page_content=content, metadata=metadata)

# Embed and store documents in batches
def embed_and_store_batch(documents, embeddings, vectorstore=None):
    """Embed and store a batch of documents"""
    
    if vectorstore is None:
        print("Creating new ChromaDB vector store...")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory="./chroma_db_2024",
            collection_name="cve_2024_collection"
        )
    else:
        print(f"Adding {len(documents)} documents to existing vector store...")
        vectorstore.add_documents(documents)
    
    return vectorstore

# Main processing function
def process_all_2024():
    """Process all CVEs from 2024"""
    
    print("="*60)
    print("EMBEDDING ALL 2024 CVE DATA")
    print("="*60)
    
    # Initialize embeddings once
    print("\nInitializing HuggingFace embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'mps'},
        encode_kwargs={'normalize_embeddings': True}
    )
    print("Embeddings initialized")
    
    vectorstore = None
    total_cves_processed = 0
    
    # Process each month of 2024
    for month in range(1, 13):
        try:
            # Fetch CVEs for the month
            cves = fetch_cves_for_month(2024, month)
            
            if not cves:
                print(f"  No CVEs found for month {month}")
                continue
            
            # Convert to documents
            print(f"Converting {len(cves)} CVEs to documents...")
            documents = []
            for cve in cves:
                try:
                    doc = cve_to_document(cve)
                    documents.append(doc)
                except Exception as e:
                    print(f"  ✗ Error converting {cve.get('id', 'unknown')}: {e}")
            
            print(f"✓ Created {len(documents)} documents")
            
            # Embed and store in batches of 100
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                print(f"Embedding batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")
                vectorstore = embed_and_store_batch(batch, embeddings, vectorstore)
            
            total_cves_processed += len(documents)
            print(f"Month {month} complete. Total CVEs processed: {total_cves_processed}")
            
        except Exception as e:
            print(f"✗ Error processing month {month}: {e}")
            continue
    
    print("\n" + "="*60)
    print(f"EMBEDDING COMPLETE!")
    print(f"Total CVEs processed: {total_cves_processed}")
    print(f"Vector store location: ./chroma_db_2024")
    print("="*60)

if __name__ == "__main__":
    start_time = time.time()
    process_all_2024()
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print(f"\n✓ Total time: {minutes} minutes {seconds} seconds")