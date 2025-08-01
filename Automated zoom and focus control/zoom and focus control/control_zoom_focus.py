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

PROGRAM_VERSION = "1.0.0"

usbOpen_flag = False
withZoom = False
withFocus = False
withIris = False
withOptFil = False

# Configure logging
logging.basicConfig(filename='lens_control.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def calculate_focus(Z):
    """Calculate focus value for a given zoom value using a 5th-degree polynomial."""
    try:
        return (4.7105e-10 * Z**5) - (1.7064e-7 * Z**4) + (1.9530e-5 * Z**3) - (2.0363e-3 * Z**2) - (0.5778 * Z) + 240.7969
    except Exception as e:
        logging.error(f"Error calculating focus for Z={Z}: {e}")
        print(f"Error calculating focus for Z={Z}: {e}")
        return None

def generate_zoom_focus_values():
    """Generate zoom and focus values in real-time using the 5th-degree polynomial for focus.
    Returns a list of dictionaries with Zoom and Focus values."""
    zoom_focus_data = []
    
    # Loop through zoom values from 80 to 243
    for Z in range(80, 244, 1):
        try:
            # Calculate and round the focus value using the polynomial
            focus_value = calculate_focus(Z)
            if focus_value is None:
                continue
            focus_value = round(focus_value)
            zoom_focus_data.append({"Zoom": Z, "Focus": focus_value})
        except Exception as e:
            logging.error(f"Error processing Z={Z}: {e}")
            print(f"Error processing Z={Z}: {e}")
            continue
    
    print(f"Generated {len(zoom_focus_data)} zoom and focus value pairs")
    logging.info(f"Generated {len(zoom_focus_data)} zoom and focus value pairs")
    return zoom_focus_data

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
                time.sleep(0.01)
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
                time.sleep(0.01)
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

def AutomatedLensControl(device_number=0, use_generator=True):
    """Control zoom and focus using generated or initial values."""
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

    # Get zoom and focus values
    zoom_values = []
    focus_values = []
    if use_generator:
        try:
            zoom_focus_data = generate_zoom_focus_values()
            zoom_values = [row["Zoom"] for row in zoom_focus_data]
            focus_values = [row["Focus"] for row in zoom_focus_data]
            print(f"Loaded {len(zoom_values)} zoom and focus value pairs from generator")
            logging.info(f"Loaded {len(zoom_values)} zoom and focus value pairs from generator")
        except Exception as e:
            print(f"Error generating zoom and focus values: {e}")
            logging.error(f"Error generating zoom and focus values: {e}")
            zoom_values = [80]  # Fallback to initial values
            focus_values = [244]
    else:
        print("Using initial values: Zoom=80, Focus=244")
        logging.info("Using initial zoom=80, focus=244")
        zoom_values = [80]
        focus_values = [244]

    if not zoom_values or not focus_values:
        print("No valid zoom or focus values. Exiting.")
        logging.error("No valid zoom or focus values")
        UsbDisconnect()
        return

    # Rescale zoom and focus values to [1, 256]
    zoom_min, zoom_max = min(zoom_values), max(zoom_values)
    focus_min, focus_max = min(focus_values), max(focus_values)
    rescaled_zoom = [RescaleValue(z, zoom_min, zoom_max, 1, 256) for z in zoom_values]
    rescaled_focus = [RescaleValue(f, focus_min, focus_max, 1, 256) for f in focus_values]

    # Map rescaled values to lens address range
    if withZoom:
        zoom_addresses = [int(np.interp(z, [1, 256], [LensCtrl.zoomMinAddr, LensCtrl.zoomMaxAddr])) for z in rescaled_zoom]
    else:
        zoom_addresses = [0] * len(rescaled_zoom)  # Placeholder if no zoom
    if withFocus:
        focus_addresses = [int(np.interp(f, [1, 256], [LensCtrl.focusMinAddr, LensCtrl.focusMaxAddr])) for f in rescaled_focus]
    else:
        focus_addresses = [0] * len(rescaled_focus)  # Placeholder if no focus

    # Apply zoom and focus values
    for i, (zoom_addr, focus_addr, orig_zoom, orig_focus, scale_zoom, scale_focus) in enumerate(
        zip(zoom_addresses, focus_addresses, zoom_values, focus_values, rescaled_zoom, rescaled_focus)
    ):
        print(f"Step {i+1}/{len(zoom_addresses)}:")
        logging.info(f"Step {i+1}/{len(zoom_addresses)}")
        if not MoveToZoomFocus(zoom_addr, focus_addr, orig_zoom, orig_focus, scale_zoom, scale_focus):
            print("Movement failed. Stopping.")
            logging.error("Movement failed")
            break
        time.sleep(0.05)  # Minimal delay for stability

    # Disconnect when done
    UsbDisconnect()
    print("Automated lens control completed.")
    logging.info("Automated lens control completed")

def main():
    """Main function to generate and control zoom and focus."""
    print(f"LensConnect Automated Control {PROGRAM_VERSION}")
    try:
        AutomatedLensControl(device_number=0, use_generator=True)
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred: {e}")
        UsbDisconnect()

if __name__ == "__main__":
    main()