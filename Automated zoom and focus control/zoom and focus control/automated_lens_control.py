import UsbCtrl
import LensCtrl
import ConfigVal as CV
import LensAccess as LA
import LensInfo as LI
import DefVal as DV
import LensSetup as LS
import time
import numpy as np

PROGRAM_VERSION = "1.0.0"

usbOpen_flag = False
withZoom = False
withFocus = False
withIris = False
withOptFil = False

def OnOff(flag):
    if flag == 1:
        return "ON"
    else:
        return "OFF"

def ScanUsbWithLensInfo():
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
    global usbOpen_flag, withZoom, withFocus, withIris, withOptFil
    retval = UsbCtrl.UsbOpen(deviceNumber)
    if retval != DV.RET_SUCCESS:
        print(f"UsbOpen error: {retval}")
        return retval
    
    retval = UsbCtrl.UsbSetConfig()
    if retval != DV.RET_SUCCESS:
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
    return 0

def UsbDisconnect():
    global usbOpen_flag, withZoom, withFocus, withIris, withOptFil
    UsbCtrl.UsbClose()
    usbOpen_flag = False
    withZoom = False
    withFocus = False
    withIris = False
    withOptFil = False

def InitializeLens():
    if withZoom and not (LensCtrl.status2 & CV.ZOOM_MASK == DV.INIT_COMPLETED):
        print("Initializing Zoom")
        LensCtrl.ZoomInit()
        time.sleep(1)  # Wait for initialization
        LensCtrl.Status2ReadSet()  # Update status
    if withFocus and not (LensCtrl.status2 & CV.FOCUS_MASK == DV.INIT_COMPLETED):
        print("Initializing Focus")
        LensCtrl.FocusInit()
        time.sleep(1)  # Wait for initialization
        LensCtrl.Status2ReadSet()  # Update status

def MoveToZoomFocus(zoom_addr, focus_addr):
    if withZoom and (LensCtrl.status2 & CV.ZOOM_MASK == DV.INIT_COMPLETED):
        if LensCtrl.zoomMinAddr <= zoom_addr <= LensCtrl.zoomMaxAddr:
            print(f"Moving zoom to address: {zoom_addr}")
            try:
                LensCtrl.ZoomMove(zoom_addr)  # Use ZoomMove (verify this function exists)
                time.sleep(0.5)  # Allow movement to complete
            except AttributeError:
                print("Error: LensCtrl.ZoomMove not found. Please check the LensCtrl module.")
                return
        else:
            print(f"Zoom address {zoom_addr} out of range [{LensCtrl.zoomMinAddr}, {LensCtrl.zoomMaxAddr}]")
    if withFocus and (LensCtrl.status2 & CV.FOCUS_MASK == DV.INIT_COMPLETED):
        if LensCtrl.focusMinAddr <= focus_addr <= LensCtrl.focusMaxAddr:
            print(f"Moving focus to address: {focus_addr}")
            try:
                LensCtrl.FocusMove(focus_addr)  # Use FocusMove (verify this function exists)
                time.sleep(0.5)  # Allow movement to complete
            except AttributeError:
                print("Error: LensCtrl.FocusMove not found. Please check the LensCtrl module.")
                return
        else:
            print(f"Focus address {focus_addr} out of range [{LensCtrl.focusMinAddr}, {LensCtrl.focusMaxAddr}]")

def GenerateZoomFocusValues(num_steps=5):
    zoom_values = []
    focus_values = []
    if withZoom and (LensCtrl.status2 & CV.ZOOM_MASK == DV.INIT_COMPLETED):
        zoom_values = np.linspace(LensCtrl.zoomMinAddr, LensCtrl.zoomMaxAddr, num_steps, dtype=int).tolist()
    if withFocus and (LensCtrl.status2 & CV.FOCUS_MASK == DV.INIT_COMPLETED):
        focus_values = np.linspace(LensCtrl.focusMinAddr, LensCtrl.focusMaxAddr, num_steps, dtype=int).tolist()
    return zoom_values, focus_values

def AutomatedLensControl(device_number=0, num_steps=5):
    # Connect to the lens
    if not usbOpen_flag:
        num_devices = ScanUsbWithLensInfo()
        if num_devices == 0:
            print("No devices available. Exiting.")
            return
        retval = UsbConnect(device_number)
        if retval != DV.RET_SUCCESS:
            print(f"Failed to connect to device {device_number}. Exiting.")
            return

    # Initialize zoom and focus if necessary
    InitializeLens()

    # Generate zoom and focus values
    zoom_values, focus_values = GenerateZoomFocusValues(num_steps)
    if not zoom_values and not focus_values:
        print("No zoom or focus capabilities available or initialized. Exiting.")
        UsbDisconnect()
        return

    print(f"Generated {len(zoom_values)} zoom values: {zoom_values}")
    print(f"Generated {len(focus_values)} focus values: {focus_values}")

    # Apply zoom and focus values sequentially
    max_steps = max(len(zoom_values), len(focus_values))
    for i in range(max_steps):
        zoom_addr = zoom_values[i] if i < len(zoom_values) else zoom_values[-1]
        focus_addr = focus_values[i] if i < len(focus_values) else focus_values[-1]
        print(f"Step {i+1}/{max_steps}:")
        MoveToZoomFocus(zoom_addr, focus_addr)
        time.sleep(1)  # Delay between steps for smooth operation

    # Disconnect when done
    UsbDisconnect()
    print("Automated lens control completed.")

def main():
    print(f"LensConnect Automated Control {PROGRAM_VERSION}")
    try:
        AutomatedLensControl(device_number=0, num_steps=5)
    except Exception as e:
        print(f"An error occurred: {e}")
        UsbDisconnect()

if __name__ == "__main__":
    main()