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
import traceback

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from cameras import *
    from utility_funcs import clean_mp_queue
else:
    from .cameras import *
    from .utility_funcs import clean_mp_queue
local_modules = locals()  # get as a dictionary the locally imported modules for defining the content of "cameras" module
# Below the automatic exploring of the imported modules and Associated names. Class definition should contain "Camera" in a class name
cameras_cls_names = [camera_class for camera_class in local_modules.keys() if "Camera" in camera_class]
# Collect actual classes for using them below on UI
cameras_ctrl_classes = [local_modules[camera_name] for camera_name in cameras_cls_names]
cameras_ctrl_types = [ctrl_class.camera_type() for ctrl_class in cameras_ctrl_classes]
cameras_settings = [ctrl_class.camera_settings(ctrl_class) for ctrl_class in cameras_ctrl_classes]


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
        self.fps = 0  # will automatically measure and correct FPS, used for recording by relying on cv2.VideoWriter methods
        self.images2record = None  # placeholder for queue with images for recording
        self.video_file_path = None  # placeholder for a video file path used for recording
        self.n_images_fps_buffer = 10; self.ring_fps_buffer = np.zeros((self.n_images_fps_buffer, )); self.index_fps_buffer = 0
        # Checking input parameters
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
            self.camera_settings = cameras_settings[self.supported_cameras.index(self.camera_type)]
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
                # Dev Note about putting time.sleep() below - if the scripts launched in Python debugger by Visual Studio Code
                if self.camera_initialized:
                    self.data_queue.put_nowait("Opened"); time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
                else:
                    report = self.camera_ref.initialization_status()
                    self.data_queue.put_nowait("Camera NOT Opened. Problem report:\n" + report)
                    time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
            else:
                self.initialized = False; self.data_queue.put_nowait("Camera not supported"); self.trigger_data.set()

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
                        if command == "Snap" or command == "Snap Image":
                            t1 = time.perf_counter()  # will be used for counting FPS
                            image = self.camera_ref.snap_image()  # calling the implemented method from an abstract class
                            passed_s = round((time.perf_counter() - t1), 9)
                            if self.fps == 0:
                                self.fps = int(round(1.0/passed_s, 0))  # first estimation of FPS
                                self.index_fps_buffer = 0  # set to the default value
                                self.ring_fps_buffer[self.index_fps_buffer] = self.fps; self.index_fps_buffer += 1
                            if self.record_flag:
                                timestamp_str = datetime.fromtimestamp(time.time()).strftime('%H:%M:%S.%f')[:-3]
                                if not self.images2record.full():
                                    self.images2record.put_nowait((image, timestamp_str))  # put numpy array and timestamp str for record
                            else:
                                # below - averaging ... stored measured FPS for more stable estimation of it
                                fps = int(round(1.0/passed_s, 0))  # FPS calculation for averaging
                                if self.index_fps_buffer < len(self.ring_fps_buffer) - 1:
                                    self.ring_fps_buffer[self.index_fps_buffer] = fps; self.index_fps_buffer += 1
                                elif self.index_fps_buffer == len(self.ring_fps_buffer) - 1:
                                    self.ring_fps_buffer[self.index_fps_buffer] = fps
                                    self.fps = int(round(np.mean(self.ring_fps_buffer))); self.index_fps_buffer = 0
                            if image is not None:
                                self.data_queue.put_nowait(image)
                            else:
                                self.data_queue.put_nowait("String placeholder Image")
                            self.trigger_data.set()  # set the trigger that the data is available for the calling main module
                        elif command == "Start Recording":
                            self.record_flag = True; self.images2record = thQueue(maxsize=20)
                            self.record_thread = Thread(target=self.record); self.record_thread.start()
                            print("Start recording", flush=True)
                        elif command == "Stop Recording":
                            self.record_flag = False; time.sleep(2.5*self.sleep_time_actions_ms)
                            if self.record_thread.is_alive():
                                self.record_thread.join(timeout=0.2)
                            self.images2record = clean_mp_queue(self.images2record); del self.images2record; self.images2record = None
                            print("Stop recording", flush=True)
                        elif command == "Get FPS":
                            self.data_queue.put_nowait(self.fps); self.trigger_data.set()  # set a trigger - some data is available for read
                        elif command == "Open Settings":
                            self.camera_ref.access_camera_settings(); self.fps = 0  # call native method for applying camera settings (OpenCV)
                        elif command == "Stop" or command == "Quit":
                            self.close()  # close the camera wrapper
                            self.initialized = False; self.fps = 0  # set the flag for the loop to stop it
                            self.data_queue.put_nowait("Stopped"); time.sleep(self.sleep_time_actions_ms); self.trigger_data.set()
                        elif command == "Get Updated Settings":
                            self.data_queue.put_nowait(self.camera_ref.available_camera_settings); self.trigger_data.set()
                        else:
                            print("Camera NOT RECOGNIZED the command:", command, flush=True)
                    # Commands with parameters
                    elif isinstance(command, tuple):
                        (command_str, parameters) = command  # unpacking tuple
                        if command_str == "Set Exposure Time":
                            if callable(getattr(self.camera_ref, "set_exposure_time", None)):
                                try:
                                    self.camera_ref.set_exposure_time(parameters); self.fps = 0
                                except Exception as e:
                                    exception_metadata = (type(e).__name__, str(e), traceback.format_exc())
                                    print("Encountered Exception:", exception_metadata, flush=True)
                                self.trigger_data.set()
                        else:
                            print("Camera NOT RECOGNIZED the command:", command, flush=True)
                    # Some reporting of not recognized commands
                    else:
                        print("Camera NOT RECOGNIZED the command:", command, flush=True)
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
                image, timestamp_str = self.images2record.get_nowait()
                pil_img = Image.fromarray(image)  # conversion numpy array to PIL image
                draw_handle = ImageDraw.Draw(pil_img)  # draw handle for put text
                font = ImageFont.truetype(font='arial.ttf', size=22)  # embedded fonts
                position = (25, 25)  # (x, y) position of writing
                draw_handle.text(position, timestamp_str, fill=0, font=font)  # Add black text to a gray image
                image2record = np.array(pil_img)  # conversion PIL image to np.ndarray
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
                    self.video_writer = cv2.VideoWriter(self.video_file_path, self.cv2_codec, self.fps, (w, h))
                    self.video_writer.write(image2record); first_step = False
                else:
                    if self.gray_scaled_img:
                        image2record = cv2.cvtColor(image2record, cv2.COLOR_GRAY2BGR)  # conversion from grayscale image to BGR format
                    image2record = cv2.cvtColor(image2record, cv2.COLOR_RGB2BGR)  # required back conversion for pyopencv
                    self.video_writer.write(image2record)  # write a frame
            else:
                time.sleep(self.sleep_time_actions_ms)
        if not self.record_flag:
            self.video_writer.release()  # close a file
            self.video_file_path = None; print("Stop recording Thread", flush=True)

    # %% Utility methods
    def close(self):
        """
        Close connection to the camera.

        Returns
        -------
        None.

        """
        self.camera_ref.close()  # closing logic should be implemented by the camera
