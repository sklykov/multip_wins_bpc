# -*- coding: utf-8 -*-
"""
Class storing values associated with tkinter Spinbox for providing better access to them.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""
# %% Imports
from tkinter.ttk import Spinbox
from tkinter import TclError, DoubleVar, IntVar


# %% Class def.
class SpinboxWrapper():
    """Wrapper for tkinter.ttk.Spinbox button with validation method."""

    def __init__(self, spinbox_button: Spinbox, associated_value, min_value, max_value, n_digit_points: int = 3):
        self.spinbox = spinbox_button; self.associated_value = associated_value
        self.min_value = min_value; self.max_value = max_value; self.n_digit_points = n_digit_points
        # Define associate type of input for explicit conversion of value
        if isinstance(self.associated_value, DoubleVar):
            self.value_type = 'float'
            self.value = float(self.associated_value.get())  # initial assigned value
        elif isinstance(self.associated_value, IntVar):
            self.value_type = 'int'
            self.value = int(self.associated_value.get())  # initial assigned value
        else:
            raise ValueError("Provided associated_value isn't instance of tkinter DoubleVar or IntVar")

    def extract_value(self):
        """
        Read and verify type of provided in the Spinbox.

        Returns
        -------
        provided_value : int or rounded float
            Extracted value from the text variable associated with Spinbox.

        """
        try:
            provided_value = self.associated_value.get()
            if self.value_type == 'float':
                provided_value = round(float(provided_value), self.n_digit_points)
            else:
                provided_value = int(provided_value)
        except TclError:
            self.associated_value.set(self.value)
            provided_value = self.value
        return provided_value

    def validate_input(self) -> bool:
        """
        Validate Spinbox input.

        Returns
        -------
        bool
            True if the value lays in valid range or provided with as the float or int number.

        """
        extracted_value = self.extract_value(); value_renewed = False; value_is_valid = False
        # Define if the value provided in numerical form and it's the different from the stored one
        if self.value_type == 'float':
            epsilon = 10**(-(self.n_digit_points + 3))
            if abs(self.value - extracted_value) > epsilon:
                value_renewed = True
        else:
            if self.value != extracted_value:
                value_renewed = True
        if value_renewed:
            if extracted_value < self.min_value or extracted_value > self.max_value:
                self.associated_value.set(self.value)
            else:
                self.value = extracted_value  # update stored value
                self.associated_value.set(extracted_value); value_is_valid = True
        return value_is_valid
