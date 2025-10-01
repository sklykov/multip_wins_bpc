# -*- coding: utf-8 -*-
"""
Simple GUI for representing of generated noisy image using PyQT.

@author: sklykov

@license: GPL v3 (as it is enforced by the license of PyQt5).

"""
# %% Global imports
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QGridLayout, QSpinBox, QCheckBox, QVBoxLayout
import numpy as np
import time
import pyqtgraph

# %% Local imports
from acq_img_worker import ImagingThread

# TODO points below
# 1) make model implementation of multithreaded application which generates images and updates main UI, remove standard Thread usage
# 2) pythonize code (remove camel case notation for variables, clean up the old code)


# %% Implementation of all windows inside the child class
class SimUscope(QMainWindow):
    """Create the GUI with buttons for testing the performance of image showing / updating."""

    __generation_flag: bool = False  # Private class variable for recording state of continuous generation
    __flagTestPerformance: bool = False  # Private class variable for switching between test state by using QCheckBox

    def __init__(self, img_height: int, img_width: int):
        """Create overall UI inside the QMainWindow widget."""
        super().__init__(None)  # None - default parameter for the parent variable (it's the main window)
        self.setWindowTitle("Display UI - Camera Image"); self.setGeometry(200, 200, 800, 700)
        wid = QWidget(self); self.setCentralWidget(wid)  # setting central widget
        self.update_img_task = QTimer(parent=self)   # update task for continuous imaging
        self.start_time = time.perf_counter()  # for recording time measurements for performance evaluation
        self.n_performance_counts = 0  # for counting number of timing measurements
        self.mean_acq_time_ms = 0  # for counting time required for estimating of continuous snaps stream
        self.update_img_on_display_task = QTimer(parent=self)
        self.current_img = np.zeros((img_height, img_width), dtype=np.uint8)  # storing current image

        # Central plot - Image display initialization
        self.img_height = img_height; self.img_width = img_width
        self.img = np.zeros((self.img_height, self.img_width), dtype='uint8')  # Black initial image
        self.plot = pyqtgraph.PlotItem(); self.plot.setXRange(0, self.img_width); self.plot.setYRange(0, self.img_height)
        self.image_widget = pyqtgraph.ImageView(view=self.plot)  # The main widget for image showing
        self.image_widget.ui.roiBtn.hide(); self.image_widget.ui.menuBtn.hide()   # Hide ROI, Norm buttons from the ImageView
        self.image_widget.setImage(self.img)  # Set image for representation in the ImageView widget

        # Buttons creation
        self.buttonGenSingleImg = QPushButton("Generate Single Pic"); self.buttonGenSingleImg.clicked.connect(self.generate_single_pic)
        self.buttonContinuousGen = QPushButton("Continuous Generation")  # Switches on/off continuous generation
        self.toggle_performance_test = QCheckBox("Test Performance"); self.toggle_performance_test.setEnabled(True)
        self.toggle_performance_test.setChecked(False)  # setChecked - set the state of a button
        self.buttonContinuousGen.clicked.connect(self.generate_continuous_pics); self.buttonContinuousGen.setCheckable(True)
        self.exp_time_ctrl = QSpinBox(self); self.exp_time_ctrl.setSingleStep(1); self.exp_time_ctrl.setSuffix(" ms")
        self.exp_time_ctrl.setPrefix("Exposure time: "); self.exp_time_ctrl.setMinimum(1); self.exp_time_ctrl.setMaximum(1000)
        self.exp_time_ctrl.setValue(100); self.exp_time_ctrl.adjustSize()
        self.quitButton = QPushButton("Quit"); self.quitButton.setStyleSheet("color: red")

        # Grid layout below - the main layout pattern for all buttons and windows on the Main Window
        grid = QGridLayout(); wid.setLayout(grid)  # Grid layout created independently of the
        grid.addWidget(self.buttonGenSingleImg, 0, 0, 1, 1); grid.addWidget(self.buttonContinuousGen, 0, 1, 1, 1)
        grid.addWidget(self.toggle_performance_test, 0, 2, 1, 1); grid.addWidget(self.exp_time_ctrl, 0, 3, 1, 1)
        grid.addWidget(self.quitButton, 0, 5, 1, 1)
        vbox = QVBoxLayout()  # create independent layout as container for Height / Width Spinboxes and add it to the grid later
        self.width_ctrl = QSpinBox(self); self.height_ctrl = QSpinBox(self); vbox.addWidget(self.width_ctrl)
        self.height_ctrl.setPrefix("Height: "); self.width_ctrl.setPrefix("Width: "); vbox.addWidget(self.height_ctrl)
        grid.addLayout(vbox, 0, 4, 1, 1); self.width_ctrl.setSingleStep(2); self.height_ctrl.setSingleStep(2)
        self.width_ctrl.setMinimum(50); self.height_ctrl.setMinimum(50)
        self.width_ctrl.setMaximum(3000); self.height_ctrl.setMaximum(3000)
        self.width_ctrl.setValue(self.img_width); self.height_ctrl.setValue(self.img_height)
        self.width_ctrl.adjustSize(); self.height_ctrl.adjustSize()
        # image_widget should be central - for better representation of generated images
        grid.addWidget(self.image_widget, 1, 0, 5, 6)  # the ImageView widget spans on ... rows and ... columns (2 values in the end)

        # Set valueChanged event handlers for buttons
        self.width_ctrl.valueChanged.connect(self.image_sizes_changed); self.height_ctrl.valueChanged.connect(self.image_sizes_changed)
        self.quitButton.clicked.connect(self.quit_clicked); self.exp_time_ctrl.valueChanged.connect(self.change_exp_time)

        # Reimplementation of logic for getting images from pure Thread
        self.img_acq_thr = ImagingThread(self, img_height, img_width); self.img_acq_thr.start()
        self.img_acq_thr.acquired_image.connect(self.get_updated_image)

    def generate_single_pic(self):
        """
        Handle clicking of Generate Single Picture. This method updates the image associated with ImageView widget.

        Returns
        -------
        None.

        """
        self.img_acq_thr.resume_work()  # proceed in the main loop of image acquisition worker to single image acquisition

    def get_updated_image(self, img: np.ndarray):
        """
        Receive updated signal containing an image.

        Parameters
        ----------
        img: np.ndarray
            Image sent by the emit() method of a pyqtSignal which wraps image generation.

        Returns
        -------
        None.

        """
        # self.image_widget.setImage(img)   # update displayed image - direct updating task
        self.current_img = img.copy()   # store current image received from the acquisition thread
        self.update_img_on_display_task.singleShot(1, self.update_displayed_image)  # async request updating of displayed image
        self.img_acq_thr.pause_work()  # pause the internal loop for the next execution (acquisition)
        if self.__generation_flag:
            if self.toggle_performance_test.isChecked():
                # Calculate mean acquisition time
                if self.n_performance_counts == 0:
                    self.mean_acq_time_ms = int(np.round((time.perf_counter() - self.start_time)*1000))
                else:
                    self.mean_acq_time_ms += int(np.round((time.perf_counter() - self.start_time)*1000))
                    self.mean_acq_time_ms = int(round(0.5*self.mean_acq_time_ms, 0))
                # Printing out simple report on the performance
                if self.n_performance_counts != 0 and self.n_performance_counts % 10 == 0 and self.exp_time_ctrl.value() > 59:
                    print("Mean acquisition time [ms]:", self.mean_acq_time_ms, flush=True)
                elif (self.n_performance_counts != 0 and self.n_performance_counts % 20 == 0
                      and 25 <= self.exp_time_ctrl.value() <= 59):
                    print("Mean acquisition time [ms]:", self.mean_acq_time_ms, flush=True)
                elif (self.n_performance_counts != 0 and self.n_performance_counts % 40 == 0
                      and self.exp_time_ctrl.value() < 25):
                    print("Mean acquisition time [ms]:", self.mean_acq_time_ms, flush=True)
                if self.n_performance_counts > 50E6:  # prevent unnecessary huge counts number
                    self.n_performance_counts = 1
                self.n_performance_counts += 1; self.start_time = time.perf_counter()
            self.update_img_task.singleShot(1, self.generate_single_pic)  # assign single update task (snaps stream)

    def generate_continuous_pics(self):
        """
        Handle clicking of Continuous Generation button. Generates continuously and updates the ImageView widget.

        Returns
        -------
        None.

        """
        self.__generation_flag = not self.__generation_flag  # changing the state of generation
        self.buttonContinuousGen.setDown(self.__generation_flag)  # changing the visible state of button (clicked or not)
        # Generation works as emulating single snap acquisition and representation
        if self.__generation_flag:
            self.toggle_performance_test.setDisabled(True)  # Disable the checkbox for preventing test on during continuous generation
            self.exp_time_ctrl.setDisabled(True)  # Disable the exposure time control
            self.width_ctrl.setDisabled(True); self.height_ctrl.setDisabled(True)
            if self.toggle_performance_test.isChecked():
                self.start_time = time.perf_counter(); self.n_performance_counts = 0
            self.update_img_task.singleShot(1, self.generate_single_pic)   # assign single update task (snaps stream)
        else:
            time.sleep((self.exp_time_ctrl.value()*2)/1000)
            self.toggle_performance_test.setEnabled(True); self.exp_time_ctrl.setEnabled(True)
            self.width_ctrl.setEnabled(True); self.height_ctrl.setEnabled(True);  self.n_performance_counts = 0

    def change_exp_time(self):
        """
        Handle changing of exposure time button.

        Returns
        -------
        None.
        """
        if not self.__generation_flag:
            self.img_acq_thr.set_pause_ms(self.exp_time_ctrl.value())

    def update_displayed_image(self):
        """
        Wrap updating of a displayed image task in the class method for calling it as singleShot() method of QTimer.

        Returns
        -------
        None.

        """
        self.image_widget.setImage(self.current_img)

    # noinspection PyMethodOverriding
    def closeEvent(self, qt_event: QCloseEvent):
        """
        Rewrites the default behaviour of clicking on the X button on the main window GUI.

        Parameters
        ----------
        qt_event : QWidget Close Event (QCloseEvent)
            Needed by the API.

        Returns
        -------
        None.

        """
        if self.__generation_flag:
            self.__generation_flag = False  # For notifying of Generation Thread to stop generation
            self.img_acq_thr.stop()
            time.sleep((self.exp_time_ctrl.value()*2)/1000)  # Delay for waiting the Generation Thread ended
            qt_event.accept()  # Maybe redundant, but this is explicit accepting quit event

    def quit_clicked(self):
        """
        Handle the clicking event on the Quit Button.

        Sets the global variables to False state. Waits for threads stop running. Quits the Main window.

        Returns
        -------
        None.

        """
        if self.__generation_flag:
            self.__generation_flag = False  # For notifying of Generation Thread to stop generation
            time.sleep((self.exp_time_ctrl.value()*2)/1000)  # Artificial delay for waiting the Generation Thread ended
        self.close()  # Calls the closing event for QMainWindow

    def image_sizes_changed(self):
        """
        Handle changing of image width or height. Allows to pick up values for single image generation and continuous one.

        Returns
        -------
        None.

        """
        self.img_width = self.width_ctrl.value(); self.img_height = self.height_ctrl.value()
        self.img_acq_thr.stop(); del self.img_acq_thr  # clean up previous instance of an image generator
        self.img_acq_thr = ImagingThread(self, self.img_height, self.img_width); self.img_acq_thr.start()
        self.img_acq_thr.acquired_image.connect(self.get_updated_image)


# %% Tests
if __name__ == "__main__":
    width_default = 1000; height_default = 1000  # Default width and height for generation of images
    my_app = QApplication([])  # application without any command-line arguments
    my_app.setQuitOnLastWindowClosed(True)  # workaround for forcing the quit of the application window for returning to the kernel
    main_window = SimUscope(width_default, height_default); main_window.show()
    my_app.exec()  # Exit of the main program
