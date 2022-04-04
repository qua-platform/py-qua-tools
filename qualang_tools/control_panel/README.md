# Control Panel

This package includes tools for directly controlling the OPX.
It currently has the following modules:

* [ManualOutputControl](README_manual_output_control.md) - This module allows controlling the outputs from the OPX in CW mode. Once created, it has an API for defining which channels are on. Analog channels also have an API for defining their amplitude and frequency.
* [VNA](README_vna.md) - This module allows to configure the OPX as a VNA for a given element (readout resonator for instance) and operation (readout pulse for instance) already defined in the configuration. Once created, it has an API for defining which measurements are to be run depending on the down-conversion solution used (ED: envelope detector, IR: image rejection mixer, IQ: IQ mixer).
