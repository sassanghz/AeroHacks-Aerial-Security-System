import { useEffect, useState } from "react";
import "./App.css";
import VideoPlayer from "./compoents/VideoPlayer";
import AnalysisDetails from "./compoents/AnalysisDetails";
import ChatInput from "./compoents/ChatInput";
import AudioControls from "./compoents/AudioControls";

const initialAnalysis = {
  age: "",
  skin_tone: "",
  facial_features: [],
  clothing: [],
  injuries_or_condition: [],
  uncertainty: [],
};

function App() {
  const [analysisData, setAnalysisData] = useState(initialAnalysis);

  useEffect(() => {
    fetch("http://localhost:5001/latest_analysis")
      .then((res) => res.json())
      .then((data) => setAnalysisData(data))
      .catch((err) => console.error("Initial analysis fetch failed:", err));

    const source = new EventSource("http://localhost:5001/analysis_stream");

    source.addEventListener("analysis", (event) => {
      try {
        const data = JSON.parse(event.data);
        setAnalysisData(data);
      } catch (err) {
        console.error("Failed to parse SSE data:", err);
      }
    });

    source.onerror = (err) => {
      console.error("SSE error:", err);
    };

    return () => {
      source.close();
    };
  }, []);

  return (
    <main className="app-shell">
      <section className="panel video-panel">
        <VideoPlayer />
      </section>

      <section className="panel info-panel">
        <AnalysisDetails data={analysisData} />
      </section>

      <section className="panel input-panel">
        <ChatInput />
      </section>

      <section className="panel audio-panel">
        <AudioControls />
      </section>
    </main>
  );
}

export default App;