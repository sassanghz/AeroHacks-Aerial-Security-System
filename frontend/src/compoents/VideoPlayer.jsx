import { useEffect, useState } from "react";

function VideoPlayer() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const stream = new EventSource("http://localhost:5001/analysis_stream");

    stream.addEventListener("analysis", (event) => {
      const data = JSON.parse(event.data);

      // Backend has started analyzing at least one frame
      if (data.updated_at && data.updated_at > 0) {
        setIsReady(true);
      }
    });

    stream.onerror = () => {
      console.error("Failed to connect to analysis stream");
    };

    return () => {
      stream.close();
    };
  }, []);

  return (
    <div className="video-wrap">
      {isReady ? (
        <img
          className="video-element"
          src="http://localhost:5001/video_feed"
          alt="Processed security feed"
        />
      ) : (
        <div>Waiting for analysis to start...</div>
      )}
    </div>
  );
}

export default VideoPlayer;
