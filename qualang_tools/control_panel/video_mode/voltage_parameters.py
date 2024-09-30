import time
import logging


__all__ = ["VoltageParameter"]


# VoltageParameter Class remains unchanged
class VoltageParameter:
    def __init__(self, name, initial_value=0.0, units="V"):
        self.name = name
        self.latest_value = initial_value
        self._value = initial_value
        self.units = units
        logging.debug(f"{self.name} initialized with value {self.latest_value} {self.units}")

    def get(self):
        time.sleep(0.2)  # Simulate a 200ms delay
        self.latest_value = self._value
        logging.debug(f"Getting {self.name}: {self.latest_value} {self.units}")
        return self.latest_value

    def set(self, new_value):
        self._value = new_value
        updated_value = self.get()  # Return the value after setting
        logging.debug(f"Setting {self.name} to {new_value}: Actual value is {updated_value} {self.units}")
        return updated_value