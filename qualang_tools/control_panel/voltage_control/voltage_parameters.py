from typing import Any, Optional
import pyvisa as visa

import logging


# VoltageParameter Class remains unchanged
class Parameter:
    def __init__(self, name, label=None, initial_value=0.0, units="V"):
        self.name = name
        self.label = label
        self.latest_value = initial_value
        self._value = initial_value
        self.units = units
        # logging.debug(f"{self.name} initialized with value {self.latest_value} {self.units}")

    def get(self):
        # time.sleep(0.2)  # Simulate a 200ms delay
        self.latest_value = self._value
        # logging.debug(f"Getting {self.name}: {self.latest_value} {self.units}")
        return self.latest_value

    def set(self, new_value):
        self._value = new_value
        updated_value = self.get()  # Return the value after setting
        # logging.debug(f"Setting {self.name} to {new_value}: Actual value is {updated_value} {self.units}")
        return updated_value

    def get_latest(self):
        return self.latest_value


# QDAC2 instrument class
class QDACII:
    def __init__(
        self,
        communication_type: str,
        IP_address: str = None,
        port: int = 5025,
        USB_device: int = None,
        lib: str = "@py",
    ):
        """
        Open the communication to a QDAC2 instrument with python. The communication can be enabled via either Ethernet or USB.

        :param communication_type: Can be either "Ethernet" or "USB".
        :param IP_address: IP address of the instrument - required only for Ethernet communication.
        :param port: port of the instrument, 5025 by default - required only for Ethernet communication.
        :param USB_device: identification number of the device - required only for USB communication.
        :param lib: use '@py' to use pyvisa-py backend (default).
        """
        self.communication_type = communication_type
        rm = visa.ResourceManager(lib)  # To use pyvisa-py backend, use argument '@py'
        if communication_type.lower() == "ethernet":
            self._visa = rm.open_resource(f"TCPIP::{IP_address}::{port}::SOCKET")
            # self._visa.baud_rate = 921600
            # self._visa.send_end = False
        elif communication_type.lower() == "usb":
            self._visa = rm.open_resource(f"ASRL{USB_device}::INSTR")
        elif communication_type.lower() == "dummy":
            print("Dummy QDACII connected!")
        else:
            raise ValueError(f"Invalid communication type: {communication_type}")

        if communication_type != "dummy":
            self._visa.write_termination = "\n"
            self._visa.read_termination = "\n"
            print(self._visa.query("*IDN?"))
            print(self._visa.query("syst:err:all?"))

    def query(self, cmd):
        return self._visa.query(cmd)

    def write(self, cmd):
        self._visa.write(cmd)

    def write_binary_values(self, cmd, values):
        self._visa.write_binary_values(cmd, values)

    def __exit__(self):
        self.close()


class qdac_ch(Parameter):
    def __init__(self, QDAC: QDACII, channel_number, name, label=None, initial_value=0.0, units="V"):
        super().__init__(name, label, initial_value, units)
        self.qdac = QDAC
        self.ch_nb = channel_number

    def get(self):
        # print(f"QUERY: sour{self.ch_nb}:volt ?")
        # self.latest_value = 0.01
        self.latest_value = float(self.qdac.query(f"sour{self.ch_nb}:volt?"))
        logging.debug(f"Getting {self.name}: {self.latest_value} {self.units}")
        return self.latest_value

    def set(self, new_value):
        self.qdac.write(f"sour{self.ch_nb}:volt {new_value}")
        # print(f"WRITE: sour{self.ch_nb}:volt {new_value}")
        updated_value = self.get()  # Return the value after setting
        logging.debug(f"Setting {self.name} to {new_value}: Actual value is {updated_value} {self.units}")

        return updated_value

    def __call__(self, *args: Any, **kwargs: Any) -> Optional[float]:
        if len(args) == 0 and len(kwargs) == 0:
            return self.get()
        else:
            self.set(*args, **kwargs)
