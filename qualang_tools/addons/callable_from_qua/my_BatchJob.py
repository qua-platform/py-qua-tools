import dataclasses
import inspect
from time import sleep
from typing import List, Any, Dict, TypeVar, Generic, Tuple, Iterator, Union

from qm.QmJob import QmJob
from qm.qua import declare_stream, save, FUNCTIONS, pause, declare, assign
from qm.qua._dsl import _ResultSource, _Variable, align



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
        # save(self._local_run_id, local_run_stream)
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

T = TypeVar('T')

class BatchJob(Generic[T]):

    def __init__(self):
        # self._batches: List[_ActiveBatch] = list(map(lambda x: _ActiveBatch(x), batches))
        self._local_runs: List[LocalRun] = []
        self._local_run_stream = None
        self._last_local_run = -1

    def local_run(self, fn: callable, *args, **kwargs):
        lr = LocalRun(fn, self._local_run_stream, len(self._local_runs), list(args), kwargs)
        self._local_runs.append(lr)

    def declare_all(self):
        # for b in self._batches:
        #     b.declare()
        self._local_run_stream = declare_stream()

    def do_stream_processing(self):
        # for b in self._batches:
        #     b.do_stream_processing()
        for local_run in self._local_runs:
            local_run.do_stream_processing()
        if len(self._local_runs) > 0:
            self._local_run_stream.with_timestamps().save("__local_run")

    def attempt_local_run(self, job: QmJob):
        if not job.is_paused():
            return
        # local_run_id = job.result_handles.get("__local_run").fetch_all()
        # if local_run_id is not None and local_run_id[1] != self._last_local_run:
        #     self._last_local_run = local_run_id[1]
        #     self._local_runs[local_run_id[0]].run(job)
        #     job.resume()
        self._local_runs[0].run(job)
        job.resume()

    # def __iter__(self) -> Iterator[Tuple[_ActiveBatch, T]]:
    #     self.index = 0
    #     return self
    #
    # def __next__(self) -> tuple[_ActiveBatch, T]:
    #     if self.index < len(self._batches):
    #         b = self._batches[self.index]
    #         self.index += 1
    #         return b, b.data
    #     else:
    #         raise StopIteration
