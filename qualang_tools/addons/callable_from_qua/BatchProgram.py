import datetime
import os
from platform import python_version

import numpy as np
from typing import Callable, Optional, Dict
import qm
import xarray as xr
from git import Repo
from lib.batch.BatchJob import ActiveBatch, BatchJob
from lib.execution import execute, generate_qmm, log, pbar
from lib.save_utils import save_xarray
from qm import generate_qua_script
from qw_qm_admin.quam import QuAM
from qm import QmJob

from project_root import BASE_PATH


def _get_metadata(qmm, prog, config):
    qmm_version = qmm.version()
    repo = Repo(BASE_PATH)

    # This is required because os.getlogin() doesn't work on linux when running from a service
    # TODO: get specific exception type
    try:
        username = os.getlogin()
    except:
        username = ""

    md = {
        "user": username,
        "python": python_version(),
        "QOP client": qmm_version["client"],
        "QOP server": qmm_version["server"],
        "qw-qm commit": repo.git.log().split("\n")[0].split(" ")[1]
    }
    if (prog is not None) and (config is not None):
        s = generate_qua_script(prog, config)
        md["prog_and_config"] = s
    return md


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

    @staticmethod
    def close_all_quantum_machines():
        qmm = generate_qmm()
        qmm.close_all_quantum_machines()

    def execute(self,
                machine: QuAM,
                callback: Callable[['BatchProgram', QmJob], None] = None,
                callback_sleep: int = 1,
                execute_kwargs: Optional[Dict] = None,
                **kwargs) -> QmJob:
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
            if callback is not None and datetime.datetime.now()-self._last_callback > datetime.timedelta(seconds=callback_sleep):
                callback(self, job)
                self._last_callback = datetime.datetime.now()

        qmm = generate_qmm()
        self._last_execution = datetime.datetime.now()
        with execute(qmm, machine, self._program, timeout=100, config=self._config, execute_kwargs=execute_kwargs, **kwargs) as job:
            res_handles = job.result_handles
            for b, _ in self._batch_job:
                if b.progress_axis is not None:
                    pbar(job.result_handles, len(
                        b.progress_axis), b.label, fn=fn_callback)
            res_handles.wait_for_all_values()
            log.info('all values arrived')
            print(job.execution_report())

        self._metadata = _get_metadata(qmm, self._program, self._config)

        return job

    def _get_coord(self, job, b: ActiveBatch, name: str, data_vars):
        if b.is_over_time_axis(name):
            d = np.min([v[1][0].shape[0] for v in data_vars.values()])
            for v in data_vars.values():
                v[1][0] = v[1][0][:d, ]

            return np.array([self._last_execution + datetime.timedelta(microseconds=i[1]/1000)
                             for i in job.result_handles.get(f"{name}{b.label}").fetch_all()[:d]])
        else:
            return b.get_axis(name).values

    def _get_data(self, job, b: ActiveBatch, name: str):
        res = job.result_handles.get(b.get_result_var(
            name).save_arg(b.label)).fetch_all()
        if type(res[0]) == np.void:
            res = np.array([x[0] for x in res])
        return res

    def get_results(self,
                    job: QmJob,
                    batch_label: Optional[str] = 'batch',
                    filen: Optional[str] = 'unknown') -> xr.Dataset:
        """
        Returns the results of the job as an xarray dataset. The batch_label is used to label the batch dimension.

        Args:
            job: The QM job that was executed
            batch_label: The label to use for the batch dimension
            filen: The filename to save the dataset to

        Returns:
            An xarray dataset containing the results of the job
        """
        if self._last_execution is None:
            raise RuntimeError("please execute program first")
        batch_datasets = []
        for b, _ in self._batch_job:
            data_vars = {
                var_name: (
                    [batch_label] + [x.label for x in b.get_result_var(
                        var_name).get_independent_vars() if x.function is None],
                    [self._get_data(job, b, var_name)]
                )
                for var_name in b.dependent_var_names
            }
            coords = {
                var_name: self._get_coord(job, b, var_name, data_vars)
                for var_name in b.axes_names
            } | {
                batch_label: [b.label]
            }
            batch_datasets.append(
                xr.Dataset(data_vars=data_vars, coords=coords)
            )
        ds = xr.concat(batch_datasets, batch_label)

        # add extra coords
        extra_coords = {}

        # collect all extra coords
        for b, _ in self._batch_job:
            for var_name in b.axes_names:
                extra_coords[var_name] = {}
                ax = b.get_axis(var_name)
                if ax._extra_coords is not None:
                    for extra_coord in ax.get_extra_coords():
                        extra_coords[var_name][extra_coord] = []

        # evaluate extra coord values
        for var_name in extra_coords:
            for extra_coord_name in extra_coords[var_name]:
                for b, _ in self._batch_job:
                    transform_obj = b.get_axis(var_name).get_extra_coords()[
                        extra_coord_name]
                    if callable(transform_obj):
                        val = transform_obj(b.get_axis(var_name).values)
                    else:
                        val = np.polyval(
                            transform_obj, b.get_axis(var_name).values)
                    extra_coords[var_name][extra_coord_name].append(val)
                ds.coords[extra_coord_name] = (
                    (batch_label, var_name), extra_coords[var_name][extra_coord_name])

        ds.attrs.update(**self._metadata)
        save_xarray(ds, filen)

        return ds

    def simulate(self, simulation_config: qm.SimulationConfig, **kwargs):
        """
        Simulates the program using the given simulation config

        Args:
            simulation_config: The simulation config to use. Typically takes one initialization argument which is the
                number of FPGA clock cycles to simulate.
            **kwargs: Additional arguments to pass to the simulate function

        Returns:
            The simulation result
        """
        qmm = generate_qmm()
        return qmm.simulate(self._config, self._program, simulation_config, **kwargs)

    @property
    def metadata(self):
        return self._metadata
