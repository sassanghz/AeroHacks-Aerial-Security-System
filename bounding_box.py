import cv2
import numpy as np
import yaml

def draw_bounding_box(frame, class_id, confidence, x, y, x_plus_w, y_plus_h):

    label = f"Intruder Detected({confidence:.0%})"
    cv2.rectangle(frame, (x, y), (x_plus_w, y_plus_h), (255,255,255), 2)
    cv2.putText(frame, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
    cv2.putText(frame,'Recording...', (2, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    

    