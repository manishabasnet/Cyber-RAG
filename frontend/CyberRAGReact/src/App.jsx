import Chatbot from "./components/Chatbot";
import VulnerabilityCard from "./components/VulnerabilityCard";

function App() {
  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Cyber RAG</h1>

      <div style={styles.chatbotWrapper}>
        <VulnerabilityCard
          title="Sample Vulnerability"
          description="This is a brief description of a sample vulnerability."
        />
        <Chatbot />
      </div>
    </div>
  );
}

const styles = {
  container: {
    height: "100vh",
    width: "100%",
    backgroundColor: "#F5E5E1", 
    position: "relative"
  },
  title: {
    textAlign: "center",
    marginTop: "20px",
    color: "#174143", 
    fontSize: "36px",
    fontWeight: "bold"
  },
  chatbotWrapper: {
    position: "fixed",
    bottom: "20px",
    right: "20px"
  }
};

export default App;
