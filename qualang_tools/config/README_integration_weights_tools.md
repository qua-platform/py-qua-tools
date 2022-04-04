# Integration Weights Tools

## Introduction
---------------
This package includes tools for the creation and manipulation of integration weights. 

## Functions
------------
* `convert_integration_weights` - Converts a list of integration weights, in which each sample corresponds to a clock cycle (4ns), to a list of tuples with the format (weight, time_to_integrate_in_ns). Can be used to convert between the old format (up to QOP 1.10) to the new format introduced in QOP 1.20.
* `compress_integration_weights` - Compresses the list of tuples with the format (weight, time_to_integrate_in_ns).
* `plot_integration_weights` - Plot the integration weights in units of ns.