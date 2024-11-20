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


# %% Camera class
class CameraWrapper(Process):
    """Class for wrapping camera controlling functions in the additional Process() instance."""

    # Dev. note: it's not necessary to make the variables below private explicitly, since they are embedded to the Process
    initialized: bool = False  # flag - initialized or not the camera
    camera_ref = None  # handle to the camera (API specific)
    camera_type: str = "Simulated"  # provided by the calling program
    live_stream_flag: bool = False; commands_queue: Queue; trigger_commands: Event
    data_queue: Queue; trigger_data: Event; lifo_queues = None
    data_triggered_queues = None; queues_triggers = None

    def __init__(self, commands2camera: Queue, trigger_commands: Event, data_camera: Queue, trigger_data_camera: Queue,
                 data_triggered_queues: Sequence[Queue] = None, queues_triggers: Sequence[Event] = None, lifo_queues: Sequence[Queue] = None):
        Process.__init__(self)  # Initialize this class on the separate process with its own memory and core
        self.commands_queue = commands2camera; self.trigger_commands = trigger_commands
        self.data_queue = data_camera; self.trigger_data = trigger_data_camera
        self.script_path = Path(__file__).parent.absolute()  # for possible access the API python wrappers
        if data_triggered_queues is not None and queues_triggers is not None:
            if len(data_triggered_queues) > 0 and len(queues_triggers) > 0 and len(data_triggered_queues) == len(queues_triggers):
                self.data_triggered_queues = data_triggered_queues; self.queues_triggers = queues_triggers
        if lifo_queues is not None:
            if len(lifo_queues) > 0:
                self.lifo_queues = lifo_queues
