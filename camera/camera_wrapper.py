# -*- coding: utf-8 -*-
"""
Wrapper for the camera control.

@author: sklykov, @license: MIT license

"""
# %% Global imports
from multiprocessing import Process, Queue, Event
from queue import Empty, Full
from pathlib import Path
from typing import Sequence
import time

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from cameras import *
else:
    from .cameras import *
local_modules = locals()  # get as a dictionary the locally imported modules for defining the content of "cameras" module
# Below the automatic exploring of the imported modules and Associated names. Class definition should contain "Camera" in a class name
cameras_cls_names = [camera_class for camera_class in local_modules.keys() if "Camera" in camera_class]
# Collect actual classes for using them below on UI
cameras_ctrl_classes = [local_modules[camera_name] for camera_name in cameras_cls_names]
cameras_ctrl_types = [ctrl_class.camera_type() for ctrl_class in cameras_ctrl_classes]


# %% Camera class
class CameraWrapper(Process):
    """Class for wrapping camera controlling functions in the additional to the main script Process() instance."""

    # Dev. note: it's not necessary to make the variables below private explicitly, since they are embedded to the Process
    initialized: bool = False  # flag - initialized or not the camera
    camera_ref = None  # handle to the camera (API specific)
    camera_type: str = "Simulated"  # provided by the calling program
    live_stream_flag: bool = False; commands_queue: Queue; trigger_commands: Event
    data_queue: Queue; trigger_data: Event; lifo_queues = None; supported_cameras: list = []
    data_triggered_queues = None; queues_triggers = None; camera_supported: bool = False
    camera_initialized: bool = False  # flag for explicit recognition that the camera is initialized (opened)

    def __init__(self, camera_type: str, commands2camera: Queue, trigger_commands: Event, data_camera: Queue, trigger_data_camera: Queue,
                 data_triggered_queues: Sequence[Queue] = None, queues_triggers: Sequence[Event] = None, lifo_queues: Sequence[Queue] = None):
        """
        CameraWrapper(Process) instance initialization.

        Parameters
        ----------
        camera_type : str
            Provided type of a camera.
        commands2camera : Queue
            Queue with sent from the main script commands, like "Snap".
        trigger_commands : Event
            Trigger for retrieving from the commands2camera queue.
        data_camera : Queue
            Queue with sent from this script data / messages / exceptions.
        trigger_data_camera : Queue
            Trigger for retrieving from the data_camera queue.
        data_triggered_queues : Sequence[Queue], optional
            Sequence with several more queues for duplicating data for the independent processes. The default is None.
        queues_triggers : Sequence[Event], optional
            Sequence with several more Events for duplicating triggers for the independent processes. The default is None.
        lifo_queues : Sequence[Queue], optional
            Queues for independent processes which just subscribe for them. The default is None.

        Raises
        ------
        ValueError
            Check provided description.

        Returns
        -------
        None.

        """
        self.commands_queue = commands2camera; self.trigger_commands = trigger_commands
        self.data_queue = data_camera; self.trigger_data = trigger_data_camera
        self.script_path = Path(__file__).parent.absolute()  # for possible access the API python wrappers
        self.sleep_time_actions_ms = 0.004  # for putting artificial delay between setting the trigger and sending the data
        if data_triggered_queues is not None and queues_triggers is not None:
            if len(data_triggered_queues) > 0 and len(queues_triggers) > 0 and len(data_triggered_queues) == len(queues_triggers):
                self.data_triggered_queues = data_triggered_queues; self.queues_triggers = queues_triggers
        if lifo_queues is not None:
            if len(lifo_queues) > 0:
                self.lifo_queues = lifo_queues
        # Check that the camera type is supported (could be duplicated from the main script)
        self.supported_cameras = cameras_ctrl_types  # can be checked / loaded from the configuration
        if camera_type in self.supported_cameras:
            self.camera_type = camera_type; self.camera_supported = True
        # Checking provided parameters to be consistent and empty
        if self.commands_queue.empty() and self.data_queue.empty() and not self.trigger_data.is_set() and not self.trigger_commands.is_set():
            if self.camera_supported:
                Process.__init__(self)  # Initialize this class on the separate process with its own memory and core
                self.initialized = True  # Process class initialized
            else:
                raise ValueError("Provided camera type isn't supported (not specified as the supported one)")
        else:
            raise ValueError("The CameraWrapper class expects to obtain empty Queues and not set Events from 'multiprocessing'")

    # %% Main Loop logic
    def run(self):
        """
        Rewritten standard method of the Process with the logic for controlling camera.

        Invoke by the instance.start() method.

        Returns
        -------
        None.

        """
        # Starting the Process loop. The camera connection should be initialized here.
        if self.initialized:
            if self.camera_type == self.supported_cameras[0]:  # automatic discovery of the imported classes
                self.camera_ref = cameras_ctrl_classes[0]()  # initialize the camera controlling class
                self.camera_initialized = self.camera_ref.initialize()  # explicit initialization method
                # self.camera_initialized = True  # placeholder for the initialization of the camera
                # Dev Note about putting time.sleep() below - if the scripts launched in Python debugger by Visual Studio Code
                if self.camera_initialized:
                    self.data_queue.put_nowait("Initialized"); time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
            else:
                self.initialized = False  # if there is no initialization logic, by default set to False

        # Loop for checking the commands from the controlling script and handling them
        while self.initialized and self.camera_initialized:
            self.trigger_commands.wait()  # wait for the externally set (by the main script) trigger
            if self.trigger_commands.is_set():
                self.trigger_commands.clear()
            # Getting the commands from the queue
            if not self.commands_queue.empty():
                try:
                    command = self.commands_queue.get_nowait()  # Handling the commands from the main script
                    # print("Camera received a command:", command)
                    # Snap single image
                    if command == "Snap" or command == "Snap Image":
                        image = self.camera_ref.snap_image()
                        # print("Received image shape in Camera class:", image.shape, flush=True)
                        if image is not None:
                            self.data_queue.put_nowait(image)
                            # print("Camera sent image on Queue", flush=True)
                        else:
                            self.data_queue.put_nowait("String placeholder Image")
                        self.trigger_data.set()  # set the trigger that the data is available
                    if command == "Stop" or command == "Quit":
                        self.close()  # close the camera wrapper
                        self.initialized = False  # set the flag for the loop to stop it
                        self.data_queue.put_nowait("Stopped"); time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
                # Handling exceptions by the getting the commands from the queue
                except (Empty, Full):
                    self.data_queue.put_nowait(Exception("Queue with commands or empty, either full. The CameraWrapper Process stopped"))
                    self.trigger_data.set(); self.initialized = False
            else:
                self.data_queue.put_nowait(Exception("Await to receive the command, by the Queue with commands is empty"))
                self.trigger_data.set(); self.initialized = False

    # %% Utility methods
    def close(self):
        """
        Close connection to the camera.

        Returns
        -------
        None.

        """
        if self.camera_type == "Simulated":
            self.camera_initialized = False; time.sleep(0.005)  # camera closing logic
