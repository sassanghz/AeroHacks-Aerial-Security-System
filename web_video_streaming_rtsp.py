import cv2
from flask import Flask, render_template, Response
from djitellopy import tello

drone = tello.Tello()
drone.connect()
drone.send_command_with_return("port 8890 11111")
drone.streamon()

app=Flask(__name__)
web_frame = drone.get_frame_read().web_frame

def stream_live_video_frame():
    while True:
        web_frame = drone.get_frame_read().web_frame
        
        ret, buffer = cv2.imencode('.jpg', web_frame)
        web_frame = buffer.tobytes()

        yield(b'--web_frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + web_frame + b'\r\n')

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(stream_live_video_frame(),mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__=="__main__":
    app.run(debug=True)
