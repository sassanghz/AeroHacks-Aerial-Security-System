import cv2
import numpy as np
# from bounding_box import draw_bounding_box
from drone_object_dection_recording import AVAI
from flight_logic import PID
# from djitellopy import tello
from datetime import datetime

#-----Global Parameters------

#error calculations 
width,height = 360,240

# y constansts
Kpy = 0.2
Kiy = 0.0
Kdy = 0.1

# yaw constansts
Kpyaw = 0.2
Kiyaw = 0.0
Kdyaw = 0.1
#----------------------------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

cap = cv2.VideoCapture(0)

# drone = tello.Tello()
# drone.connect()
# drone.streamon()
# drone.takeoff()

args = AVAI(model= "C:/Users/15149/Desktop/blueprint/best.onnx", 
            yaml_file= "C:/Users/15149/Desktop/blueprint/data.yaml",
            record=False,
            output_file = f"Intruder_Recorded_Video_{timestamp}.mp4",
            codec='mp4v')

args2 = PID(Kpy,Kiy,Kdy,Kpyaw,Kiyaw,Kdyaw)

args.load_classes_from_yaml()
args.load_model()

# args.start_recording()

while True:
    ret, frame = cap.read()
    # frame = drone.get_frame_read().frame
    # args.record_frame(frame)
    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    frame,result = args.object_detection(frame)
    # cap,result = args.object_detection(frame)
    # print(result)
    if result is not None:
        cx,cy,a = result
        args2.computation(cx,cy,width,height,a)

    # cv2.putText(frame, "Battery:" + str(drone.get_battery()) + "%", (2,60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    cv2.imshow('Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        # drone.land() #Emergency landing applies too
        # args.stop_recording()
        break

cap.release()
cv2.destroyAllWindows()
# drone.reboot()
