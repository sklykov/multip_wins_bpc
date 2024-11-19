# -*- coding: utf-8 -*-
"""
Utility functions.

@author: sklykov, @license: MIT license

"""
# %% Global imports
from multiprocessing import Queue
from queue import Empty
import time


# %% Functions
def clean_mp_queue(queue: Queue) -> Queue:
    """
    Remove the stored in the Queue remained messages / data.

    Parameters
    ----------
    queue : Queue
        Instance of Queue class from the multiprocessing module.

    Returns
    -------
    Queue
        Cleaned up Queue.

    """
    if queue is not None:
        while not queue.empty():
            try:
                queue.get_nowait(); time.sleep(0.002)
            except Empty:
                break
    return queue
