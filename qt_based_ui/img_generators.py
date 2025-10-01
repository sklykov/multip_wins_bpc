# coding=utf-8
"""
Store noisy image generators in a module.

@author: sklykov

@license: GPL v3 (as it is enforced by the license of PyQt5).

"""
# %% Global imports
from threading import Thread
import numpy as np
import time

# %% Local imports
from generate_noise_pic import generate_noise_picture

# Global variable - straight way of synchronizing of button clicked on the GUI with the independent thread process
global flag_generation


# %% Class wrapper for threaded noisy single picture generation
class SingleImageGenerator(Thread):
    """Threaded class for generation of single noisy image."""

    height = 100; width = 100; image = np.zeros((height, width), dtype='uint8')

    def __init__(self, height: int = 100, width: int = 100):
        Thread.__init__(self); self.height = height; self.width = width

    def run(self):
        """
        Generate of single image and storing it inside the class variable.

        Returns
        -------
        None.

        """
        self.image = generate_noise_picture(self.width, self.height)  # Width and height order re-defined in the subfunction as well


# %% Class wrapper for threaded noisy continuous pictures generation for checking the performance of Python representation
class ContinuousImageGenerator(Thread):
    """Threaded class for generation of continuous stream of noisy images and updating the ImageView widget."""

    meanGenTimes = np.zeros(200, dtype="uint")

    def __init__(self, image_widget, refresh_delay_ms: int = 100, height: int = 100, width: int = 100, test_performance_flag: bool = False):
        Thread.__init__(self); self.height = height; self.width = width; self.test_performance_flag = test_performance_flag
        self.image_widget = image_widget; self.refresh_delay_ms = refresh_delay_ms

    def run(self):
        """
        Make continuous generation of noisy pictures and updating the ImageView widget from pyqtgraph for their showing.

        Returns
        -------
        None.

        """
        i = 0  # for adding the elements into pre-initialized array for further mean generation time calculation
        while flag_generation:
            t1 = time.time()
            if self.test_performance_flag:
                # Below - the workaround for preventing kernel dying during continuous generation without any delays
                if self.refresh_delay_ms == 0:  # if the delay between frames is 0, then the generation is unstable
                    self.refresh_delay_ms += 1  # make the delay at least 1 ms
            image = generate_noise_picture(self.width, self.height)  # Get the noisy picture, width and height swapped
            self.image_widget.setImage(image)  # Set the image for representation by passed ImageView pyqtgraph widget
            time.sleep(self.refresh_delay_ms/1000)  # Applying artificial delays between each image generation
            # If testing of Performance requested, then accumulating of passed times in the array performed
            if self.test_performance_flag:
                t2 = time.time()
                if i < np.size(self.meanGenTimes):
                    self.meanGenTimes[i] = np.uint(np.round((t2-t1)*1000)); i += 1  # Add the passed time to the array
        # If generation stopped and the test of performance was asked, then print out the mean generation time
        if self.test_performance_flag:
            # Calculation of the final element that in the array is zero (passed time not saved)
            j = 0
            for j in range(np.size(self.meanGenTimes)):
                if self.meanGenTimes[j] == 0:
                    break
            self.meanGenTimes = self.meanGenTimes[0:j]  # Truncate array till the non-zerp element for mean value calculation
            mean_gen_t = np.uint(np.round(np.mean(self.meanGenTimes)))
            print("Mean generation time is:", mean_gen_t, "ms")
