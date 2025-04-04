# -*- coding: utf-8 -*-
"""
Wrapper for the camera control.

@author: sklykov, @license: MIT license

"""
# %% Global imports
from multiprocessing import Process, Queue, Event
from queue import Empty, Full
from queue import Queue as thQueue
from threading import Thread
from pathlib import Path
from typing import Sequence
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

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
    gray_scaled_img: bool = False  # flag for designating type of acquired image on a camera

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
        self.script_path = Path(__file__).parent.parent.absolute()  # for possible access the API python wrappers
        self.sleep_time_actions_ms = 0.004  # for putting artificial delay between setting the trigger and sending the data
        self.record_flag = False  # flag for start recording streamed single snapped images
        self.fps = None  # will automatically measure and correct FPS (NOTE if there is direct control for setting exposure time)
        self.exp_time_changed = False  # flag for checking if exp. time or camera FPS setting changed
        self.images2record = None  # placeholder for queue with images for recording
        self.video_file_path = None  # placeholder for a video file path used for recording
        # Checking input parameters
        if data_triggered_queues is not None and queues_triggers is not None:
            if len(data_triggered_queues) > 0 and len(queues_triggers) > 0 and len(data_triggered_queues) == len(queues_triggers):
                self.data_triggered_queues = data_triggered_queues; self.queues_triggers = queues_triggers
        if lifo_queues is not None:
            if len(lifo_queues) > 0:
                self.lifo_queues = lifo_queues
        # Check that the camera type is supported (could be duplicated from the main script)
        self.supported_cameras = cameras_ctrl_types  # can be checked / loaded from the configuration
        print("Supported cameras:", cameras_ctrl_types, flush=True)
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
            if self.camera_type in self.supported_cameras:  # automatic discovery of the imported classes
                camera_index = self.supported_cameras.index(self.camera_type)
                self.camera_ref = cameras_ctrl_classes[camera_index]()  # initialize the camera controlling class
                self.camera_initialized = self.camera_ref.initialize()  # explicit initialization method
                # self.camera_initialized = True  # placeholder for the initialization of the camera
                # Dev Note about putting time.sleep() below - if the scripts launched in Python debugger by Visual Studio Code
                if self.camera_initialized:
                    self.data_queue.put_nowait("Initialized"); time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
                else:
                    report = self.camera_ref.initialization_status()
                    self.data_queue.put_nowait("NOT Initialized. Problem report:\n" + report)
                    time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
            else:
                self.initialized = False  # if there is no initialization logic, by default set to False

        # Loop for checking the commands from the controlling script and handling them
        while self.initialized and self.camera_initialized:
            self.trigger_commands.wait()  # wait for the externally set (by the main script) trigger
            if self.trigger_commands.is_set():
                self.trigger_commands.clear()  # return trigger, which starts logic below, to a default value (False)
            # Getting the commands from a queue
            if not self.commands_queue.empty():
                try:
                    command = self.commands_queue.get_nowait()  # Handling the commands from the main script
                    # print("Camera received a command:", command)
                    if isinstance(command, str):  # command provided as a simple string
                        # Snap single image
                        if command == "Snap" or command == "Snap Image":
                            # t1 = time.perf_counter()  # will be used for setting FPS setting
                            image = self.camera_ref.snap_image()  # calling the implemented method from an abstract class
                            # passed_s = round((time.perf_counter() - t1), 9)
                            if self.record_flag:
                                # passed_ms = int(round(1000.0*(time.perf_counter() - t1), 0))  # measured time inms for single acquisition
                                timestamp_str = datetime.fromtimestamp(time.time()).strftime('%H:%M:%S.%f')[:-3]
                                # print("Passed ms:", passed_ms, flush=True)
                                # print("Timestamp: ", timestamp_str, flush=True)
                                pil_img = Image.fromarray(image)  # conversion numpy array to PIL image
                                draw_handle = ImageDraw.Draw(pil_img)  # draw handle for put text
                                font = ImageFont.truetype(font='arial.ttf', size=22)  # embedded fonts
                                position = (25, 25)  # (x, y) position of writing
                                draw_handle.text(position, timestamp_str, fill=0, font=font)  # Add black text to a gray image
                                image = np.array(pil_img)  # conversion PIL image to np.ndarray
                                if not self.images2record.full():
                                    self.images2record.put_nowait(image)
                            else:
                                # if not self.exp_time_changed and passed_s > 0.0:
                                #     if self.fps is None:
                                #         self.fps = int(round(1.0/passed_s, 0))  # first estimation of FPS
                                #     else:
                                #         self.fps = int(round(0.5*(self.fps + round(1.0/passed_s, 0)), 0))  # averaging of estimated FPS
                                #     # print("Measured FPS:", self.fps, flush=True)
                                # elif self.exp_time_changed:  # acknowledge changed exposure time
                                #     self.fps = None; self.exp_time_changed = False
                                if self.exp_time_changed:
                                    self.exp_time_changed = False
                            # print("Received image shape in Camera class:", image.shape, flush=True)
                            if image is not None:
                                self.data_queue.put_nowait(image)
                                # print("Camera sent image on Queue", flush=True)
                            else:
                                self.data_queue.put_nowait("String placeholder Image")
                            self.trigger_data.set()  # set the trigger that the data is available for the calling main module
                        elif command == "Start Recording":
                            self.record_flag = True
                            self.images2record = thQueue(maxsize=20)
                            self.record_thread = Thread(target=self.record); self.record_thread.start()
                            print("Start recording", flush=True)
                        elif command == "Stop Recording":
                            self.record_flag = False; time.sleep(2.5*self.sleep_time_actions_ms)
                            if self.record_thread.is_alive():
                                self.record_thread.join(timeout=0.2)
                            if not self.images2record.empty():
                                while not self.images2record.empty():
                                    try:
                                        self.images2record.get_nowait()
                                    except Empty:
                                        break
                            del self.images2record; self.images2record = None
                            print("Stop recording", flush=True)
                        elif command == "Get FPS":
                            if self.fps is not None:
                                self.data_queue.put_nowait(self.fps)
                            else:
                                self.data_queue.put_nowait(0)  # default value if FPS not measured
                            self.trigger_data.set()  # set the trigger that the data is available for the calling main module
                        elif command == "Stop" or command == "Quit":
                            self.close()  # close the camera wrapper
                            self.initialized = False  # set the flag for the loop to stop it
                            self.data_queue.put_nowait("Stopped"); time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
                    # Commands with parameters
                    elif isinstance(command, tuple):
                        (command_str, parameters) = command  # unpacking tuple
                        # Set exposure time
                        if command_str == "Set Exposure Time":
                            exp_time_set = self.camera_ref.set_exp_time(int(parameters))
                            if exp_time_set:
                                exp_time = self.camera_ref.get_exp_time()
                                self.exp_time_changed = True
                                if isinstance(exp_time, int):
                                    self.data_queue.put_nowait(exp_time); time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
                            else:
                                self.data_queue.put_nowait("Exposure Time NOT SET"); time.sleep(self.sleep_time_actions_ms)
                                self.trigger_data.set()
                        # Store measured on the main UI FPS
                        elif command_str == "Measured FPS":
                            self.fps = int(parameters)  # set measured FPS
                    # Some reporting of not recognized commands
                    else:
                        print("Camera received NOT RECOGNIZED command:", command, flush=True)
                # Handling exceptions by the getting the commands from the queue
                except (Empty, Full):
                    self.data_queue.put_nowait(Exception("Queue with commands or empty, either full. The CameraWrapper Process stopped"))
                    self.trigger_data.set(); self.initialized = False
            else:
                self.data_queue.put_nowait(Exception("Await to receive the command, but the Queue with commands is empty"))
                self.trigger_data.set(); self.initialized = False

    # %% Record method (can be moved in an additional Process isntead of Thread)
    def record(self):
        """
        Start record of snaps stream in video with ".mov" format.

        Returns
        -------
        None.

        """
        print("Start recording Thread", flush=True)
        if self.video_file_path is None:
            timestamp = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d_%H-%M-%S")
            self.video_file_path = str(self.script_path.joinpath("test_video_" + timestamp + ".mov"))
        first_step = True  # flag to create the video file handler
        while self.record_flag:
            if self.images2record is not None and not self.images2record.empty():
                image2record = self.images2record.get_nowait()
                # print("Get for recording an image:", image2record.shape, flush=True)
                if first_step:  # prepare video file to write in
                    self.cv2_codec = cv2.VideoWriter_fourcc(*'jpeg')  # 'mp4v', 'jpeg' for .mov file
                    # self.cv2_codec = cv2.VideoWriter_fourcc(*'MJPG')  # for .avi file: xvid, mp4, mj
                    img_shape_len = len(image2record.shape)  # length of image shape, assuming 2 for grayscaled image, 3 - for RGB (BGR)
                    if img_shape_len == 2:
                        h, w = image2record.shape
                        # HINT: VideoWriter not supporting gray-scaled images, convert it before
                        image2record = cv2.cvtColor(image2record, cv2.COLOR_GRAY2BGR)
                        self.gray_scaled_img = True  # for designating of acquired image type
                    elif img_shape_len == 3:
                        h, w, _ = image2record.shape
                        self.gray_scaled_img = False
                        image2record = cv2.cvtColor(image2record, cv2.COLOR_RGB2BGR)  # required back conversion for pyopencv
                    self.video_writer = cv2.VideoWriter(self.video_file_path, self.cv2_codec,
                                                        self.fps, (w, h))
                    self.video_writer.write(image2record)
                    first_step = False
                else:
                    if self.gray_scaled_img:
                        image2record = cv2.cvtColor(image2record, cv2.COLOR_GRAY2BGR)  # conversion from grayscale image to BGR format
                    image2record = cv2.cvtColor(image2record, cv2.COLOR_RGB2BGR)  # required back conversion for pyopencv
                    self.video_writer.write(image2record)  # write a frame
            else:
                time.sleep(self.sleep_time_actions_ms)
        if not self.record_flag:
            self.video_writer.release()  # close a file
            self.video_file_path = None  # back to a default value
            print("Stop recording Thread", flush=True)

    # %% Utility methods
    def close(self):
        """
        Close connection to the camera.

        Returns
        -------
        None.

        """
        self.camera_ref.close()  # closing logic should be implemented by the camera
