import dataclasses
from time import sleep
from typing import List, Any, Dict
from qm.QmJob import QmJob
from qm.qua import declare_stream, save, pause, program
from qm.qua._dsl import _ResultSource, _Variable, align
from qm import generate_qua_script
import qm


@dataclasses.dataclass
class LocalRunQuaArgument:
    tag: str
    stream: _ResultSource


class LocalRun:
    def __init__(
        self,
        fn: callable,
        local_run_stream: _ResultSource,
        local_run_id: int,
        args: List[Any],
        kwargs: Dict[str, Any],
    ):
        self._fn = fn
        self._local_run_id = local_run_id
        self._streams: Dict[str, _ResultSource] = {}
        self._declare(local_run_stream, args, kwargs)
        self._last_arg_fetch: Dict[str, int] = {}

    def _declare(
        self, local_run_stream: _ResultSource, args: List[Any], kwargs: Dict[str, Any]
    ):
        align()
        self._args = [
            self._convert_to_qua_arg(f"__pos__{i}", arg) for i, arg in enumerate(args)
        ]
        self._kwargs = {
            name: self._convert_to_qua_arg(name, arg) for name, arg in kwargs.items()
        }
        save(self._local_run_id, local_run_stream)
        pause()
        align()

    def _convert_to_qua_arg(self, arg_id: str, arg):
        if isinstance(arg, _Variable):
            tag = f"__local_run__{self._local_run_id}__{arg_id}"
            stream = declare_stream()
            save(arg, stream)
            self._streams[tag] = stream
            return LocalRunQuaArgument(tag, stream)
        else:
            return arg

    def do_stream_processing(self):
        for tag, stream in self._streams.items():
            stream.with_timestamps().save(tag)

    def _convert_to_value_arg(self, job: QmJob, arg):
        if not isinstance(arg, LocalRunQuaArgument):
            return arg
        while True:
            value = job.result_handles.get(arg.tag).fetch_all()
            if value is not None and (
                arg.tag not in self._last_arg_fetch
                or self._last_arg_fetch[arg.tag] != value[1]
            ):
                self._last_arg_fetch[arg.tag] = value[1]
                return value[0]
            sleep(0.01)

    def run(self, job: QmJob):
        args = [self._convert_to_value_arg(job, arg) for arg in self._args]
        kwargs = {
            name: self._convert_to_value_arg(job, arg)
            for name, arg in self._kwargs.items()
        }
        self._fn(*args, **kwargs)


class CallableFromQUA:
    def __init__(self, qua_sequence, quantum_machine):
        """Framework allowing the user to call Python functions directly from the core of a QUA program.
        The Python function can be wrapped under a Python or QUA for loop and variables can be passed to and from this function (Python or QUA variables).
        This can be used to update the parameters of external instruments such as the Octave LO frequency and power, or the QDAC channel voltages for instance.
        It can also be used to post-process data in Python (machine learning, fitting, ...) and update the running QUA program seamlessly.
        It can also be used to quickly print the values of QUA variables for debugging purposes.
            quantum_machine: The quantum machine object.

        """
        self._local_runs: List[LocalRun] = []
        self._local_run_stream = None
        self._last_local_run = -1
        self._qua_sequence = qua_sequence
        self._qm = quantum_machine
        self.qua_program = self._build_program(self._qm)

    def local_run(self, fn: callable, *args, **kwargs):
        lr = LocalRun(
            fn, self._local_run_stream, len(self._local_runs), list(args), kwargs
        )
        self._local_runs.append(lr)

    def declare_all(self):
        self._local_run_stream = declare_stream()

    def do_stream_processing(self):
        for local_run in self._local_runs:
            local_run.do_stream_processing()
        if len(self._local_runs) > 0:
            self._local_run_stream.with_timestamps().save("__local_run")

    def attempt_local_run(self, job: QmJob):
        if not job.is_paused():
            return
        local_run_id = job.result_handles.get("__local_run").fetch_all()
        if local_run_id is not None and local_run_id[1] != self._last_local_run:
            self._last_local_run = local_run_id[1]
            self._local_runs[local_run_id[0]].run(job)
            job.resume()

    def _build_program(self, qm):
        with program() as prog:
            self.declare_all()
            self._qua_sequence(self, qm)
            self.do_stream_processing()
        return prog

    def execute(
        self, func=None
    ) -> QmJob:
        """
        Executes the program using the given machine. If callback is not None, it will be called every callback_sleep
        The execution uses a context manager, so the machine will be closed automatically when the execution is done.
        Furthermore, if another user is using any machine, the execution will wait until the machine is free.

        Args:
            program: The QUA program to execute

        Returns:
            The QM job that was executed
        """

        if func is None:

            def func(x):
                return

        def fn_callback():
            self.attempt_local_run(job)
            func(res_handles)

        job = self._qm.execute(self.qua_program)
        res_handles = job.result_handles
        while res_handles.is_processing():
            fn_callback()
        return job

    def generate_qua_script(self, config):
        return generate_qua_script(self.qua_program, config)


def run_local(func):
    def wrapper(batches: CallableFromQUA, *args, **kwargs):
        batches.local_run(func, *args, **kwargs)

    return wrapper
