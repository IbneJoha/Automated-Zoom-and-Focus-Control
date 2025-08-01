import cv2
import time
from ids_peak import ids_peak
from ids_peak import ids_peak_ipl_extension
from ultralytics import YOLO
import argparse

def main():
    # Argparse untuk menerima input model YOLO
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default='C:/Joha_IDS/01/model/model12_n/best.pt', help="Path to YOLO model")
    parser.add_argument("--conf", type=float, default=0.3, help="Confidence threshold")
    args = parser.parse_args()

    # Load model YOLO
    model = YOLO(args.model, verbose=False)

    # Initialize IDS Peak Library
    ids_peak.Library.Initialize()
    device_manager = ids_peak.DeviceManager.Instance()

    try:
        device_manager.Update()
        if device_manager.Devices().empty():
            print("No device found. Exiting Program.")
            return -1

        device = device_manager.Devices()[0].OpenDevice(ids_peak.DeviceAccessType_Control)
        remote_nodemap = device.RemoteDevice().NodeMaps()[0]

        remote_nodemap.FindNode("UserSetSelector").SetCurrentEntry("Default")
        remote_nodemap.FindNode("UserSetLoad").Execute()
        remote_nodemap.FindNode("UserSetLoad").WaitUntilDone()

        # Set exposure time for high FPS
        remote_nodemap.FindNode("ExposureTime").SetValue(1500)
        # print("Exposure Time set to 1500 us")

        # Set FPS
        target_fps = 130
        remote_nodemap.FindNode("AcquisitionFrameRate").SetValue(target_fps)
        print(f"Acquisition Frame Rate set to {target_fps} FPS")

        data_stream = device.DataStreams()[0].OpenDataStream()
        payload_size = remote_nodemap.FindNode("PayloadSize").Value()

        # Increase buffer count to reduce frame drop
        buffer_count_max = max(data_stream.NumBuffersAnnouncedMinRequired(), 20)

        for _ in range(buffer_count_max):
            buffer = data_stream.AllocAndAnnounceBuffer(payload_size)
            data_stream.QueueBuffer(buffer)

        remote_nodemap.FindNode("TLParamsLocked").SetValue(1)
        data_stream.StartAcquisition()
        remote_nodemap.FindNode("AcquisitionStart").Execute()
        remote_nodemap.FindNode("AcquisitionStart").WaitUntilDone()

        # start_time = time.time()
        frame_count = 0

        while True:
            try:
                buffer = data_stream.WaitForFinishedBuffer(500)
                img = ids_peak_ipl_extension.BufferToImage(buffer)


                # Convert image to RGB for faster processing
                frame = img.get_numpy_2D()
                # frame = cv2.cvtColor(frame, cv2.COLOR_BAYER_RG2RGB)  # (1080, 1440, 3)

                frame_count += 1
                # elapsed_time = time.time() - start_time
                # fps = frame_count / elapsed_time

                # # Print FPS
                # print(f"FPS: {fps:.2f}")
                if len(frame.shape) == 2:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)



                # Skip the first few frames (e.g., frame_count < 2)
                if frame_count < 3:
                    data_stream.QueueBuffer(buffer)
                    continue
                

                if frame_count > 10:


                    # Perform YOLO object detection on the frame
                    results = model(frame, conf=args.conf, verbose=False)

                    # Draw bounding boxes for detected objects
                    for result in results[0].boxes:
                        x1, y1, x2, y2 = map(int, result.xyxy[0].tolist())
                        # score = float(result.conf.item())
                        # label = result.cls[0].item()

                        # Calculate width and height
                        width = x2 - x1
                        height = y2 - y1

                        # Calculate area of the bounding box
                        area = width * height

                        # Draw rectangle and label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
                        # cv2.putText(frame, f"ID: {label} | Score: {score:.2f}", (x1, y1 - 10),
                        #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                        # Print the coordinates, width, height, and area of the bounding box
                        # print(f"Coordinates of point 1: ({x1}, {y1}), Coordinates of point 2: ({x2}, {y2})")
                        print(f"Height: {height}, Width: {width}")
                        print(f"Bounding Box Area: {area}")



                    # Show live video feed with detections
                    cv2.imshow("Live Feed", frame)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                    data_stream.QueueBuffer(buffer)

            except Exception as e:
                print(f"Exception: {e}")

        print("Stopping acquisition...")
        remote_nodemap.FindNode("AcquisitionStop").Execute()
        remote_nodemap.FindNode("AcquisitionStop").WaitUntilDone()

        data_stream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
        data_stream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)
        for buffer in data_stream.AnnouncedBuffers():
            data_stream.RevokeBuffer(buffer)

        remote_nodemap.FindNode("TLParamsLocked").SetValue(0)

    except Exception as e:
        print(f"EXCEPTION: {e}")
        return -2

    finally:
        ids_peak.Library.Close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
