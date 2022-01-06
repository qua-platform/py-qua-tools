# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]
### Changed
- The imports from the package, mainly when doing import *, has changed.
### Added
- Add a "Control Panel" - A user interface for controlling the outputs from the OPX in CW mode, based on the user's configuration.
- Added support for Elements with digital inputs/outputs (in the config builder tool)
### Fixed
- Fixed bakery bug - Negative wait for single input element was not working.
- Fixed bakery bug - Fixed the symmetric padding method when wait duration was even.
- Readme had voltage values in code examples that were not realistic.
- Fixed convention of input/output ports of Element in config builder

## [0.5.0] - 2021-12-2
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

[Unreleased]: https://github.com/qua-platform/py-qua-tools/compare/v0.5.0...HEAD
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
