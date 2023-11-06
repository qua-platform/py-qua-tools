import datetime
import os
from platform import python_version
import time
import numpy as np
from typing import Callable, Optional, Dict
import qm
import xarray as xr
from my_BatchJob import BatchJob
from qm import generate_qua_script
from qm import QmJob


class BatchProgram:
    """
    A class representing a QUA job (program + config) that was defined using the BatchJob interface.

    Methods

    execute(machine, callback=None, callback_sleep=1, **kwargs)
        Executes the program using the given machine. If callback is not None, it will be called every callback_sleep

    get_results(job, batch_label="batch",filen='unknown')
        Returns the results of the job as an xarray dataset. The batch_label is used to label the batch dimension.

    """

    def __init__(self,
                 program: qm.program._Program,
                 config: dict,
                 batch_job: BatchJob):
        self._program = program
        self._config = config
        self._batch_job = batch_job
        self._last_execution = None
        self._last_callback = None

    def execute(self,
                qm) -> QmJob:
        """
        Executes the program using the given machine. If callback is not None, it will be called every callback_sleep
        The execution uses a context manager, so the machine will be closed automatically when the execution is done.
        Furthermore, if another user is using any machine, the execution will wait until the machine is free.

        Args:
            machine: The QuAM used to configure the execution. This is used to generate the config that is needed to
                open a quantum machine, as well as to set the LOs.
            callback: A function to call every callback_sleep seconds. Has the signature callback(batchprogram, job)
            callback_sleep: The number of seconds between each callback call
            execute_kwargs: Additional arguments to pass to QuantumMachine.execute function. Typically used to pass compiler flags.
            **kwargs: Additional arguments to pass to the execute function

        Returns:
            The QM job that was executed
        """
        self._last_callback = datetime.datetime.now()

        def fn_callback():
            self._batch_job.attempt_local_run(job)

        job = qm.execute(self._program)
        res_handles = job.result_handles
        fn_callback()
        time.sleep(1)
        fn_callback()
        time.sleep(1)
        fn_callback()
        time.sleep(1)
        fn_callback()
        print(job.execution_report())

        return job
