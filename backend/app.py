import atexit
import json
import os
import queue
import re
import threading
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2
from flask import Flask, Response, jsonify, request, send_from_directory

from faceAnalyze import analyzeImage
from tts import text_to_speech_file

app = Flask(__name__)

# ----------------------------
# Config
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
ANALYSIS_JSON_PATH = BASE_DIR / "analysis.json"
AUDIO_DIR = BASE_DIR / "audio"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Webcam by default:
#   VIDEO_SOURCE=0                      -> default webcam
#   VIDEO_SOURCE=1                      -> second webcam
#   VIDEO_SOURCE=videos/source.mov      -> local file
#   VIDEO_SOURCE=rtsp://...             -> RTSP camera
VIDEO_SOURCE_RAW = os.getenv("VIDEO_SOURCE", "0")

ANALYSIS_INTERVAL_SEC = float(os.getenv("ANALYSIS_INTERVAL_SEC", "5"))
TARGET_FPS_SLEEP_SEC = float(os.getenv("TARGET_FPS_SLEEP_SEC", "0.03"))

workers_started = False
workers_lock = threading.Lock()

# ----------------------------
# Helpers
# ----------------------------
def parse_video_source(value: str):
    value = str(value).strip()

    # Webcam index, e.g. "0", "1"
    if value.isdigit():
        return int(value)

    # Relative local path
    candidate = Path(value)
    if not candidate.is_absolute() and not str(value).startswith(("rtsp://", "http://", "https://")):
        candidate = BASE_DIR / candidate
        return str(candidate)

    return value


VIDEO_SOURCE = parse_video_source(VIDEO_SOURCE_RAW)

# ----------------------------
# Shared state
# ----------------------------
cap = None
cap_lock = threading.Lock()

frame_lock = threading.Lock()
analysis_lock = threading.Lock()

latest_frame_jpeg: bytes | None = None
analysis_version = 0

latest_analysis = {
    "age": "Not clearly visible",
    "skin_tone": "Not clearly visible",
    "facial_features": ["Not clearly visible"],
    "clothing": ["Not clearly visible"],
    "injuries_or_condition": ["None visible"],
    "uncertainty": ["initializing"],
    "frame_id": 0,
    "updated_at": 0,
}

analysis_queue: queue.Queue[tuple[int, float, Any]] = queue.Queue(maxsize=1)
stop_event = threading.Event()

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

if face_cascade.empty():
    raise RuntimeError("Failed to load OpenCV Haar cascade for face detection.")

# ----------------------------
# Capture lifecycle
# ----------------------------
def ensure_capture_open() -> None:
    global cap

    with cap_lock:
        if cap is not None and cap.isOpened():
            return

        cap = cv2.VideoCapture(VIDEO_SOURCE)

        # Optional webcam tuning
        if isinstance(VIDEO_SOURCE, int):
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            raise RuntimeError(f"Could not open video source: {VIDEO_SOURCE!r}")


def release_capture() -> None:
    global cap
    with cap_lock:
        if cap is not None:
            cap.release()
            cap = None


# ----------------------------
# Normalization helpers
# ----------------------------
def normalize_string(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def normalize_list(value: Any, fallback: str) -> list[str]:
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned or [fallback]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return [fallback]


def coerce_analysis_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result

    if result is None:
        return {}

    if not isinstance(result, str):
        result = str(result)

    text = result.strip()

    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    return {}


def normalize_analysis_result(result: Any, frame_id: int, updated_at: float) -> dict[str, Any]:
    if not isinstance(result, dict):
        result = {}

    normalized = {
        "age": normalize_string(result.get("age"), "Not clearly visible"),
        "skin_tone": normalize_string(result.get("skin_tone"), "Not clearly visible"),
        "facial_features": normalize_list(result.get("facial_features"), "Not clearly visible"),
        "clothing": normalize_list(result.get("clothing"), "Not clearly visible"),
        "injuries_or_condition": normalize_list(
            result.get("injuries_or_condition"), "None visible"
        ),
        "uncertainty": normalize_list(result.get("uncertainty"), "none"),
        "frame_id": frame_id,
        "updated_at": updated_at,
    }
    return normalized


def write_analysis_json(data: dict[str, Any]) -> None:
    ANALYSIS_JSON_PATH.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def set_latest_analysis(data: dict[str, Any]) -> None:
    global latest_analysis, analysis_version
    with analysis_lock:
        latest_analysis = data
        analysis_version += 1


# ----------------------------
# Background workers
# ----------------------------
def capture_worker() -> None:
    global latest_frame_jpeg

    ensure_capture_open()

    frame_id = 0
    last_analysis_enqueue_time = 0.0
    consecutive_failures = 0

    while not stop_event.is_set():
        with cap_lock:
            ret, frame = cap.read() if cap is not None else (False, None)

        # For webcam: retry instead of stopping immediately
        if not ret or frame is None:
            consecutive_failures += 1
            print(f"Frame read failed (#{consecutive_failures}). Retrying...", flush=True)

            if consecutive_failures >= 20:
                print("Too many frame failures. Reopening capture...", flush=True)
                release_capture()
                time.sleep(0.5)
                try:
                    ensure_capture_open()
                except Exception as exc:
                    print(f"Reopen failed: {exc}", flush=True)
                    time.sleep(1.0)

            time.sleep(0.1)
            continue

        consecutive_failures = 0
        frame_id += 1

        # Mirror webcam preview for natural UX
        if isinstance(VIDEO_SOURCE, int):
            frame = cv2.flip(frame, 1)

        analysis_frame = frame.copy()
        display_frame = frame.copy()

        gray = cv2.cvtColor(display_frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=7,
            minSize=(80, 80),
        )

        face_detected = len(faces) > 0

        for (x, y, w, h) in faces:
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 170), 2)

        source_label = "WEBCAM" if isinstance(VIDEO_SOURCE, int) else "LIVE"
        face_status = "FACE DETECTED" if face_detected else "NO FACE"
        status_text = f"{source_label} | faces: {len(faces)} | {face_status}"

        cv2.putText(
            display_frame,
            status_text,
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 170),
            2,
        )

        ok, buffer = cv2.imencode(".jpg", display_frame)
        if ok:
            with frame_lock:
                latest_frame_jpeg = buffer.tobytes()

        now = time.time()

        # Only run analysis if at least one face is detected,
        # and only once every ANALYSIS_INTERVAL_SEC seconds
        if (
            face_detected
            and (now - last_analysis_enqueue_time) >= ANALYSIS_INTERVAL_SEC
            and analysis_queue.empty()
        ):
            try:
                analysis_queue.put_nowait((frame_id, now, analysis_frame))
                last_analysis_enqueue_time = now
                print(f"[capture] face detected, queued frame {frame_id} for analysis", flush=True)
            except queue.Full:
                pass

        time.sleep(TARGET_FPS_SLEEP_SEC)

    release_capture()



def analysis_worker() -> None:
    while not stop_event.is_set():
        try:
            frame_id, timestamp, frame = analysis_queue.get(timeout=0.25)
        except queue.Empty:
            continue

        snapshot_path = IMAGE_DIR / f"frame_{frame_id}_{int(timestamp * 1000)}.jpg"
        cv2.imwrite(str(snapshot_path), frame)
        print(f"[analysis] analyzing {snapshot_path}", flush=True)

        try:
            raw_result = analyzeImage(str(snapshot_path))
            parsed_result = coerce_analysis_result(raw_result)
            normalized = normalize_analysis_result(parsed_result, frame_id, timestamp)

            print("\n--- Raw analysis result ---")
            print(raw_result)
            print("---------------------------\n", flush=True)

        except Exception as exc:
            normalized = normalize_analysis_result(
                {
                    "uncertainty": [f"analysis error: {exc}"],
                },
                frame_id,
                timestamp,
            )

        print("\n--- Analysis updated ---")
        print(json.dumps(normalized, indent=2))
        print("------------------------\n", flush=True)

        set_latest_analysis(normalized)
        write_analysis_json(normalized)
        analysis_queue.task_done()


# ----------------------------
# Streaming generators
# ----------------------------
def mjpeg_generator():
    while not stop_event.is_set():
        with frame_lock:
            frame = latest_frame_jpeg

        if frame is None:
            time.sleep(0.05)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame +
            b"\r\n"
        )

        time.sleep(0.03)


def sse_generator():
    last_seen_version = -1
    last_ping = 0.0

    while not stop_event.is_set():
        with analysis_lock:
            current_version = analysis_version
            payload = dict(latest_analysis)

        now = time.time()

        if current_version != last_seen_version:
            last_seen_version = current_version
            yield f"event: analysis\ndata: {json.dumps(payload)}\n\n"
            last_ping = now
        elif (now - last_ping) >= 15:
            yield ": ping\n\n"
            last_ping = now

        time.sleep(0.25)


# ----------------------------
# Routes
# ----------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/")
def index():
    return jsonify(
        {
            "status": "ok",
            "video_source": str(VIDEO_SOURCE),
            "endpoints": {
                "video_feed": "/video_feed",
                "latest_analysis": "/latest_analysis",
                "analysis_stream": "/analysis_stream",
                "speak": "/speak",
            },
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/latest_analysis")
def get_latest_analysis():
    start_background_threads()
    with analysis_lock:
        return jsonify(latest_analysis)


@app.route("/analysis_stream")
def analysis_stream():
    start_background_threads()
    return Response(
        sse_generator(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/video_feed")
def video_feed():
    start_background_threads()
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename, mimetype="audio/wav")


@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()

    if not text:
        return jsonify({"error": "Text is required"}), 400

    filename = f"tts_{int(time.time() * 1000)}_{uuid4().hex[:8]}.wav"
    output_path = AUDIO_DIR / filename

    try:
        text_to_speech_file(
            text=text,
            output_path=str(output_path),
        )
    except Exception as exc:
        return jsonify({"error": f"Failed to generate audio: {exc}"}), 500

    audio_url = f"{request.host_url.rstrip('/')}/audio/{filename}"

    return jsonify(
        {
            "success": True,
            "audio_url": audio_url,
            "file_name": filename,
        }
    )


# ----------------------------
# Startup / shutdown
# ----------------------------
def start_background_threads() -> None:
    global workers_started

    with workers_lock:
        if workers_started:
            return

        ensure_capture_open()

        threading.Thread(
            target=capture_worker,
            daemon=True,
            name="capture-worker",
        ).start()

        threading.Thread(
            target=analysis_worker,
            daemon=True,
            name="analysis-worker",
        ).start()

        workers_started = True


@atexit.register
def cleanup():
    stop_event.set()
    release_capture()


if __name__ == "__main__":
    start_background_threads()
    app.run(host="0.0.0.0", port=5001, debug=True, threaded=True, use_reloader=False)
