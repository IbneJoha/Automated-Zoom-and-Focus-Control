import datetime
import time

from ids_peak import ids_peak
from ids_peak import ids_peak_ipl_extension

"""camera settings param file"""
param_path = "/home/wicomai/occ/config/mono8.cset"
"""define camera exposure time"""
ExposureTime = 74
TargetFPS = 220

def cam_streaming(frame_queue):
    """init acmera connection"""
    ids_peak.Library.Initialize()
    device_manager = ids_peak.DeviceManager.Instance()
    
    # try:
    device_manager.Update()

    if device_manager.Devices().empty():
        print("No device found. Exiting Program.")
        return -1

    """open the camera"""
    device = device_manager.Devices()[0].OpenDevice(ids_peak.DeviceAccessType_Control)
    remote_nodemap = device.RemoteDevice().NodeMaps()[0]

    remote_nodemap.FindNode("UserSetSelector").SetCurrentEntry("Default")
    remote_nodemap.FindNode("UserSetLoad").Execute()
    remote_nodemap.FindNode("UserSetLoad").WaitUntilDone()
    
    """load the camera param settings"""
    remote_nodemap.LoadFromFile(param_path)

    """check image format"""
    pixel_format = remote_nodemap.FindNode("PixelFormat").CurrentEntry().SymbolicValue()
    print(f"Using PixelFormat: {pixel_format}")

    """reinforce some important settings"""
    # remote_nodemap.FindNode("ExposureAuto").SetCurrentEntry("Continuous")
    remote_nodemap.FindNode("GainAuto").SetCurrentEntry("Continuous")
    remote_nodemap.FindNode("BalanceWhiteAuto").SetCurrentEntry("Continuous")
    remote_nodemap.FindNode("ExposureTime").SetValue(ExposureTime)
    
    """manually set the camera frame rate"""
    max_frame_rate = remote_nodemap.FindNode("AcquisitionFrameRate").Maximum()
    remote_nodemap.FindNode("AcquisitionFrameRate").SetValue(TargetFPS)
    print(f"Max Frame Rate: {max_frame_rate}")

    """"start camera stream"""
    data_stream = device.DataStreams()[0].OpenDataStream()
    payload_size = remote_nodemap.FindNode("PayloadSize").Value()
    buffer_count_max = data_stream.NumBuffersAnnouncedMinRequired()
    
    for _ in range(buffer_count_max):
        buffer = data_stream.AllocAndAnnounceBuffer(payload_size)
        data_stream.QueueBuffer(buffer)

    remote_nodemap.FindNode("TLParamsLocked").SetValue(1)
    data_stream.StartAcquisition()
    remote_nodemap.FindNode("AcquisitionStart").Execute()
    remote_nodemap.FindNode("AcquisitionStart").WaitUntilDone()
    
    """define variables for counting the fps"""
    loop_counter, frame_counter = 0, 0
    # fps_timer_start = datetime.datetime.now().timestamp()
    fps_timer_start = time.time()
    
    """continuously grabbing image from camera"""
    while True:
        try:
            """wait for camera image buffer, set to 1 for faster speed (no need to wait for the buffer to full)"""
            buffer = data_stream.WaitForFinishedBuffer(1)
            img = ids_peak_ipl_extension.BufferToImage(buffer)

            """reshape the image"""
            frame = img.get_numpy_3D()
            # print(f"Frame shape ori: {frame.shape}")
            
            """put the fresh image into the queue"""
            frame_queue.put(frame)
            data_stream.QueueBuffer(buffer)
            
            """for measuring fps"""
            frame_counter += 1
            cur_time = time.time()
            if cur_time - fps_timer_start > 1:
                print(f"FPS: {(frame_counter / (cur_time - fps_timer_start)):.3f}")
                frame_counter = 0
                fps_timer_start = time.time()
                loop_counter += 1

        except Exception as e:
            """
            because the buffer size is 1, sometimes the image graber is too fast
            when try to grab image meanwhile the image is not ready, it raise errors
            this exception to catch such errors and skip it to next itreration"""
            # print(f"Exception: {e}")
            continue
    
    """stopping the image acquisition function"""
    print("Stopping acquisition...")
    remote_nodemap.FindNode("AcquisitionStop").Execute()
    remote_nodemap.FindNode("AcquisitionStop").WaitUntilDone()

    data_stream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
    data_stream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)
    for buffer in data_stream.AnnouncedBuffers():
        data_stream.RevokeBuffer(buffer)

    remote_nodemap.FindNode("TLParamsLocked").SetValue(0)
    ids_peak.Library.Close()