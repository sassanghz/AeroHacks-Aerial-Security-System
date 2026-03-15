import cv2
import time
import threading
from faceAnalyze import analyzeImage 
from helper import latest_image

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

imageFolder = "images"
iTime = 0
analysis_thread = None

print ("Press 'q' to quit the camera feed.")

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

capture_active = False
last_face_seen_time = None
no_face_timeout = 5

def run_analysis(image_path: str) -> None:
    try:
        result = analyzeImage(image_path)
        print("Analysis done:", result)
    except Exception as e:
        print("Analysis error:", e)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    frame = cv2.flip(frame, 1)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cv2.imshow('Camera Feed', frame)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=7,
        minSize=(80, 80)
    )

    current_time = time.time()

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if len(faces) > 0:
        last_face_seen_time = current_time
        if not capture_active:
            capture_active = True
            iTime = 0  # allow immediate capture when face first appears
            print("Face detected. Starting photo capture.")
    else:
        if capture_active and last_face_seen_time is not None:
            if current_time - last_face_seen_time >= no_face_timeout:
                capture_active = False
                print("No face detected for 5 seconds. Stopping photo capture.")

    status = "CAPTURING" if capture_active else "WAITING FOR FACE"
    cv2.putText(
        frame,
        status,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0) if capture_active else (0, 0, 255),
        2
    )

    cv2.imshow("Camera Feed", frame)

    should_capture = (
        capture_active
        and current_time - iTime >= 5
        and (analysis_thread is None or not analysis_thread.is_alive())
    )

    if should_capture:
        file_name = f"{imageFolder}/{int(current_time)}.jpg"
        cv2.imwrite(file_name, frame)
        print(f"Saved: {file_name}")

        analysis_thread = threading.Thread(
            target=run_analysis,
            args=(file_name,),
            daemon=True,
        )
        analysis_thread.start()

        iTime = current_time

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()