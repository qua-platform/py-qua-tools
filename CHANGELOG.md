# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]
### Fixed
- octave_tools - Fix bug when setting calibrate to False in ``get_correction_for_each_LO_and_IF()``.

### Added
- octave_tools - Added the possibility to pass the AutoCalibrationParams to ``get_correction_for_each_LO_and_IF()`` to customize the calibration parameters (IF_amplitude for instance).

## [0.17.4] - 2024-05-07
### Fixed
- control_panel - Fix init of ManualOutputControl (remove old logger call).

## [0.17.3] - 2024-05-06
### Fixed
- digital_filters - added `multi_exponential_decay` to `__init__` file.

## [0.17.2] - 2024-05-06
### Added
- digital_filters - added `multi_exponential_decay` function which can be used to fit and extract the exponential decay coefficients when there are multiple time constants. It supports any number of exponential decays.

### Changed
- digital_filters - `exponential_decay` function now internally uses the `multi_exponential_decay` function for calculation. The user-facing interface of `exponential_decay` remains unchanged, ensuring backward compatibility.
- digital_filters - `multi_exponential_decay` function has the following formula: `s * (1 + a1 * np.exp(-x / t1) + a2 * np.exp(-x / t2) + ... + an * np.exp(-x / tn))`, where `s=1` by default.

## [0.17.1] - 2024-04-19
### Fixed
- results/DataHandler - Only load DataHandler XarrayDataProcessor if xarray can be imported
- results/DataHandler - Fix bug with the data folder path.
- bakery - Fix typo in the `baking` tool config lookup (`mwInput` -> `MWInput`)

## [0.17.0] - 2024-04-18
### Added
- Video_mode - New module to update some pre-defined parameters of a QUA program while fetching data from the OPX.
- simulator - ``create_simulator_controller_connections`` can now be used to create the connections between a subset of a large cluster.
- results - ``DataHandler`` can be used to save data (values, matplotlib figures, numpy/xarray arrays) to the local file storage.
- callable_from_qua - Framework used to call Python functions within the core of a QUA program.
- octave_tools - Added library of functions for manipulating the calibration database and updating the mixer correction parameters dynamically in Python or in QUA directly.
- digital_filters - Added library of functions allowing the derivation of the digital filter taps to correct distortions.
- macros - Added `long_wait` convenience macro to simplify waiting for longer than the maximum wait time.

### Changed
- bakery - Added the possibility to use the `mwInput` key to enable baking compatibility with MW-FEM dedicated element.
- config/waveform_tools - Added sampling rate argument with default value set to 1GS/s to the waveforms.
- simulator - ``create_simulator_controller_connections`` now creates the connections with a different algorithm that uses all available optical connections.
- simulator - ``create_simulator_controller_connections`` order of input parameters has changed.
- External_frameworks/qcodes - Fixed the unit of phase
- External_frameworks/qcodes - Added a flag to allow for the phase to remain wrapped 
- results - Add a warning when timeout is reached in ``wait_until_job_is_paused``.

### Deprecated
- simulator - ``qualang_tools.simulator_tools`` has been deprecated and was moved to ``qualang_tools.simulator``.

### Fixed
- loops - An error will be raised when the logarithmic step is too small (from_array & qua_logspace with integers).

## [0.16.0] - 2024-01-25
### Fixed
- ConfigBuilder - `Element` now correctly accepts default arguments.
- External_frameworks/qcodes - Fix bug with the setpoints when streaming the raw adc traces.
- bakery - add the `RF_inputs` key to be compatible with the Octave API from qm-qua>=1.1.5.

### Added
- External_frameworks/qcodes - Added ``update_readout_length()`` to update locally the readout length of a given readout element and operation.
- External_frameworks/qcodes - Added ``update_qm()`` to update the quantum machine (close and re-open it) in case the config has been updated. 
- External_frameworks/qcodes - Added ``live_plotting()`` to fetch and plot the OPX results while the program is running.
- Unit - Added `volts2dBm` and `dBm2volts`.

### Changed
- Eased package dependencies, requires python 3.8 or above
- Unit - `demod2volts` now has a `single_demod` flag to correctly convert the data from single demodulation.

## Deprecated
- ConfigBuilder and ConfigGUI are not being activity developed and may not have all config options


## [0.15.2] - 2023-09-06
### Added
- results - Add `wait_until_job_is_paused()` to block python console until the OPX sequence reaches a `pause()` statement.
- External_frameworks/qcodes - Added ``cluster_name`` as optional input parameter to connect to the OPX with QOP220 or above.

### Changed
- Units.unit - `units.unit.Hz` now rounds the result and casts it to an integer if the flag coerce_to_integer is set to True. Same for `kHz`, `MHz` and `GHz`.
- External_frameworks/qcodes - Added ``wait_until_job_is_paused()`` in the resume() command to ensure that resume will be called only after the program reached the pause() statement.

## [0.15.1] - 2023-06-07
### Changed
- Loosened requirements on `pandas`

### Added
- External_frameworks/qcodes - Add the possibility to input a scale factor to the get_measurement_parameter() function in order to convert the results from Volts to an arbitrary unit.

### Fixed
- External_frameworks/qcodes - Now it is possible to plot several results on the same graph with the inspectr tool.

## [0.15.0] - 2023-05-15
### Added
- External_frameworks - add qcodes drivers to set the OPX as a qcodes instrument.
- Examples - add examples to show how to integrate the OPX in your qcodes framework and customize the qcodes driver

## [0.14.0] - 2023-03-23
- Changed `qm-qua` requirements to be >=1.1.0

### Added
- Config.helper_tools - Added the function `transform_negative_delays()` to adjust a config containing negative delays by offsetting all delays by the most negative one.

### Fixed
- Fixed the loops library to support `qm-qua` 1.1.0  

## [0.13.2] - 2023-02-23
### Added
- Plot.fitting - add resonator frequency vs flux fitting function.
- Plot.plots - add the possibility to fit the data to be plotted for plot_demodulated_data_1D.
- addons.variables.assign_variables_to_element - A function to force variables assignment to specific elements.

### Changed
- Units.unit - `units.unit.ns` now returns `1/4` within an open `qm.qua.program` scope and `1` otherwise. Same for `us`, `ms`, `s`, and `clock_cycle`. By default results of `a * ns` operation are cast to `int` and a warning is generated if casting discards a nonzero remainder.

### Fixed
- simulator_tools.create_simulator_controller_connections - now deals with the case of 1 controller.

## [0.13.1] - 2022-11-18
- Fix init files.

## [0.13.0] - 2022-11-18
### Added
- Multi-user Tools - A subpackage that allows several users to work simultaneously.
- Config.helper_tools - This package includes tools for writing and updating the configuration.
- Plot.fitting - This tool enables the use to fit results from qua programs.
- Bakery - Added a flag to disable the addition of an `align` to the `run` function.

### Changed
- Plot.plots - Added functions to plot results from qua programs (`plot_demodulated_data 1D and 2D`, `get_simulated_samples_by_element` and `plot_simulator_output`)
- Bakery - Now uses the more efficient `frame_rotation_2pi` instead of `frame_rotation`.

### Fixed
- Bakery - Fixed cases in which a `frame_rotation_2pi(0.0)` was added.

## [0.12.0] - 2022-08-29
### Changed
- **Breaking change!** - Waveform tools - Added a missing 2$\pi$ factor into `detuning` parameter in `drag_gaussian_pulse_waveforms` and `drag_cosine_pulse_waveforms`. 
  This will produce different results compared to previous versions, to get the same results, divide the `detuning` parameter by 2pi. Both `detuning`, `delta`, and `anharmonicity` are now expected in`Hz` rather than `rad`; a 2$\pi$ multiplication occurs in the built-in function.
- Waveform tools - Renamed argument `delta` to `anharmonicity` in `drag_gaussian_pulse_waveforms` and `drag_cosine_pulse_waveforms`. 
  `delta` is still accepted but will be deprecated in future versions.
- ConfigBuilder - renamed arguments (backward compatible) in Element and MeasureElement classes.
- ConfigBuilder - renamed AnalogOutputPort attribute channel_weights to crosstalk

### Added
- ConfigBuilder - PiecewiseConstantIntegrationWeights class.
- ConfigBuilder - added thread and Oscillator to Element class.
- ConfigBuilder - added shareable field to all ports.
- ConfigBuilder - added doc strings

### Fixed
- ConfigBuilder - measure pulse type in the configuration
- ConfigBuilder - removed offset field in DigitalOutputPort
- ConfigBuilder - DigitalInputPort's port id
- ConfigBuilder - fixed len method of Parameter when a setter is used
- Fixed dependency to be compatible with qm-qua 0.4.0

## [0.11.2] - 2022-07-25
### Changed
- results - Improved `is_processing()` and add `get_start_time()` to fetching_tool.

## [0.11.1] - 2022-07-19
### Fixed
- Fixed internal package structure to support mkdocs.

## [0.11.0] - 2022-07-18
### Added
- Calibrations - a new package with an API to perform basic single qubit calibration protocols.
- Results.fetching_tool - Add the `.is_processing()` method.
### Fixed
- Loops - Fixed qua_logspace() and from_array() for logarithmic increments with integers.

## [0.10.0] - 2022-07-04
### Fixed
- ManualOutputControl - Fixed the `close` function
- Waveform tools - DRAG now handles alpha=0 correctly (Was not fixed in 0.9.0)
### Added
- Results - a new package with fetching tools and progress bar.
- Plot - a new package with plotting tool for interrupting live plotting.
- Loops - a new package with the qua_arange, qua_linspace, qua_logspace, from_array and get_equivalent_log_array tools for parametrizing QUA for_ loops.
- Units - a new package with an API to use units (MHz, us, mV...) and functions to convert data to other units (demodulated data to volts for instance).
- Waveform tools - Added various flattop waveforms and Blackman integral waveform
### Changed
- Added support for Python 3.10
- Lower Numpy requirement to 1.17.0


## [0.9.0] - 2022-05-24
### Fixed
- various issues were fixed in config builder
- Waveform tools - DRAG now handles alpha=0 correctly
### Added
- config builder MeasurePulse now accepts IntegrationWeights object as well
- config builder Element now accepts ControlPulse and MeasurePulse
- config builder Parameter class now support basic algebra (+, -, /, *, **)
- A new tool for discriminating two states in the IQ blob under `analysis.discriminator`
### Changed
- All config builder objects can be initialized with all the data (but still can be built step by step)
- config builder FluxTunableTransmon - parameter name changed from fl_port to flux_port
- config builder Coupler - parameter name changed from p to port
- config builder Element - renamed set_delay/buffer methods as set_digital_input_delay/buffer
- config builder ConfigVar is changed to ConfigVars
- config builder ConfigVars - parameter method now returns a Parameter object instead of lambda function
- config builder ConfigVars - parameter method optionally accepts a setter
- config builder Controller - does not accept number of outputs and inputs anymore
- config builder Mixer - added MixerData class (holds intermediate_frequency, lo_frequecy and correction matrix), we now support correction matrix for every pair of IF and LO frequencies
- Waveform tools - now return Numpy arrays


## [0.8.0] - 2022-04-04
### Added
- Interactive plotlib - Support for 2d plot, better data manipulation and better fits
- Waveform tools - Added the waveform tool package, currently including scripts for creating Gaussian and Cosine DRAG waveforms
- Control Panel - VNA Mode - This module allows to configure the OPX as a VNA for a given element (readout resonator for instance) and 
operation (readout pulse for instance) already defined in the configuration.

## [0.7.2] - 2022-03-15
### Fixed
- Set minimum version of docutils dependency to 0.14

## [0.7.1] - 2022-03-13
### Fixed
- Interactive Plotting Toolbox - Fixed several small issues when loading a figure
- Integration Weights Tool - When compressing and plotting integration weights, the correct label is shown. 
- Set minimum version of docutils dependency to 0.14
- Fix config builder GUI imports
### Added
- Interactive Plotting Toolbox - Added default markers when fitting 
- Interactive Plotting Toolbox - Improved example and added a demo video 
- readme for config builder GUI

## [0.7.0] - 2022-02-10
### Added
- Add experimental feature - [InteractivePlotLib](https://github.com/qua-platform/py-qua-tools/tree/main/qualang_tools/addons).
  This plotting library, built on Matplotlib, adds many new features to it.
### Fixed
- Integration weights tool - Fixed a bug which caused the integration weight tool to not work on lists

## [0.6.5] - 2022-01-26
### Changed
- ManualOutputControl - Digital outputs are now controlled by independent quantum machines, allowing switching them on and off without deadtime.

## [0.6.4] - 2022-01-25
### Fixed
- Bakery - Using "delete_samples()" did not update the element internal time tracking. 

## [0.6.3] - 2022-01-24
### Added
- ManualOutputControl - An option to open up the ManualOutputControl without a configuration file. Using ManualOutputControl.ports().
- ManualOutputControl - Added a readme file to explain how to use.
- ManualOutputControl - Added various validations and exceptions when illegal operations are performed
- ManualOutputControl - Added print_analog_status() and print_digital_status() to print the current status.
### Changed
- ManualOutputControl - analog_status() and digital_status() now return a dict containing the information.

## [0.6.2] - 2022-01-18
### Fixed
- Bakery Bug - [delete_samples() crash](https://github.com/qua-platform/py-qua-tools/issues/57)
- Bakery Bug - [Bakery Bug - using a negative wait can lead to infinite recursion](https://github.com/qua-platform/py-qua-tools/issues/56)
- ConfigBuilder Bug - renamed digital_inputs in Element to digitalInputs
- ConfigBuilder Bug - removed empty dictionary of outputPulseParameters when not initialized
- ConfigBuilder Bug - fixed the format of Mixers in the configuration

## [0.6.1] - 2022-01-13
### Changed
- API Changes to the "ManualOutputControl" class:
  - Constructor does not take "digital_on" elements.
  - Constructor accepts optional input of elements to include.
  - "set_amplitude" and "update_frequency" have been renamed to "set_amplitude" and "set_frequency".
  - "digital_on" and "digital_off" no longer change elements which are not given.
  - "digital_on" and "digital_off" can accept no input, which makes them turn on and off all channels.
  - New function, "turn_off_elements" which turns off both digital and analog of the given elements.

## [0.6.0] - 2022-01-11
### Changed
- The imports from the package, mainly when doing import *, has changed.
### Added
- Add a "Control Panel" - A user interface for controlling the outputs from the OPX in CW mode, based on the user's configuration.
- Added support for Elements with digital inputs/outputs (in the config builder tool).
### Fixed
- Fixed bakery bug - Negative wait for single input element was not working.
- Fixed bakery bug - Fixed the symmetric padding method when wait duration was even.
- Readme had voltage values in code examples that were not realistic.
- Fixed convention of input/output ports of Element in config builder.

## [0.5.0] - 2021-12-02
### Added
- Added a brand-new Config GUI which can be used to visually edit and modify QUA configurations.
- A readme has been added for the Config builder which guides you through basic usage (and more).

## [0.4.1] - 2021-12-15
### Fixed
- Fixed a bug in the compress_integration_weights functions -> consecutive values with the same difference were deleted.
### Added
- In addition, added a function to plot the integration weights.

## [0.4.0] - 2021-12-14
### Added
- Main new feature: Added a toolbox for building configuration files!
- Also added a tool for creating the inter-OPX connections for simulations.

## [0.3.3] - 2021-11-21
### Fixed
- Added back add_Op() with deprecation.
- Improved examples and docs.

## [0.3.2] - 2021-10-20
### Fixed
- Fix Ramsey example.

## [0.3.1] - 2021-10-20
### Changed
- Change play_at() behavior - play_at() will now use the latest frame & detuning.

## [0.3.0] - 2021-10-18
### Added
- Sampling rate is now tunable within the baking.
- Integration weights tool added.
- Possibility to delete samples in the baking.

## [0.2.2] - 2021-10-06
### Fixed
- Clarification in the documentation (readme.md) about the need to declare the Quantum Machine after the baking of all waveforms to ensure they are runnable within the QUA program.
- Removed Entropy dependency from XEB example.


## [0.2.1] - 2021-09-06
### Added
- Extended the method get_Op_length() which does not require a quantum element anymore, as the output of the method will be the longest baked waveform across all involved quantum elements if none is provided (specifically useful for the example of 2 qubit RB in qua-libs).
### Changed
- Updated docstrings describing the baking tool to make it more readable.
- Refined the method b.align() which was padding 0s to all elements in the config instead of only aligning elements already involved in the baking context manager when no argument was provided. This is now corrected.

## [0.2.0] - 2021-08-16
### Added
- Digital waveforms are now editable within the baking and can be attached to arbitrary baked waveforms (b.add_digital_waveform).
- Existing digital waveform can now be attached to a baked operation.
- The possibility to update the config or not is now induced directly by the providing of a baking index to adapt the length of the baked reference pulse (no update_config boolean in baking initialization required anymore).
- One can delete a baked Operation from the config using delete_baked_Op (which deletes both analog and digital baked waveforms associated to the baking object).

## [0.1.1] - 2021-08-02
### Fixed
- Fixed license metadata.

## [0.1.0] - 2021-08-02
### Added
- This release exposes the baking, RB and XEB functionality.

[Unreleased]: https://github.com/qua-platform/py-qua-tools/compare/v0.17.1...HEAD
[0.17.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.17.0...v0.17.1
[0.17.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.15.2...v0.16.0
[0.15.2]: https://github.com/qua-platform/py-qua-tools/compare/v0.15.1...v0.15.2
[0.15.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.15.0...v0.15.1
[0.15.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.13.2...v0.14.0
[0.13.2]: https://github.com/qua-platform/py-qua-tools/compare/v0.13.1...v0.13.2
[0.13.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.13.0...v0.13.1
[0.13.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.11.2...v0.12.0
[0.11.2]: https://github.com/qua-platform/py-qua-tools/compare/v0.11.1...v0.11.2
[0.11.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.7.2...v0.8.0
[0.7.2]: https://github.com/qua-platform/py-qua-tools/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.6.5...v0.7.0
[0.6.5]: https://github.com/qua-platform/py-qua-tools/compare/v0.6.4...v0.6.5
[0.6.4]: https://github.com/qua-platform/py-qua-tools/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/qua-platform/py-qua-tools/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/qua-platform/py-qua-tools/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/qua-platform/py-qua-tools/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/qua-platform/py-qua-tools/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/qua-platform/py-qua-tools/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/qua-platform/py-qua-tools/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/qua-platform/py-qua-tools/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/qua-platform/py-qua-tools/releases/tag/v0.1.0
