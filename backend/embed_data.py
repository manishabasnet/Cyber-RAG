import os
import requests
import time
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Disable tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

load_dotenv('../.env')

def fetch_all_cves():
    """Fetch ALL CVEs using pagination (no date filter)"""
    
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    nvd_api_key = os.getenv('NVD_API_KEY')
    headers = {}
    if nvd_api_key:
        headers['apiKey'] = nvd_api_key
        print("Using NVD API key (50 requests per 30 seconds)")
    else:
        print("No API key found (5 requests per 30 seconds)")
    
    all_cves = []
    start_index = 0
    results_per_page = 2000  # Maximum allowed as per NVD API
    
    print(f"\n{'='*60}")
    print("FETCHING ALL CVEs FROM NVD")
    print(f"{'='*60}")
    
    # First request to get total count
    params = {
        "resultsPerPage": results_per_page,
        "startIndex": 0
    }
    
    print("Making initial request to get total CVE count...")
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        print(f"✗ Error: {response.status_code}")
        return []
    
    data = response.json()
    total_results = data.get('totalResults', 0)
    
    print(f"\n✓ Total CVEs in database: {total_results:,}")
    print(f"  Pages needed: {(total_results // results_per_page) + 1}")
    print(f"  CVEs per page: {results_per_page}")
    
    estimated_time = 0
    if nvd_api_key:
        estimated_time = (total_results / results_per_page) * 0.6
    else:
        estimated_time = (total_results / results_per_page) * 6
    
    print(f"  Estimated fetch time: {int(estimated_time//60)} min {int(estimated_time%60)} sec")
    print(f"\nStarting fetch...\n")
    
    # Process first batch
    vulnerabilities = data.get('vulnerabilities', [])
    for vuln in vulnerabilities:
        all_cves.append(vuln['cve'])
    
    print(f"[Page 1] Fetched {len(vulnerabilities):,} CVEs | Total: {len(all_cves):,}/{total_results:,}")
    
    start_index += results_per_page
    page_num = 2
    
    # Fetch remaining pages
    while start_index < total_results:
        params = {
            "resultsPerPage": results_per_page,
            "startIndex": start_index
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get('vulnerabilities', [])
                
                if not vulnerabilities:
                    break
                
                for vuln in vulnerabilities:
                    all_cves.append(vuln['cve'])
                
                progress = (len(all_cves) / total_results) * 100
                print(f"[Page {page_num}] Fetched {len(vulnerabilities):,} CVEs | Total: {len(all_cves):,}/{total_results:,} ({progress:.1f}%)")
                
                start_index += results_per_page
                page_num += 1
                
                # Rate limiting
                if nvd_api_key:
                    time.sleep(0.6)  # Safe with API key
                else:
                    time.sleep(6)    # Safe without API key
                    
            else:
                print(f"✗ Error on page {page_num}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"✗ Exception on page {page_num}: {e}")
            break
    
    print(f"\n{'='*60}")
    print(f"✓ FETCH COMPLETE!")
    print(f"  Total CVEs fetched: {len(all_cves):,}")
    print(f"{'='*60}")
    
    return all_cves

def cve_to_document(cve):
    """Convert CVE to Document"""
    
    description = ""
    for desc in cve.get('descriptions', []):
        if desc['lang'] == 'en':
            description = desc['value']
            break
    
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
    
    content = f"""CVE ID: {cve['id']}
Status: {cve.get('vulnStatus', 'Unknown')}
Severity: {cvss_severity} (Score: {cvss_score})

Description:
{description}
"""
    
    metadata = {
        "cve_id": cve['id'],
        "published": cve['published'],
        "lastModified": cve['lastModified'],
        "vulnStatus": cve.get('vulnStatus', 'Unknown'),
        "cvss_score": str(cvss_score),
        "cvss_severity": cvss_severity,
        "source": "NVD",
        "year": cve['published'][:4]
    }
    
    return Document(page_content=content, metadata=metadata)

def embed_and_store_batch(documents, embeddings, vectorstore=None):
    """Embed and store documents in batches"""
    
    if vectorstore is None:
        print("Creating new ChromaDB vector store...")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory="./chroma_db_all",
            collection_name="cve_all_collection"
        )
    else:
        vectorstore.add_documents(documents)
    
    return vectorstore

def process_all_cves():
    """Process all CVEs from NVD database"""
    
    print("="*60)
    print("EMBEDDING ALL CVE DATA (ENTIRE NVD DATABASE)")
    print("USING PAGINATION - NO DATE FILTERS")
    print("="*60)
    print("\nWARNING: This will take several hours!")
    print("The process will:")
    print("  1. Fetch all CVEs via pagination")
    print("  2. Convert to documents")
    print("  3. Embed using HuggingFace (local M3)")
    print("  4. Store in ChromaDB")
    print("\nPress Ctrl+C to cancel within 5 seconds...")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return
    
    # Fetch all CVEs
    print("\n" + "="*60)
    print("STEP 1: FETCHING ALL CVEs")
    print("="*60)
    fetch_start = time.time()
    
    cves = fetch_all_cves()
    
    fetch_end = time.time()
    fetch_time = fetch_end - fetch_start
    print(f"\n✓ Fetch completed in {int(fetch_time//60)}m {int(fetch_time%60)}s")
    
    if not cves:
        print("No CVEs fetched. Exiting.")
        return
    
    # Convert to documents
    print("\n" + "="*60)
    print("STEP 2: CONVERTING TO DOCUMENTS")
    print("="*60)
    
    documents = []
    failed_conversions = 0
    
    for i, cve in enumerate(cves, 1):
        try:
            doc = cve_to_document(cve)
            documents.append(doc)
            
            if i % 1000 == 0:
                print(f"Converted {i:,}/{len(cves):,} CVEs...")
                
        except Exception as e:
            failed_conversions += 1
            if failed_conversions <= 10:  # Only print first 10 errors
                print(f"✗ Error converting {cve.get('id', 'unknown')}: {e}")
    
    print(f"\n✓ Conversion complete!")
    print(f"  Successful: {len(documents):,}")
    print(f"  Failed: {failed_conversions:,}")
    
    # Initialize embeddings
    print("\n" + "="*60)
    print("STEP 3: INITIALIZING EMBEDDINGS")
    print("="*60)
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'mps'},
        encode_kwargs={'normalize_embeddings': True}
    )
    print("✓ Embeddings initialized (using M3 GPU)")
    
    # Embed and store
    print("\n" + "="*60)
    print("STEP 4: EMBEDDING AND STORING")
    print("="*60)
    
    embed_start = time.time()
    vectorstore = None
    batch_size = 100
    total_batches = (len(documents) - 1) // batch_size + 1
    
    print(f"Processing {len(documents):,} documents in batches of {batch_size}")
    print(f"Total batches: {total_batches:,}\n")
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        batch_num = i//batch_size + 1
        
        try:
            vectorstore = embed_and_store_batch(batch, embeddings, vectorstore)
            progress = (batch_num / total_batches) * 100
            print(f"[Batch {batch_num:,}/{total_batches:,}] Embedded {len(batch)} documents ({progress:.1f}%)")
            
        except KeyboardInterrupt:
            print(f"\n\n⚠ Interrupted by user at batch {batch_num}")
            print(f"Progress saved: {batch_num * batch_size:,} CVEs embedded")
            return
        except Exception as e:
            print(f"✗ Error on batch {batch_num}: {e}")
    
    embed_end = time.time()
    embed_time = embed_end - embed_start
    
    print("\n" + "="*60)
    print("EMBEDDING COMPLETE!")
    print("="*60)
    print(f"Total CVEs embedded: {len(documents):,}")
    print(f"Fetch time: {int(fetch_time//60)}m {int(fetch_time%60)}s")
    print(f"Embed time: {int(embed_time//60)}m {int(embed_time%60)}s")
    print(f"Vector store: ./chroma_db_all")
    print("="*60)

if __name__ == "__main__":
    overall_start = time.time()
    
    try:
        process_all_cves()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    finally:
        overall_end = time.time()
        total_time = overall_end - overall_start
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        print(f"\n✓ Total time: {hours}h {minutes}m {seconds}s")