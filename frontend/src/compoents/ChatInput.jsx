import { useRef, useState } from "react";

const BACKEND_URL = "http://localhost:5001";

function ChatInput() {
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const audioRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending) return;

    setError("");
    setIsSending(true);
    setMessage("");

    try {
      const response = await fetch(`${BACKEND_URL}/speak`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: trimmedMessage }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate audio");
      }

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = `${data.audio_url}?t=${Date.now()}`;
        audioRef.current.load();
        await audioRef.current.play();
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div style={{ width: "100%" }}>
      <form
        className="chat-input-wrap"
        onSubmit={handleSubmit}
        style={{ width: "100%", display: "flex" }}
      >
        <input
          className="chat-input"
          type="text"
          placeholder="Enter a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={isSending}
          style={{ flex: 1 }}
        />
        <button className="send-button" type="submit" disabled={isSending}>
          {isSending ? "Generating..." : "Send"}
        </button>
      </form>

      {error && <p>{error}</p>}

      <audio ref={audioRef} />
    </div>
  );
}

export default ChatInput;
