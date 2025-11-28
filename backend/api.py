import os
import requests
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from datetime import datetime, timedelta 


os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load .env from parent directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Verify API key is loaded
if not os.getenv('OPENAI_API_KEY'):
    print("ERROR: OPENAI_API_KEY not found in environment variables!")
    print(f"Looking for .env at: {os.path.abspath(env_path)}")
    print("Please ensure your .env file exists and contains OPENAI_API_KEY")
    sys.exit(1)

print(f"Environment loaded from: {os.path.abspath(env_path)}")
load_dotenv('.env')

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

vectorstore = None
qa_chain = None
retriever = None

def initialize_system():
    """Initialize the RAG system (called once at startup)"""
    global vectorstore, qa_chain, retriever
    
    print("="*60)
    print("Initializing CyberRAG System...")
    print("="*60)
    
    # Load embeddings
    print("Loading HuggingFace embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'mps'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Load vector store
    print("Loading vector store...")
    vectorstore = Chroma(
        persist_directory="./chroma_db_all",
        embedding_function=embeddings,
        collection_name="cve_all_collection"
    )
    
    # Get collection count
    collection = vectorstore._collection
    count = collection.count()
    print(f"Vector store loaded: {count:,} CVEs")
    
    # Initialize LLM
    print("Initializing ChatGPT...")
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    # Create retriever
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 5}  # Return top 5 relevant CVEs
    )
    
    # Creating QA chain
    template = """You are a cybersecurity expert assistant specializing in vulnerability analysis.

Answer the user's question based on the following CVE vulnerability information from the National Vulnerability Database:

Context: {context}

Question: {question}

Provide a clear, accurate, and helpful answer. If the information isn't in the context, say so. Be concise but informative.

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
    
    print("✓ CyberRAG system initialized successfully!")
    print("="*60 + "\n")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "CyberRAG API is running",
        "timestamp": str(os.popen('date').read().strip())
    }), 200

@app.route('/api/query', methods=['POST'])
def query():
    """Main query endpoint for the chatbot with conversation history support"""
    try:
        data = request.json
        user_query = data.get('query', '').strip()
        conversation_history = data.get('history', [])  # NEW: Get chat history
        
        if not user_query:
            return jsonify({
                "error": "No query provided",
                "message": "Please provide a 'query' field in the request body"
            }), 400
        
        print(f"Processing query: {user_query}")
        if conversation_history:
            print(f"With {len(conversation_history)} previous messages")
        
        # Build context from conversation history
        history_context = ""
        if conversation_history:
            # Take last 3 exchanges (6 messages) to avoid token limits
            recent_history = conversation_history[-6:]
            for msg in recent_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_context += f"{role.capitalize()}: {content}\n\n"
        
        # Get source documents
        source_docs = retriever.invoke(user_query)
        
        # Format sources
        sources = []
        context_text = ""
        for doc in source_docs:
            context_text += doc.page_content + "\n\n"
            sources.append({
                "cve_id": doc.metadata.get('cve_id'),
                "severity": doc.metadata.get('cvss_severity'),
                "score": doc.metadata.get('cvss_score'),
                "status": doc.metadata.get('vulnStatus'),
                "published": doc.metadata.get('published', '')[:10],
                "year": doc.metadata.get('year'),
                "description_preview": doc.page_content[:150] + "..."
            })
        
        # Create prompt with history
        prompt_with_history = f"""You are a cybersecurity expert assistant specializing in vulnerability analysis.

Previous conversation:
{history_context}

Current context from CVE database:
{context_text}

Current question: {user_query}

Provide a clear, accurate, and helpful answer. Consider the conversation history when answering. If referring to something from earlier in the conversation, acknowledge it naturally. If the information isn't in the context, say so.

Answer:"""
        
        # Get answer from LLM
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        answer = llm.invoke(prompt_with_history).content
        
        print(f"✓ Query processed successfully")
        
        return jsonify({
            "success": True,
            "query": user_query,
            "answer": answer,
            "sources": sources,
            "source_count": len(sources)
        }), 200
        
    except Exception as e:
        print(f"✗ Error processing query: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "An error occurred while processing your query"
        }), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get database statistics"""
    try:
        collection = vectorstore._collection
        count = collection.count()
        
        # Get last update time
        last_update = "Unknown"
        if os.path.exists('last_update.txt'):
            with open('last_update.txt', 'r') as f:
                last_update = f.read().strip()
        
        return jsonify({
            "success": True,
            "total_cves": count,
            "database": "chroma_db_all",
            "embedding_model": "sentence-transformers/all-mpnet-base-v2",
            "last_update": last_update
        }), 200
        
    except Exception as e:
        print(f"✗ Error getting stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Search for specific CVEs by ID or keyword"""
    try:
        data = request.json
        search_query = data.get('search', '').strip()
        limit = data.get('limit', 10)
        
        if not search_query:
            return jsonify({
                "error": "No search query provided"
            }), 400
        
        # Use retriever to find relevant CVEs
        docs = retriever.invoke(search_query)
        
        results = []
        for doc in docs[:limit]:
            results.append({
                "cve_id": doc.metadata.get('cve_id'),
                "severity": doc.metadata.get('cvss_severity'),
                "score": doc.metadata.get('cvss_score'),
                "status": doc.metadata.get('vulnStatus'),
                "published": doc.metadata.get('published', '')[:10],
                "description": doc.page_content
            })
        
        return jsonify({
            "success": True,
            "query": search_query,
            "results": results,
            "count": len(results)
        }), 200
        
    except Exception as e:
        print(f"✗ Error searching: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/cve/<cve_id>', methods=['GET'])
def get_cve(cve_id):
    """Get details for a specific CVE by ID"""
    try:
        collection = vectorstore._collection
        
        # Search for CVE by ID
        results = collection.get(
            where={"cve_id": cve_id.upper()},
            include=['metadatas', 'documents']
        )
        
        if not results or not results['ids']:
            return jsonify({
                "success": False,
                "error": "CVE not found",
                "cve_id": cve_id
            }), 404
        
        # Return first match
        metadata = results['metadatas'][0]
        document = results['documents'][0]
        
        return jsonify({
            "success": True,
            "cve_id": metadata.get('cve_id'),
            "severity": metadata.get('cvss_severity'),
            "score": metadata.get('cvss_score'),
            "status": metadata.get('vulnStatus'),
            "published": metadata.get('published', '')[:10],
            "lastModified": metadata.get('lastModified', '')[:10],
            "year": metadata.get('year'),
            "description": document
        }), 200
        
    except Exception as e:
        print(f"✗ Error getting CVE: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/news', methods=['POST'])
def get_news():
    """Get CVEs based on filters (date range, severity, etc.)"""
    try:
        data = request.json
        filter_type = data.get('filter', 'today')  # today, week, month, custom
        severity = data.get('severity', None)  # CRITICAL, HIGH, MEDIUM, LOW
        limit = data.get('limit', 20)
        start_date = data.get('startDate', None)
        end_date = data.get('endDate', None)
        
        from datetime import datetime, timedelta
        
        # Calculate date ranges based on filter type
        now = datetime.now()
        
        if filter_type == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif filter_type == 'week':
            start = now - timedelta(days=7)
            end = now
        elif filter_type == 'month':
            start = now - timedelta(days=30)
            end = now
        elif filter_type == 'custom' and start_date and end_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            start = now - timedelta(days=7)  # Default to week
            end = now
        
        # Format dates for NVD API
        start_str = start.strftime("%Y-%m-%dT%H:%M:%S.000")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S.000")
        
        print(f"Fetching CVEs from {start_str} to {end_str}")
        
        # Fetch from NVD API
        nvd_api_key = os.getenv('NVD_API_KEY')
        headers = {}
        if nvd_api_key:
            headers['apiKey'] = nvd_api_key
        
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {
            "lastModStartDate": start_str,
            "lastModEndDate": end_str,
            "resultsPerPage": min(limit, 2000)
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"NVD API error: {response.status_code}"
            }), 500
        
        nvd_data = response.json()
        vulnerabilities = nvd_data.get('vulnerabilities', [])
        
        # Process and filter CVEs
        cves = []
        for vuln in vulnerabilities:
            cve = vuln['cve']
            
            # Extract CVSS info
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
            
            # Filter by severity if specified
            if severity and cvss_severity != severity:
                continue
            
            # Extract description
            description = ""
            for desc in cve.get('descriptions', []):
                if desc['lang'] == 'en':
                    description = desc['value']
                    break
            
            cve_obj = {
                "cve_id": cve['id'],
                "severity": cvss_severity,
                "score": str(cvss_score),
                "status": cve.get('vulnStatus', 'Unknown'),
                "published": cve['published'][:10],
                "lastModified": cve['lastModified'][:10],
                "description": description,
                "year": cve['published'][:4]
            }
            
            cves.append(cve_obj)
        
        # Sort by lastModified (newest first)
        cves.sort(key=lambda x: x['lastModified'], reverse=True)
        
        return jsonify({
            "success": True,
            "cves": cves[:limit],
            "total": len(cves),
            "filter": filter_type,
            "date_range": {
                "start": start_str,
                "end": end_str
            }
        }), 200
        
    except Exception as e:
        print(f"✗ Error fetching news: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Initialize system before starting server
    initialize_system()
    
    # Run Flask app
    print("="*60)
    print("🚀 Starting CyberRAG API Server")
    print("="*60)
    print("\nAPI Endpoints:")
    print("  GET  http://localhost:5000/api/health")
    print("  POST http://localhost:5000/api/query")
    print("  GET  http://localhost:5000/api/stats")
    print("  POST http://localhost:5000/api/search")
    print("  GET  http://localhost:5000/api/cve/<cve_id>")
    print("\n" + "="*60)
    print("Server running on http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)