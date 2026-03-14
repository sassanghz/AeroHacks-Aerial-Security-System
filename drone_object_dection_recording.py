import cv2
import numpy as np
import os
import argparse
import yaml
from bounding_box import draw_bounding_box
from djitellopy import tello
import onnx
from datetime import datetime
import time

#-----Global Parameters------
scalefactor = 1.0/255.0
size = (640, 640)
mean = (125, 125, 125)
mean = None
ddepth = None

score_threshold = 0.55 # Threshold for the confidence score.
nms_threshold = 0.45 # Threshold for non-maximum suppression.
eta = 0.5 # Parameter that trades off precision and recall.
#----------------------------

class AVAI:
    def __init__(self, model, yaml_file, record = None, output_file = None, codec = 'mp4v'):
        # self.drone = drone
        self.model = model
        self.yaml_file = yaml_file
        self.record = record
        self.output_file = output_file
        self.codec = codec
        self.net = None

    def load_classes_from_yaml(self):

        with open(self.yaml_file, mode ='r') as f:
            data_yaml = yaml.load(f,Loader = yaml.Loader)
            self.labels = data_yaml['names']

    def load_model(self):
        self.net = cv2.dnn.readNetFromONNX(self.model)

    # Load Model -> Convert to Blob -> Set Network Path -> Get Detections -> Get Score -> Apply Non Max Suppression -> Show Bounding Boxes, Labels, & Scores
    def object_detection(self, frame):
        [h, w, d] = frame.shape

        l = max((h, w))
        img = np.zeros((l, l, 3), np.uint8)
        img[0:h, 0:w] = frame

        blob = cv2.dnn.blobFromImage(frame, scalefactor=scalefactor, size=size, mean=mean, swapRB=False, crop=False, ddepth=ddepth)
        self.net.setInput(blob)
        preds = self.net.forward()

        preds = np.array([cv2.transpose(preds[0])]) # transpose operation swaps the 2nd and 3rd dimensions.
        rows = preds.shape[1] # (1,8400,5)
        
        boxes = []
        scores = []
        class_ids = []

        for i in range(rows):
            classes_scores = preds[0][i][4:]
            (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(classes_scores)
            if maxScore >= 0.55:
                box = [
                    preds[0][i][0] - (0.5 * preds[0][i][2]),
                    preds[0][i][1] - (0.5 * preds[0][i][3]),
                    preds[0][i][2],
                    preds[0][i][3]]
                
                boxes.append(box)
                scores.append(maxScore)
                class_ids.append(maxClassIndex)


        result_boxes = cv2.dnn.NMSBoxes(boxes, scores, score_threshold, nms_threshold, eta)
    
        detections = []
        center_point = []
        bbox_area = []

        x_scale = w/640
        y_scale = h/640
    
        for i in range(len(result_boxes)):
            index = result_boxes[i]
            box = boxes[index] #[x,y,w,h]
    
            detection = {
                "class_id": class_ids[index],
                "class_name": self.labels[class_ids[index]],
                "confidence": scores[index],
                "box": box,
                "x_scale": x_scale,
                "y_scale": y_scale
            }
            detections.append(detection)

            x = box[0] * x_scale
            y = box[1] * y_scale
            width = box[2] * x_scale
            height = box[3] * y_scale

            draw_bounding_box(
                frame,
                class_ids[index],
                scores[index],
                round(x),
                round(y),
                round((x + width)),
                round((y + height)))
            
            cx = x + width //2
            cy = y + height //2

            cv2.circle(frame,(int(cx),int(cy)),6,(0,0,255), 1)
            area = width * height

            center_point.append([int(cx),int(cy)])
            bbox_area.append(area)
        
        if len(bbox_area) !=0:
            i = bbox_area.index(max(bbox_area))
            center_x = center_point[i][0]
            center_y = center_point[i][1]
            bbox_area_1 = bbox_area[i]
            result = center_x,center_y,bbox_area_1
            return frame, result
        else:
            return frame, None