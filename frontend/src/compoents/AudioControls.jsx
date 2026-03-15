import { useRef } from "react";

function AudioControls() {
  const audioRef = useRef(null);

  const playSound = (src) => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.pause();
    audio.currentTime = 0;
    audio.src = src;

    audio.play().catch((error) => {
      console.error("Audio playback failed:", error);
    });
  };

  return (
    <div className="audio-controls">
      <button type="button" onClick={() => playSound("public/audio/intruder.wav")}>
        Intruder
      </button>

      <button type="button" onClick={() => playSound("public/audio/restricted.wav")}>
        Restricted
      </button>

      <button type="button" onClick={() => playSound("public/audio/surveillance.wav")}>
        Surveillance
      </button>

      <audio ref={audioRef} hidden />
    </div>
  );
}

export default AudioControls;
