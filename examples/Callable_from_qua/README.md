# Callable from QUA usage example

This module allows the user to define Python functions and call them directly from the core of a QUA program. 
Underneath the hood, a `pause/resume` workflow is implemented for each function and the `stream processing` is used to pass QUA variables directly as arguments of these functions.

You can read more about it in [callable_from QUA](../../qualang_tools/callable_from_qua/readme.md).

In this example folder, you will find several use-cases:
* [qua_print](qua_print.py): to print the values of QUA variables in the Python terminal for debugging purposes.
* [update_other_instruments](update_other_instruments.py): to update parameters from external instruments directly within QUA for_ loops.
* [feedback_on_external_instrument](feedback_on_external_instrument.py): to update external parameters based on the result of a measurement to showcase how to implement feedback based protocols using external instruments.

New features allowing live-plotting and the transfer of arrays between the running QUA program and Python terminal will be added in a future release.
