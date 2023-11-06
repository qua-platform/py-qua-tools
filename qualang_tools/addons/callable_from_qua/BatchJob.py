import dataclasses
import inspect
from time import sleep
from typing import List, Any, Dict, TypeVar, Generic, Tuple, Iterator, Union

from qm.QmJob import QmJob
from qm.qua import declare_stream, save, FUNCTIONS, pause, declare, assign
from qm.qua._dsl import _ResultSource, _Variable, align

from lib.quaaxis import QuaAxis
from lib.quavar import QuaVar


class _ForAxisContextManager:

    def __init__(self, axis: QuaAxis, progress_st=None):
        self._progress_st = progress_st
        self._progress_var = declare(int) if progress_st is not None else None
        if self._progress_var is not None:
            assign(self._progress_var, 0)
        self._axis_for = axis.for_()
        self._axis_var: QuaVar = axis.var

    def __enter__(self):
        self._axis_for.__enter__()
        if self._progress_st is not None:
            save(self._progress_var, self._progress_st)
            assign(self._progress_var, self._progress_var + 1)
        return self._axis_var

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._axis_for.__exit__(exc_type, exc_val, exc_tb)
        if self._progress_st is not None:
            save(self._progress_var, self._progress_st)


@dataclasses.dataclass
class Batch:
    label: str
    data: Any
    axes: List[QuaAxis]


@dataclasses.dataclass
class LocalRunQuaArgument:
    tag: str
    stream: _ResultSource


class LocalRun:

    def __init__(self, fn: callable, local_run_stream: _ResultSource, local_run_id: int, args: List[Any], kwargs: Dict[str, Any]):
        self._fn = fn
        self._local_run_id = local_run_id
        self._streams: Dict[str, _ResultSource] = {}
        self._declare(local_run_stream, args, kwargs)
        self._last_arg_fetch: Dict[str, int] = {}

    def _declare(self, local_run_stream: _ResultSource, args: List[Any], kwargs: Dict[str, Any]):
        align()
        self._args = [self._convert_to_qua_arg(f"__pos__{i}", arg) for i, arg in enumerate(args)]
        self._kwargs = {name: self._convert_to_qua_arg(name, arg) for name, arg in kwargs.items()}
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
            if value is not None and (arg.tag not in self._last_arg_fetch or self._last_arg_fetch[arg.tag] != value[1]):
                self._last_arg_fetch[arg.tag] = value[1]
                return value[0]
            sleep(0.01)

    def run(self, job: QmJob):
        args = [self._convert_to_value_arg(job, arg) for arg in self._args]
        kwargs = {name: self._convert_to_value_arg(job, arg) for name, arg in self._kwargs.items()}
        self._fn(*args, **kwargs)


class _ActiveBatch:

    def __init__(self, batch: Batch):
        self._label = batch.label
        self._data = batch.data
        self._axes: Dict[str, QuaAxis] = {a.label: a for a in batch.axes}
        self._result_vars: Dict[str, QuaVar] = {}
        self._axes_order: List[str] = []
        self._progress_axis = None
        self._progress_axis_st = None
        self._average_axes: List[int] = []

    @property
    def data(self):
        return self._data

    @property
    def progress_axis(self):
        if self._progress_axis is None:
            return None
        return self._axes[self._progress_axis]

    @property
    def label(self):
        return self._label

    @property
    def dependent_var_names(self):
        return list(self._result_vars.keys())

    @property
    def independent_var_names(self):
        avg_axes = set([self._axes_order[i] for i in self._average_axes])
        return list(filter(lambda x: x not in avg_axes, self._axes_order))

    def get_axis(self, name):
        return self._axes[name]

    def get_result_var(self, name):
        return self._result_vars[name]

    def declare_result_var(self, type_: str, name: str):
        result_var = QuaVar(type_, name)
        if name in self._result_vars:
            raise RuntimeError("this variable was already defined for this batch")
        self._result_vars[name] = result_var
        return result_var.var

    def save_all_results(self):
        for result_var in self._result_vars.values():
            result_var.save_to_stream()

    def for_axis(self, name: str, average=False, progress=False):
        if name not in self._axes.keys():
            raise RuntimeError(f"axis '{name}' not found")
        self._axes_order.append(name)
        axis = self._axes[name]
        if average:
            self._average_axes.append(len(self._axes_order) - 1)
        if progress:
            if self._progress_axis is not None:
                raise RuntimeError(f"progress axis already exists")
            self._progress_axis = name
        return _ForAxisContextManager(axis,
                                      progress_st=self._progress_axis_st if progress else None)

    def for_extra_axis(self, axis: QuaAxis, average=False, progress=False):
        if axis.label in self._axes.keys():
            raise RuntimeError(f"axis '{axis.label}' already exists")
        self._axes[axis.label] = axis
        return self.for_axis(axis.label, average, progress)

    def for_(self, type: str, label: str, start: Union[float, int], stop: Union[float, int], step: Union[float, int], average=False, progress=False):
        axis = QuaAxis(type, label, start, stop, step)
        axis.declare()
        return self.for_extra_axis(axis, average, progress)

    def declare(self):
        for axis in self._axes.values():
            axis.declare()
        self._progress_axis_st = declare_stream()

    def do_stream_processing(self):
        axes_lengths = [len(self._axes[ax]) for ax in self._axes_order]
        for result_var in self._result_vars.values():
            st = result_var.st
            if result_var.qua_type == bool:
                st = st.boolean_to_int()
            if len(axes_lengths) > 0:
                st = st.buffer(*axes_lengths)
            if len(self._average_axes) > 0:
                st = st.map(FUNCTIONS.average(axis=self._average_axes))
            st.save(result_var.save_arg(self._label))
        if self._progress_axis is not None:
            self._progress_axis_st.save(self._label)


T = TypeVar('T')


class BatchJob(Generic[T]):

    def __init__(self, batches: List[Batch]):
        self._batches: List[_ActiveBatch] = list(map(lambda x: _ActiveBatch(x), batches))
        self._local_runs: List[LocalRun] = []
        self._local_run_stream = None
        self._last_local_run = -1

    def local_run(self, fn: callable, *args, **kwargs):
        lr = LocalRun(fn, self._local_run_stream, len(self._local_runs), list(args), kwargs)
        self._local_runs.append(lr)

    def declare_all(self):
        for b in self._batches:
            b.declare()
        self._local_run_stream = declare_stream()

    def do_stream_processing(self):
        for b in self._batches:
            b.do_stream_processing()
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

    def __iter__(self) -> Iterator[Tuple[_ActiveBatch, T]]:
        self.index = 0
        return self

    def __next__(self) -> tuple[_ActiveBatch, T]:
        if self.index < len(self._batches):
            b = self._batches[self.index]
            self.index += 1
            return b, b.data
        else:
            raise StopIteration
