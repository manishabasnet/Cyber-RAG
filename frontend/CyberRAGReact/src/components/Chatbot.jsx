import { useState } from "react";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! How can I assist you today?" }
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);

    const botMessage = { sender: "bot", text: "Message received!" };

    setTimeout(() => {
      setMessages((prev) => [...prev, botMessage]);
    }, 500);

    setInput("");
  };

  return (
    <div style={styles.container}>
      <div style={styles.chatBox}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              ...styles.message,
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              backgroundColor:
                msg.sender === "user" ? "#F9B487" : "#427A76",
              color: msg.sender === "user" ? "#174143" : "white"
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div style={styles.inputArea}>
        <input
          style={styles.input}
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button style={styles.button} onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    width: "450px",
    height: "600px",
    borderRadius: "12px",
    border: "2px solid #427A76",
    backgroundColor: "white",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    boxShadow: "0px 4px 14px rgba(0,0,0,0.15)"
  },

  chatBox: {
    flex: 1,
    padding: "16px", 
    display: "flex",
    flexDirection: "column",
    gap: "14px",
    overflowY: "auto",
    backgroundColor: "#F5E5E1"
  },

  message: {
    maxWidth: "85%",      
    padding: "14px 18px",  
    borderRadius: "14px",
    fontSize: "18px",     
    lineHeight: "1.4"
  },

  inputArea: {
    display: "flex",
    padding: "14px",           
    backgroundColor: "#F5E5E1",
    borderTop: "2px solid #427A76",
    gap: "10px"
  },

  input: {
    flex: 1,
    padding: "12px",        
    borderRadius: "8px",
    border: "1px solid #ccc",
    outline: "none",
    fontSize: "18px"          
  },

  button: {
    padding: "12px 20px",      
    borderRadius: "8px",
    border: "none",
    backgroundColor: "#174143",
    color: "white",
    cursor: "pointer",
    fontWeight: "bold",
    fontSize: "16px"
  }
};
