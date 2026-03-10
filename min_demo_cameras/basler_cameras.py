# -*- coding: utf-8 -*-
"""
Script for testing camera opening, getting properties and grabbing image.

@author: @sklykov

"""
# %% Imports
import time

global pypylon_installed
pypylon_installed = False
try:
    import pypylon; global pypylon
    if pypylon is not None:
        pypylon_installed = True
except ModuleNotFoundError:
    pass

# %% Module parameters
standard_delay_s = 2.5*1E-3

# %% Run as main script
if __name__ == "__main__":
    print("\n***Test Summary***\n")
    if pypylon_installed:
        from pypylon import pylon
        tl_factory = pylon.TlFactory.GetInstance(); devices = None; devices = tl_factory.EnumerateDevices()
        if devices is not None and len(devices) > 0:
            camera_handle = pylon.InstantCamera(tl_factory.CreateFirstDevice())
            if camera_handle is not None:
                print("Basler Camera found:", camera_handle.GetDeviceInfo())
            time.sleep(standard_delay_s); camera_handle.Open(); time.sleep(standard_delay_s)
            if camera_handle is not None and camera_handle.IsOpen():
                # Get the properties of camera
                camera_handle.Width.SetValue(camera_handle.Width.Max); img_width = camera_handle.Width.Max
                camera_handle.Height.SetValue(camera_handle.Height.Max); img_height = camera_handle.Height.Max
                print("Image WxH:", img_width, img_height)
                nodemap = camera_handle.GetNodeMap(); nodes = nodemap.GetNodes()
                for node in nodes:
                    try:
                        name = node.GetName(); print(name)
                    except Exception:
                        pass
                # Close connection
                camera_handle.Close(); time.sleep(standard_delay_s)
        else:
            print("No connected cameras found")
    else:
        print("Install pypylon")
