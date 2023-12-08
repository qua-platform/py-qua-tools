import dataclasses
from time import sleep
from typing import List, Any, Dict
from functools import wraps
from contextlib import contextmanager
from qm.QmJob import QmJob
from qm.QuantumMachine import QuantumMachine
from qm.program import Program
from qm.qua import declare_stream, save, pause
from qm.qua import program as qua_program
from qm.qua._dsl import _ResultSource, _Variable, align


__all__ = [
    "callable_from_qua",
    "program",
]


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
        return self._fn(*args, **kwargs)


class LocalRunManager:
    active_manager = None

    def __init__(self):
        """Framework allowing the user to call Python functions directly from the core of a QUA program.
        The Python function can be wrapped under a Python or QUA for loop and variables can be passed to and from this function (Python or QUA variables).
        This can be used to update the parameters of external instruments such as the Octave LO frequency and power, or the QDAC channel voltages for instance.
        It can also be used to post-process data in Python (machine learning, fitting, ...) and update the running QUA program seamlessly.
        It can also be used to quickly print the values of QUA variables for debugging purposes.
        """
        self._local_runs: List[LocalRun] = []
        self._local_run_stream = None
        self._last_local_run = -1
        self._qm = None  # TODO needed to transfer data from python to QUA with iovalues

    def register_local_run(self, fn: callable, *args, **kwargs):
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
            out = self._local_runs[local_run_id[0]].run(
                job
            )  # TODO needed to transfer data from python to QUA with iovalues
            if out is not None:
                if type(out) == list or type(out) == tuple:
                    if len(out) == 2:
                        self._qm.set_io1_value(out[0])
                        self._qm.set_io2_value(out[1])
                else:
                    self._qm.set_io1_value(out[0])
            job.resume()

    @contextmanager
    def local_run(
        self, quantum_machine: QuantumMachine, funcs: list[callable] = ()
    ) -> None:
        """
        Executes the program using the given quantum machine and set of local run functions called in the QUA program.

        Args:
            quantum_machine: The quantum machine object.
            funcs: Optional functions to be executed at each callback.
        """
        yield
        self._qm = quantum_machine  # TODO needed to transfer data from python to QUA with iovalues
        job = quantum_machine.get_running_job()
        result_handles = job.result_handles

        while result_handles.is_processing():
            self.attempt_local_run(job)
            for func in funcs:
                func(result_handles)


class ProgramScopeLocalRun:
    def __init__(self):
        self.local_run_manager = LocalRunManager()
        self.program_scope = qua_program()
        self.program = None

    def __enter__(self) -> Program:
        LocalRunManager.active_manager = self.local_run_manager
        self.program = self.program_scope.__enter__()
        self.local_run_manager.declare_all()
        return self.program

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.local_run_manager.do_stream_processing()
        self.program_scope.__exit__(exc_type, exc_val, exc_tb)

        # TODO this attribute setting should not be necessary
        self.program.local_run = self.local_run_manager.local_run


def callable_from_qua(func: callable):
    """Decorator that allows the call of functions, to be executed in locally Python (on the control PC), directly from a QUA program.

    :param func: The function to be executed from a QUA program.
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        local_run_manager = LocalRunManager.active_manager
        local_run_manager.register_local_run(func, *args, **kwargs)

    return wrapper
