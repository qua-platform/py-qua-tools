# QCoDeS drivers usage example

__Package__: https://github.com/qua-platform/py-qua-tools/tree/main/qualang_tools/external_frameworks/qcodes

This package contains drivers to set the OPX as a QCoDeS instrument and synchronize external parameter sweeps with 
sequences running on the OPX using the QCoDeS do"nd" methods. 
Since the OPX runs on a unique pulse processor, it can perform complex sequences that QCoDeS do not natively support. 
For example, acquire data with different formats and sweep parameters on his own.
To more fully support the OPX capabilities, this driver is more complex compared to other QCoDeS instruments' drivers.

In this example folder, you will find two folders containing:
* [basic-driver](basic-driver): demonstrating how to use the basic QCoDeS driver for the OPX.
  * [hello_qcodes.py](basic-driver/hello_qcodes.py): the example file showing the basic driver usage.
* [advanced-driver](advanced-driver): showing how to modify the basic driver QCoDeS driver.
  * [advanced_driver.py](advanced-driver/advanced_drivers.py): the modified driver.
  * [hello_qcodes_advanced.py](advanced-driver/hello_qcodes_advanced.py): the example file showing the advanced driver usage.
