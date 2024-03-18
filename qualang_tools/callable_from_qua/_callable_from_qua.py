from abc import ABC, abstractmethod
import dataclasses
from time import sleep
from typing import List, Any, Dict
from functools import wraps
from qm.QmJob import QmJob
from qm.program import Program
from qm.qua import declare_stream, save, pause
from qm.exceptions import QmQuaException
from qm.QuantumMachine import QuantumMachine
from qm.qua._dsl import _ResultSource, _Variable, align, _get_root_program_scope

__all__ = ["ProgramAddon", "callable_from_qua"]


@dataclasses.dataclass
class QuaCallableArgument:
    tag: str
    stream: _ResultSource


class QuaCallable:
    def __init__(
        self,
        fn: callable,
        qua_callable_stream: _ResultSource,
        qua_callable_id: int,
        args: List[Any],
        kwargs: Dict[str, Any],
    ):
        self._fn = fn
        self._qua_callable_id = qua_callable_id
        self._streams: Dict[str, _ResultSource] = {}
        self._declare(qua_callable_stream, args, kwargs)
        self._last_arg_fetch: Dict[str, int] = {}

    def _declare(
        self,
        qua_callable_stream: _ResultSource,
        args: List[Any],
        kwargs: Dict[str, Any],
    ):
        align()
        self._args = [self._convert_to_qua_arg(f"__pos__{i}", arg) for i, arg in enumerate(args)]
        self._kwargs = {name: self._convert_to_qua_arg(name, arg) for name, arg in kwargs.items()}
        save(self._qua_callable_id, qua_callable_stream)
        pause()
        align()

    def _convert_to_qua_arg(self, arg_id: str, arg):
        if isinstance(arg, _Variable):
            tag = f"__qua_callable__{self._qua_callable_id}__{arg_id}"
            stream = declare_stream()
            save(arg, stream)
            self._streams[tag] = stream
            return QuaCallableArgument(tag, stream)
        else:
            return arg

    def do_stream_processing(self):
        for tag, stream in self._streams.items():
            stream.with_timestamps().save(tag)

    def _convert_to_value_arg(self, job: QmJob, arg):
        if not isinstance(arg, QuaCallableArgument):
            return arg
        while True:
            value = job.result_handles.get(arg.tag).fetch_all()
            if value is not None and (arg.tag not in self._last_arg_fetch or self._last_arg_fetch[arg.tag] != value[1]):
                self._last_arg_fetch[arg.tag] = value[1]
                return value[0]
            sleep(0.01)

    def run(self, job: QmJob):
        args = [self._convert_to_value_arg(job, arg) for arg in self._args]
        kwargs = {name: self._convert_to_value_arg(job, arg) for name, arg in self._kwargs.items()}
        return self._fn(*args, **kwargs)


class ProgramAddon(ABC):
    @abstractmethod
    def enter_program(self, program: Program):
        ...

    @abstractmethod
    def exit_program(self, exc_type, exc_val, exc_tb):
        ...

    @abstractmethod
    def execute_program(self, program: Program, quantum_machine: QuantumMachine):
        ...


class QuaCallableEventManager(ProgramAddon):
    def __init__(self):
        """Framework allowing the user to call Python functions directly from the core of a QUA program.
        The Python function can be wrapped under a Python or QUA for loop and variables can be passed to and from this function (Python or QUA variables).
        This can be used to update the parameters of external instruments such as the Octave LO frequency and power, or the QDAC channel voltages for instance.
        It can also be used to post-process data in Python (machine learning, fitting, ...) and update the running QUA program seamlessly.
        It can also be used to quickly print the values of QUA variables for debugging purposes.
        """
        self._qua_callables: List[QuaCallable] = []
        self._qua_callable_stream = None
        self._last_qua_callable = -1
        self.callables: List[callable] = []  # TODO maybe merge with QuaCallable?
        self._qm = None  # TODO needed to transfer data from python to QUA with iovalues

        try:
            # Check if we are already inside a program
            _get_root_program_scope()
            self.declare_all()
        except QmQuaException:
            ...

    def enter_program(self, program: Program):
        self.declare_all()

    def exit_program(self, exc_type, exc_val, exc_tb):
        self.do_stream_processing()

    def execute_program(self, program: Program, quantum_machine: QuantumMachine):
        """
        Executes the program using the given quantum machine and set of local run functions called in the QUA program.

        Args:
            program: The program object.
            quantum_machine: The quantum machine object.
        """
        self._qm = quantum_machine  # TODO needed to transfer data from python to QUA with iovalues
        job = quantum_machine.get_running_job()
        result_handles = job.result_handles

        while result_handles.is_processing():
            self.attempt_qua_callable(job)

            for func in self.callables:
                func(result_handles)

    def register_qua_callable(self, fn: callable, *args, **kwargs):
        lr = QuaCallable(fn, self._qua_callable_stream, len(self._qua_callables), list(args), kwargs)
        self._qua_callables.append(lr)

    def declare_all(self):
        self._qua_callable_stream = declare_stream()

    def do_stream_processing(self):
        for qua_callable in self._qua_callables:
            qua_callable.do_stream_processing()
        if len(self._qua_callables) > 0:
            self._qua_callable_stream.with_timestamps().save("__qua_callable")

    def attempt_qua_callable(self, job: QmJob):
        if not job.is_paused():
            return
        qua_callable_id = job.result_handles.get("__qua_callable").fetch_all()
        if qua_callable_id is not None and qua_callable_id[1] != self._last_qua_callable:
            self._last_qua_callable = qua_callable_id[1]
            out = self._qua_callables[qua_callable_id[0]].run(
                job
            )  # TODO needed to transfer data from python to QUA with iovalues
            if out is not None:
                if isinstance(out, list) or isinstance(out, tuple):
                    if len(out) == 2:
                        self._qm.set_io1_value(out[0])
                        self._qm.set_io2_value(out[1])
                else:
                    self._qm.set_io1_value(out[0])
            job.resume()


def callable_from_qua(func: callable):
    """Decorator that allows the call of functions, to be executed in locally Python (on the control PC), directly from a QUA program.

    :param func: The function to be executed from a QUA program.
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            program = _get_root_program_scope()._program
        except IndexError:
            return func(*args, **kwargs)

        if not hasattr(program, "addons"):
            raise RuntimeError(
                "Cannot execute callable_from_qua function in a program until program is patched. "
                "Please first run qualang_tools.callable_from_qua.patch_qua_program_addons()"
            )

        if "callable_from_qua" not in program.addons:
            program.addons["callable_from_qua"] = QuaCallableEventManager()

        event_manager = program.addons["callable_from_qua"]
        # active_program_manager = QuaCallableEventManager._active_program_manager
        event_manager.register_qua_callable(func, *args, **kwargs)

    return wrapper
