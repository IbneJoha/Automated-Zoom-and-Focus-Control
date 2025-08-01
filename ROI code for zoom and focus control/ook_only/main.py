from multiprocessing import Process, Queue

from ids_cam_init import cam_streaming
from obj_detection_tracking import obj_detector
from visualization import image_show, ook_show

if __name__ == "__main__":
    """define the required queue"""
    ori_frame_queue = Queue(maxsize=5000)
    ook_roi_queue = Queue(maxsize=5000)
    vis_frame_queue = Queue(maxsize=5000)
    show_feed = True
    
    """for multiprocessing"""
    mp_img_acquisition = Process(target=cam_streaming, args=(ori_frame_queue,)) 
    mp_obj_detector = Process(target=obj_detector, args=(ori_frame_queue,ook_roi_queue,vis_frame_queue))
    mp_img_feed = Process(target=image_show, args=(vis_frame_queue,show_feed))
    mp_ook_feed = Process(target=ook_show, args=(ook_roi_queue,show_feed))
    
    mp_img_acquisition.start()
    mp_obj_detector.start()
    mp_img_feed.start()
    mp_ook_feed.start()
    
    mp_img_acquisition.join()
    mp_obj_detector.join()
    mp_img_feed.join()
    mp_ook_feed.join()