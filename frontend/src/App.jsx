import { useEffect, useState } from "react";

function App() {
    const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState([]);
  const [grounded, setGrounded] = useState(null);
  const [file, setFile] = useState(null);
  const [files, setFiles] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");

  async function refreshFiles() {
    try {
      const response = await fetch("http://127.0.0.1:8000/files");
      const data = await response.json();
      setFiles(data.files || []);
    } catch (err) {
      console.error("Failed to load files:", err);
    }
  }

  useEffect(() => {
    refreshFiles();
  }, []);

  async function uploadFile() {
    if (!file) return;
    
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://127.0.0.1:8000/upload", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      alert("File uploaded successfully!");
      setFile(null);
      refreshFiles();
    } else {
      alert("Upload failed. Please try again.");
    }
  }

  async function askQuestion() {
    const response = await fetch(
      "http://127.0.0.1:8000/ask",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          question: question
        })
      }
    );

    const data = await response.json();
    console.log("Data from backend:", data);
    setAnswer(data.answer);
    setSources(data.sources);
  }

  return (
    <div>
      <h1>Academic RAG</h1>

      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={uploadFile}>Upload File</button>

      <br /><br />

      <h3>Uploaded Files</h3>

      {files.length === 0 ? (
        <p>No files uploaded yet.</p>
      ) : (
        <ul>
          {files.map((f) => (
            <li key={f.name}>
              <a
                href={`http://127.0.0.1:8000/files/${encodeURIComponent(f.name)}`}
                target="_blank"
                rel="noreferrer"
              >
                {f.name}
              </a>{" "}
              ({f.size_mb} MB)
            </li>
          ))}
        </ul>
      )}

      <br /><br />

      <input
        value={question}
        onChange={(e) =>
          setQuestion(e.target.value)
        }
        placeholder="Ask something..."
      />

      <button onClick={askQuestion}>
        Ask
      </button>

      <h3>Answer</h3>
            
      {/* This checks if the answer is a list (Array) and extracts the text from the first item */}
      <p>{Array.isArray(answer) ? answer[0].text : (typeof answer === 'object' ? answer.text : answer)}</p>

      <h3>Retrieved Sources</h3>

      {sources && sources.map((source, index) => (
        <p key={index}>
          {source.text ? source.text : "No text available"}
        </p>
      ))}
    </div>
  );
}

export default App;