import os

import cv2

os.environ["XDG_SESSION_TYPE"] = "xcb"

def resize_and_show(frame, show_feed):
    frame_feed = cv2.resize(frame, (int(frame.shape[1]/2),int(frame.shape[0]/2)))
    # frame_feed = frame
    if show_feed:
        cv2.imshow("Image feed", frame_feed)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            return
        
def show_ook(frame, show_feed):
    if show_feed:
        for idx,frm in enumerate(frame):
            cv2.imshow(f"OOK feed {idx}", frm)
            
            if cv2.waitKey(1) & 0xFF == ord("q"):
                cv2.destroyAllWindows()
                return

def image_show(frame_queue, show_feed):
    frame_counter, skip_frame = 0, 16
    
    while True:
        frame = frame_queue.get()
        if frame is None:
            break
        
        if frame_counter % skip_frame == 0:
            resize_and_show(frame, show_feed)
        # print(f"Image size: ", frame.shape)
        frame_counter += 1
            
def ook_show(ook_queue, show_feed):
    frame_counter, skip_frame = 0, 16
    
    while True:
        ook_frame = ook_queue.get()
        
        if ook_frame is None:
            break
        
        if frame_counter % skip_frame == 0:
            show_ook(ook_frame, show_feed)
        # print(f"Image size: ", frame.shape)
        frame_counter += 1