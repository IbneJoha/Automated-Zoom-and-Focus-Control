import os
import time

import numpy as np
import cv2
from ultralytics import YOLO

YOLO_WEIGHT_PATH = "/home/wicomai/occ/model/best_9t.pt"

"""
Execute AI model for object detection
Find and extract the RoI of OOK and OFDM LED
Put each detected RoI to each queue (OOK and OFDM)
"""
def obj_detector(frame_queue, ook_queue, vis_queue):
    """load the object detection model"""
    # model = YOLO(weight_path, verbose=False) #load the model, TODO: update model
    
    """for measuring fps"""
    fps_timer_start = time.time()
    frame_counter = 0
    start = True
    MODEL = YOLO(YOLO_WEIGHT_PATH, task="detect")
    
    """continuously grab fresh image from queue"""
    while True:
        """get frame from original sampled image queue"""
        frame = frame_queue.get()
        print(frame.shape)
        W, H, Ch = frame.shape
        
        if start:
            frame_det = cv2.resize(frame, (frame.shape[1]//2, frame.shape[0]//2))
            frame_det = cv2.cvtColor(frame_det, cv2.COLOR_GRAY2BGR)
            results = MODEL.predict(frame_det, verbose=False)
            results = results[0].boxes.cpu().numpy()
            ook_bboxes = results.xyxyn[np.where(results.cls == 1)] # only first bbox
            print(f"ook_bboxes {ook_bboxes}")
            # roi = [
            #     int(ook_bboxes[0] * frame.shape[1]), 
            #     int(ook_bboxes[1] * frame.shape[0]), 
            #     int(ook_bboxes[2] * frame.shape[1]), 
            #     int(ook_bboxes[3] * frame.shape[0]), 
            # ]
            # ook_frames = {id:frame[roi[1]:roi[3], roi[0]:roi[2]].squeeze(axis=2) for id, roi in enumerate(ook_frames[:1])} #row,col,

            start = True
        
        ook_frames = []
        for boxes in ook_bboxes:
            cv2.rectangle(frame, (int(boxes[0]*H), int(boxes[1]*W)), (int(boxes[2]*H),int(boxes[3]*W)), (255,0,0), 2)
            ook_frames.append(frame[int(boxes[1]*W):int(boxes[3]*W), int(boxes[0]*H):int(boxes[2]*H)])
            
        print(f"OOK frames {len(ook_frames)} ")
        """extract the OOK RoI manually"""
        # ook_frame = frame[roi[1]:roi[3],roi[0]:roi[2]] #row,col, 
        
        """put the object RoI and frame to its queue"""
        ook_queue.put(ook_frames) #put the OFDM RoI to the queue
        vis_queue.put(frame) #put the frame with RoI bbox for visualization
        
        """For FPS calculation"""
        frame_counter += 1
        cur_time = time.time()
        if cur_time - fps_timer_start > 1:
            print(f"FPS det: {(frame_counter / (cur_time - fps_timer_start)):.3f}")
            frame_counter = 0
            fps_timer_start = time.time()