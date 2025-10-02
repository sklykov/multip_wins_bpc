# -*- coding: utf-8 -*-
"""
Generate noisy image on the QThread.

@author: sklykov

@license: GPL v3 (as it is enforced by the license of PyQt5).

"""
# %% Imports
import numpy as np
from qtpy.QtCore import QThread, Signal, QMutex, QWaitCondition

# Local import resolving if this module imported by the main one
if __name__ == '__main__':
    from generate_noise_pic import generate_noise_picture
else:
    from .generate_noise_pic import generate_noise_picture


# %% Class def.
class ImagingThread(QThread):
    # comment below is for preventing wrong inspection results for Signal
    # noinspection PyArgumentList
    acquired_image = Signal(np.ndarray)  # actual image shared as Signal, should be the class attribute, not instance one

    def __init__(self, parent_object, img_h: int, img_w: int):
        super().__init__(parent=parent_object)  # provide parent for auto managing by PyQt, can be QMainWindow
        self._mutex = QMutex()  # for locking / unlocking changing of the same variable (prevent *lost wake-up problem)
        # *lost wake-up problem: this class could potentially make _paused == False and calls wake...() but lost it this notification
        self._wait_condition = QWaitCondition()  # it hasn't internal lock for checking
        self._paused = True; self._running = True; self.pause_ms = 100
        self.img_h, self.img_w = img_h, img_w

    def run(self):
        """
        Specify the thread task (loop).

        Returns
        -------
        None.
        """
        while self._running:
            self._mutex.lock()  # locking any changing of variables to this worker (if other thread call resume or pause simultaneously)
            if self._paused:
                self._wait_condition.wait(self._mutex)  # release lock on mutex and goes to sleep automatically
            self._mutex.unlock()  # when it's running continuously, it allows main Thread to call pause / stop methods and set flags

            # Acquiring an image
            img = generate_noise_picture(height=self.img_h, width=self.img_w)
            self.acquired_image.emit(img)  # will send the generated data to the specified handler method
            # The binding of the Signal and handling method done in the calling class (SimUscope) by Signal.connect(self.method)

            # Some pause (instead of exposure time - for Simulation of image acquisition)
            self.msleep(self.pause_ms)

    def resume_work(self):
        """
        Resume paused by QWaitCondition().wait(QMutex) execution of a loop.

        Returns
        -------
        None.

        """
        self._mutex.lock()  # guarantee to change _paused variable only by this method
        self._paused = False
        self._wait_condition.wakeOne()   # wake up sleeping method (self._wait_condition.wait(self._mutex))
        self._mutex.unlock()  # release lock

    def pause_work(self):
        """
        Pause the main run loop by setting thread-safely the flag.

        Returns
        -------
        None.

        """
        self._mutex.lock()  # guarantee to change _paused variable only by this method
        self._paused = True
        self._mutex.unlock()  # release lock

    def set_pause_ms(self, pause_ms: int):
        """
        Set pause before image acquiring (generation).

        Parameters
        ----------
        pause_ms: int
            Pause in ms.

        Returns
        -------
        None
        """
        self._mutex.lock()
        if pause_ms > 0:
            self.pause_ms = pause_ms
        self._mutex.unlock()  # release lock

    def stop(self):
        """
        Stop main loop execution by setting thread-safely the flag.

        Returns
        -------
        None.

        """
        self._mutex.lock()
        self._running = False  # set flag to stop run
        self._wait_condition.wakeOne()  # if loop waits for a notification
        self._mutex.unlock()
        self.wait()  # equivalent of thread.join() call - blocks main UI thread
