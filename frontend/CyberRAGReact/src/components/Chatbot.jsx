import React, { useState, useRef, useEffect } from 'react';

function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m CyberRAG, your cybersecurity assistant. Ask me about CVE vulnerabilities, security threats, or specific CVE IDs.',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!input.trim() || loading) return;
  
    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };
  
    // Add user message
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
  
    try {
      // Check if the query is asking about a specific CVE ID
      const cveIdMatch = userMessage.content.match(/CVE-\d{4}-\d{4,}/i);
      
      if (cveIdMatch) {
        // Direct CVE lookup
        const cveId = cveIdMatch[0].toUpperCase();
        const response = await fetch(`http://localhost:5001/api/cve/${cveId}`);
        const data = await response.json();
  
        if (data.success) {
          // Format the CVE details into a readable response
          const formattedResponse = `
**${data.cve_id}**

**Severity:** ${data.severity} (Score: ${data.score})
**Status:** ${data.status}
**Published:** ${data.published}
**Last Modified:** ${data.lastModified}

**Description:**
${data.description}
          `.trim();
  
          const assistantMessage = {
            role: 'assistant',
            content: formattedResponse,
            sources: [{
              cve_id: data.cve_id,
              severity: data.severity,
              score: data.score,
              published: data.published,
              status: data.status
            }],
            timestamp: new Date()
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          // CVE not found
          const errorMessage = {
            role: 'assistant',
            content: `I couldn't find ${cveId} in the database. This CVE might not exist, or it hasn't been added to our database yet. Try asking a general question about vulnerabilities instead.`,
            timestamp: new Date(),
            isError: true
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } else {
        // Regular semantic search query WITH HISTORY
        
        // Prepare conversation history (exclude timestamps and sources for API)
        const history = messages.map(msg => ({
          role: msg.role,
          content: msg.content
        }));

        const response = await fetch('http://localhost:5001/api/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            query: userMessage.content,
            history: history  // Send conversation history
          })
        });
  
        const data = await response.json();
  
        if (data.success) {
          const assistantMessage = {
            role: 'assistant',
            content: data.answer,
            sources: data.sources,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else {
          throw new Error(data.error || 'Failed to get response');
        }
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}. Please make sure the API server is running.`,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const exampleQuestions = [
    "What are the most critical vulnerabilities in 2024?",
    "Tell me about SQL injection vulnerabilities",
    "What CVEs affect Windows Server?",
    "Show me recent Apache vulnerabilities"
  ];

  const askExample = (question) => {
    setInput(question);
  };

  return (
    <div style={{
      height: 'calc(100vh - 64px)',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#f8fafc'
    }}>
      {/* Chat Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '2rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div style={{
              maxWidth: '70%',
              padding: '1rem',
              borderRadius: '0.75rem',
              backgroundColor: message.role === 'user' 
                ? '#3b82f6' 
                : message.isError 
                  ? '#fee2e2' 
                  : '#ffffff',
              color: message.role === 'user' ? '#ffffff' : '#1e293b',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {message.content.split('**').map((part, idx) => 
                  idx % 2 === 0 ? part : <strong key={idx}>{part}</strong>
                )}
              </div>
              
              {/* Show sources if available */}
              {message.sources && message.sources.length > 0 && (
                <div style={{
                  marginTop: '1rem',
                  paddingTop: '1rem',
                  borderTop: '1px solid #e2e8f0'
                }}>
                  <div style={{ 
                    fontSize: '0.875rem', 
                    fontWeight: '600',
                    marginBottom: '0.5rem',
                    color: '#64748b'
                  }}>
                    📚 Sources ({message.sources.length})
                  </div>
                  {message.sources.map((source, idx) => (
                    <div
                      key={idx}
                      style={{
                        fontSize: '0.875rem',
                        padding: '0.5rem',
                        backgroundColor: '#f1f5f9',
                        borderRadius: '0.375rem',
                        marginBottom: '0.5rem'
                      }}
                    >
                      <strong>{source.cve_id}</strong> - 
                      {source.severity} ({source.score}) - 
                      Published: {source.published}
                    </div>
                  ))}
                </div>
              )}
              
              <div style={{
                fontSize: '0.75rem',
                color: message.role === 'user' ? '#bfdbfe' : '#94a3b8',
                marginTop: '0.5rem'
              }}>
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{
              padding: '1rem',
              backgroundColor: '#ffffff',
              borderRadius: '0.75rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <div className="dot-flashing"></div>
                Thinking...
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Example Questions */}
      {messages.length === 1 && (
        <div style={{
          padding: '0 2rem 1rem 2rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.5rem'
        }}>
          <div style={{ 
            width: '100%', 
            fontSize: '0.875rem', 
            color: '#64748b',
            marginBottom: '0.5rem'
          }}>
            💡 Try asking:
          </div>
          {exampleQuestions.map((question, idx) => (
            <button
              key={idx}
              onClick={() => askExample(question)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                fontSize: '0.875rem',
                color: '#475569',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#f1f5f9';
                e.target.style.borderColor = '#cbd5e1';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = '#ffffff';
                e.target.style.borderColor = '#e2e8f0';
              }}
            >
              {question}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div style={{
        padding: '1rem 2rem 2rem 2rem',
        backgroundColor: '#ffffff',
        borderTop: '1px solid #e2e8f0'
      }}>
        <form onSubmit={sendMessage} style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about CVE vulnerabilities..."
            disabled={loading}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              border: '2px solid #e2e8f0',
              borderRadius: '0.5rem',
              fontSize: '1rem',
              outline: 'none',
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
            onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              padding: '0.75rem 2rem',
              backgroundColor: loading || !input.trim() ? '#cbd5e1' : '#3b82f6',
              color: '#ffffff',
              border: 'none',
              borderRadius: '0.5rem',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => {
              if (!loading && input.trim()) {
                e.target.style.backgroundColor = '#2563eb';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading && input.trim()) {
                e.target.style.backgroundColor = '#3b82f6';
              }
            }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default Chatbot;