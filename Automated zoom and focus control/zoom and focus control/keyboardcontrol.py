import UsbCtrl
import LensCtrl
import ConfigVal as CV
import LensAccess as LA
import LensInfo as LI
import DefVal as DV
import LensSetup as LS
import time
import logging
import numpy as np
import keyboard

PROGRAM_VERSION = "1.0.0"

usbOpen_flag = False
withZoom = False
withFocus = False
withIris = False
withOptFil = False

# Configure logging
logging.basicConfig(filename='lens_control.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def OnOff(flag):
    """Convert flag to ON/OFF string."""
    return "ON" if flag == 1 else "OFF"

def ScanUsbWithLensInfo():
    """Scan for connected USB lens devices and return the number of devices."""
    retval, numDevice = UsbCtrl.UsbGetNumDevices()
    if numDevice >= 1:
        print("No.: S/N")
        for i in range(numDevice):
            retval = UsbCtrl.UsbOpen(i)
            if retval == 0:
                retval, SnSrting = UsbCtrl.UsbGetOpenedSnDevice(i)
                retval, model = LensCtrl.ModelName()
                retval, userName = LensCtrl.UserAreaRead()
                print(f"{i:2d} : {SnSrting}, {model} {userName}")
            else:
                print(f"{i:2d} : {'Device access error.':35s} The device may already be running.")
            UsbCtrl.UsbClose()
        return numDevice
    else:
        print("No LensConnect is connected.")
        return 0

def UsbConnect(deviceNumber):
    """Connect to a USB lens device."""
    global usbOpen_flag, withZoom, withFocus, withIris, withOptFil
    logging.info(f"Connecting to device {deviceNumber}")
    retval = UsbCtrl.UsbOpen(deviceNumber)
    if retval != DV.RET_SUCCESS:
        logging.error(f"UsbOpen error: {retval}")
        print(f"UsbOpen error: {retval}")
        return retval
    
    retval = UsbCtrl.UsbSetConfig()
    if retval != DV.RET_SUCCESS:
        logging.error(f"UsbSetConfig error: {retval}")
        print(f"UsbSetConfig error: {retval}")
        return retval

    retval, capabilities = LensCtrl.CapabilitiesRead()
    LensCtrl.Status2ReadSet()

    if capabilities & CV.ZOOM_MASK:
        LensCtrl.ZoomParameterReadSet()
        if LensCtrl.status2 & CV.ZOOM_MASK == DV.INIT_COMPLETED:
            LensCtrl.ZoomCurrentAddrReadSet()
        withZoom = True

    if capabilities & CV.FOCUS_MASK:
        LensCtrl.FocusParameterReadSet()
        if LensCtrl.status2 & CV.FOCUS_MASK == DV.INIT_COMPLETED:
            LensCtrl.FocusCurrentAddrReadSet()
        withFocus = True

    if capabilities & CV.IRIS_MASK:
        LensCtrl.IrisParameterReadSet()
        if LensCtrl.status2 & CV.IRIS_MASK == DV.INIT_COMPLETED:
            LensCtrl.IrisCurrentAddrReadSet()
        withIris = True

    if capabilities & CV.OPT_FILTER_MASK:
        LensCtrl.OptFilterParameterReadSet()
        if LensCtrl.status2 & CV.OPT_FILTER_MASK == DV.INIT_COMPLETED:
            LensCtrl.OptFilterCurrentAddrReadSet()
        withOptFil = True
    
    usbOpen_flag = True
    logging.info("Device connected successfully")
    return 0

def UsbDisconnect():
    """Disconnect from the USB lens device."""
    global usbOpen_flag, withZoom, withFocus, withIris, withOptFil
    UsbCtrl.UsbClose()
    usbOpen_flag = False
    withZoom = False
    withFocus = False
    withIris = False
    withOptFil = False
    logging.info("Device disconnected")

def InitializeLens():
    """Initialize zoom and focus if necessary."""
    if withZoom and not (LensCtrl.status2 & CV.ZOOM_MASK == DV.INIT_COMPLETED):
        print("Initializing Zoom")
        logging.info("Initializing Zoom")
        LensCtrl.ZoomInit()
        time.sleep(1)
        LensCtrl.Status2ReadSet()
    if withFocus and not (LensCtrl.status2 & CV.FOCUS_MASK == DV.INIT_COMPLETED):
        print("Initializing Focus")
        logging.info("Initializing Focus")
        LensCtrl.FocusInit()
        time.sleep(1)
        LensCtrl.Status2ReadSet()

def SetMaxSpeed():
    """Set zoom and focus to maximum speed."""
    try:
        if withZoom:
            LS.ZoomSpeedChange()  # Check LensSetup module for correct method
            logging.info("Set zoom speed (default or max)")
        if withFocus:
            LS.FocusSpeedChange()  # Check LensSetup module for correct method
            logging.info("Set focus speed (default or max)")
    except AttributeError as e:
        logging.warning(f"Speed change function not found: {e}")
        print(f"Warning: Could not set speed. Using default speed. Error: {e}")
    except TypeError as e:
        logging.warning(f"Speed change function error: {e}")
        print(f"Warning: Could not set speed. Using default speed. Error: {e}")

def RescaleValue(value, in_min, in_max, out_min=1, out_max=256):
    """Rescale a value from [in_min, in_max] to [out_min, out_max]."""
    if in_max == in_min:
        return out_min
    return out_min + (out_max - out_min) * (value - in_min) / (in_max - in_min)

def MoveToZoomFocus(zoom_addr, focus_addr, original_zoom, original_focus, scaled_zoom, scaled_focus):
    """Move zoom and focus to specified addresses and print original, scaled, and current values.
    Adjusts zoom first, then focus."""
    if withZoom and (LensCtrl.status2 & CV.ZOOM_MASK == DV.INIT_COMPLETED):
        if LensCtrl.zoomMinAddr <= zoom_addr <= LensCtrl.zoomMaxAddr:
            print(f"Zoom - Original: {original_zoom:.2f}, Scaled [1,256]: {scaled_zoom:.2f}, Desired address: {zoom_addr}")
            logging.info(f"Zoom - Original: {original_zoom:.2f}, Scaled: {scaled_zoom:.2f}, Desired address: {zoom_addr}")
            try:
                LensCtrl.ZoomMove(zoom_addr)  # Replace with correct function if needed
                time.sleep(0.1)
                LensCtrl.ZoomCurrentAddrReadSet()
                print(f"Current zoom address: {LensCtrl.zoomCurrentAddr}")
                logging.info(f"Current zoom address: {LensCtrl.zoomCurrentAddr}")
            except AttributeError as e:
                logging.error(f"ZoomMove error: {e}")
                print(f"Error: LensCtrl.ZoomMove not found. Please check the LensCtrl module. Error: {e}")
                return False
            except Exception as e:
                logging.error(f"Zoom movement error: {e}")
                print(f"Error during zoom movement: {e}")
                return False
        else:
            print(f"Zoom address {zoom_addr} out of range [{LensCtrl.zoomMinAddr}, {LensCtrl.zoomMaxAddr}]")
            logging.warning(f"Zoom address {zoom_addr} out of range")
    
    # Small delay to ensure zoom stabilizes before adjusting focus
    time.sleep(0.05)
    
    if withFocus and (LensCtrl.status2 & CV.FOCUS_MASK == DV.INIT_COMPLETED):
        if LensCtrl.focusMinAddr <= focus_addr <= LensCtrl.focusMaxAddr:
            print(f"Focus - Original: {original_focus:.2f}, Scaled [1,256]: {scaled_focus:.2f}, Desired address: {focus_addr}")
            logging.info(f"Focus - Original: {original_focus:.2f}, Scaled: {scaled_focus:.2f}, Desired address: {focus_addr}")
            try:
                LensCtrl.FocusMove(focus_addr)  # Replace with correct function if needed
                time.sleep(0.1)
                LensCtrl.FocusCurrentAddrReadSet()
                print(f"Current focus address: {LensCtrl.focusCurrentAddr}")
                logging.info(f"Current focus address: {LensCtrl.focusCurrentAddr}")
            except AttributeError as e:
                logging.error(f"FocusMove error: {e}")
                print(f"Error: LensCtrl.FocusMove not found. Please check the LensCtrl module. Error: {e}")
                return False
            except Exception as e:
                logging.error(f"Focus movement error: {e}")
                print(f"Error during focus movement: {e}")
                return False
        else:
            print(f"Focus address {focus_addr} out of range [{LensCtrl.focusMinAddr}, {LensCtrl.focusMaxAddr}]")
            logging.warning(f"Focus address {focus_addr} out of range")
    return True

def AutomatedLensControl(device_number=0):
    """Control zoom and focus using keyboard input."""
    # Connect to the lens
    if not usbOpen_flag:
        num_devices = ScanUsbWithLensInfo()
        if num_devices == 0:
            print("No devices available. Exiting.")
            logging.error("No devices available")
            return
        retval = UsbConnect(device_number)
        if retval != DV.RET_SUCCESS:
            print(f"Failed to connect to device {device_number}. Exiting.")
            logging.error(f"Failed to connect to device {device_number}: {retval}")
            return

    # Initialize zoom and focus
    InitializeLens()

    # Set maximum speed
    SetMaxSpeed()

    # Initialize zoom and focus values
    current_zoom = 80
    current_focus = 244
    zoom_min, zoom_max = 80, 243  # Range for rescaling (adjust if needed)
    focus_min, focus_max = 143, 244  # Range for rescaling (approximate, adjust if needed)

    print("Keyboard controls:")
    print("  1: Increase zoom by 1")
    print("  2: Decrease zoom by 1")
    print("  3: Increase focus by 1")
    print("  4: Decrease focus by 1")
    print("  q: Quit")
    print(f"Starting values: Zoom={current_zoom}, Focus={current_focus}")

    try:
        while True:
            # Check for keyboard input
            if keyboard.is_pressed('1'):
                current_zoom = min(current_zoom + 1, zoom_max)
                print(f"Zoom increased to {current_zoom}")
                logging.info(f"Zoom increased to {current_zoom}")
            elif keyboard.is_pressed('2'):
                current_zoom = max(current_zoom - 1, zoom_min)
                print(f"Zoom decreased to {current_zoom}")
                logging.info(f"Zoom decreased to {current_zoom}")
            elif keyboard.is_pressed('3'):
                current_focus = min(current_focus + 1, focus_max)
                print(f"Focus increased to {current_focus}")
                logging.info(f"Focus increased to {current_focus}")
            elif keyboard.is_pressed('4'):
                current_focus = max(current_focus - 1, focus_min)
                print(f"Focus decreased to {current_focus}")
                logging.info(f"Focus decreased to {current_focus}")
            elif keyboard.is_pressed('q'):
                print("Exiting...")
                logging.info("User requested exit")
                break
            else:
                time.sleep(0.01)  # Avoid CPU overload
                continue

            # Rescale zoom and focus to [1, 256]
            scaled_zoom = RescaleValue(current_zoom, zoom_min, zoom_max, 1, 256)
            scaled_focus = RescaleValue(current_focus, focus_min, focus_max, 1, 256)

            # Map rescaled values to lens address range
            if withZoom:
                zoom_addr = int(np.interp(scaled_zoom, [1, 256], [LensCtrl.zoomMinAddr, LensCtrl.zoomMaxAddr]))
            else:
                zoom_addr = 0
            if withFocus:
                focus_addr = int(np.interp(scaled_focus, [1, 256], [LensCtrl.focusMinAddr, LensCtrl.focusMaxAddr]))
            else:
                focus_addr = 0

            # Apply zoom and focus
            if not MoveToZoomFocus(zoom_addr, focus_addr, current_zoom, current_focus, scaled_zoom, scaled_focus):
                print("Movement failed. Stopping.")
                logging.error("Movement failed")
                break

            time.sleep(0.2)  # Delay for stability and to debounce keyboard input

    except Exception as e:
        print(f"Error during keyboard control: {e}")
        logging.error(f"Error during keyboard control: {e}")

    # Disconnect when done
    UsbDisconnect()
    print("Automated lens control completed.")
    logging.info("Automated lens control completed")

def main():
    """Main function to control zoom and focus via keyboard."""
    print(f"LensConnect Automated Control {PROGRAM_VERSION}")
    try:
        AutomatedLensControl(device_number=0)
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred: {e}")
        UsbDisconnect()

if __name__ == "__main__":
    main()