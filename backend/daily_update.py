import os
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

os.environ["TOKENIZERS_PARALLELISM"] = "false"

load_dotenv('../.env')

# File to track last update time
LAST_UPDATE_FILE = "last_update.txt"

def get_last_update_time():
    """Get the timestamp of the last update"""
    
    if os.path.exists(LAST_UPDATE_FILE):
        with open(LAST_UPDATE_FILE, 'r') as f:
            timestamp = f.read().strip()
            print(f"Last update was: {timestamp}")
            return timestamp
    else:
        # If no previous update, get CVEs from last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        timestamp = seven_days_ago.strftime("%Y-%m-%dT%H:%M:%S.000")
        print(f"No previous update found. Starting from: {timestamp}")
        return timestamp

def save_last_update_time(timestamp):
    """Save the current update timestamp"""
    
    with open(LAST_UPDATE_FILE, 'w') as f:
        f.write(timestamp)
    print(f"✓ Saved update timestamp: {timestamp}")

def fetch_modified_cves(start_date, end_date):
    """Fetch CVEs modified between start_date and end_date"""
    
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    nvd_api_key = os.getenv('NVD_API_KEY')
    headers = {}
    if nvd_api_key:
        headers['apiKey'] = nvd_api_key
    
    all_cves = []
    start_index = 0
    results_per_page = 2000
    
    print(f"\n{'='*60}")
    print(f"Fetching modified CVEs")
    print(f"From: {start_date}")
    print(f"To:   {end_date}")
    print(f"{'='*60}")
    
    while True:
        params = {
            "lastModStartDate": start_date,
            "lastModEndDate": end_date,
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
                
                total_results = data.get('totalResults', 0)
                print(f"Fetched {len(vulnerabilities)} CVEs | Total: {len(all_cves)}/{total_results}")
                
                if start_index + len(vulnerabilities) >= total_results:
                    break
                
                start_index += results_per_page
                
                # Rate limiting
                if nvd_api_key:
                    time.sleep(0.6)
                else:
                    time.sleep(6)
                    
            else:
                print(f"✗ Error: {response.status_code}")
                break
                
        except Exception as e:
            print(f"✗ Exception: {e}")
            break
    
    print(f"✓ Total CVEs fetched: {len(all_cves)}")
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

def update_or_add_cves(documents, embeddings):
    """Update existing CVEs or add new ones to the vector store"""
    
    print("\nLoading existing vector store...")
    
    vectorstore = Chroma(
        persist_directory="./chroma_db_all",
        embedding_function=embeddings,
        collection_name="cve_all_collection"
    )
    
    collection = vectorstore._collection
    
    print("Processing updates...")
    
    updated_count = 0
    added_count = 0
    
    for i, doc in enumerate(documents, 1):
        cve_id = doc.metadata['cve_id']
        
        try:
            # Check if CVE already exists by querying with where filter
            existing = collection.get(
                where={"cve_id": cve_id},
                include=['metadatas']  # Changed from 'ids' to 'metadatas'
            )
            
            if existing and existing['ids']:
                # CVE exists - delete old version
                collection.delete(ids=existing['ids'])
                updated_count += 1
                action = "Updated"
            else:
                # New CVE
                added_count += 1
                action = "Added"
            
            # Add the new/updated version
            vectorstore.add_documents([doc])
            
            # To indicate progress
            if i % 100 == 0:
                print(f"  Processed {i}/{len(documents)} CVEs...")
            
        except Exception as e:
            print(f"✗ Error processing {cve_id}: {e}")
            continue
    
    print(f"  Update complete!")
    print(f"  New CVEs added: {added_count}")
    print(f"  Existing CVEs updated: {updated_count}")
    print(f"  Total processed: {len(documents)}")
    
    return vectorstore

def daily_update():
    """Main function to perform daily update"""
    
    print("="*60)
    print("DAILY CVE DATABASE UPDATE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    start_time = time.time()
    
    # Get last update time
    last_update = get_last_update_time()
    
    # Current time
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000")
    
    # Fetch modified CVEs
    cves = fetch_modified_cves(last_update, current_time)
    
    if not cves:
        print("\n✓ No new or modified CVEs found. Database is up to date!")
        save_last_update_time(current_time)
        return
    
    # Convert to documents
    print(f"\nConverting {len(cves)} CVEs to documents...")
    documents = []
    for cve in cves:
        try:
            doc = cve_to_document(cve)
            documents.append(doc)
        except Exception as e:
            print(f"✗ Error converting {cve.get('id', 'unknown')}: {e}")
    
    print(f"✓ Converted {len(documents)} documents")
    
    # Initialize embeddings
    print("\nInitializing embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'mps'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Update vector store
    print("\nUpdating vector store...")
    update_or_add_cves(documents, embeddings)
    
    # Save update timestamp
    save_last_update_time(current_time)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print("\n" + "="*60)
    print("UPDATE COMPLETE!")
    print(f"Time taken: {int(elapsed//60)}m {int(elapsed%60)}s")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    try:
        daily_update()
    except Exception as e:
        print(f"\n✗ Update failed: {e}")
        import traceback
        traceback.print_exc()