"""Tools to help handling results from QUA programs.

Content:
    - fetching_tool: API to easily fetch data from the stream processing.
    - progress_counter: Displays progress bar and prints remaining computation time.
"""
import numpy as np
import time


class fetching_tool:
    def __init__(self, job, data_list, mode="wait_for_all"):
        """
        API to easily fetch data from the stream processing.
        **Example**: my_results = fetching_tool(job=my_job, data_list=["I", "Q"], mode="live")

        :param job: a ``QmJob`` object (see QM Job API) corresponding to the current execution.
        :param data_list: a list of the result names saved in the stream processing.
        :param mode: current acquisition mode among ['live', 'wait_for_all'], default is 'wait_for_all'. 'live' will fetch data one by one for all named results for live plotting purposes. 'wait_for_all' will wait until all values were processed for all named results.
        """
        if not data_list:
            raise Exception("The provided data list is empty.")
        if mode not in ["live", "wait_for_all"]:
            raise Exception(
                f"Mode '{mode}' is not supported. Supported modes are ['live', 'wait_for_all']"
            )
        self.data_list = data_list
        self.mode = mode
        self.results = []
        self.data_handles = []
        self.res_handles = job.result_handles
        if mode == "live":
            for data in self.data_list:
                if hasattr(self.res_handles, data):
                    self.data_handles.append(self.res_handles.get(data))
                    self.data_handles[-1].wait_for_values(1)
                else:
                    raise Warning(f"{data} is not saved in the stream processing.")
            # Live plotting parameters
            self._b_cont = False
            self._b_last = True
            self.start_time = 0

    def is_processing(self):
        """
        Returns True while the program is processing, and also once after the processing is done. Can be used for live plotting.
        **Example**: while my_results.is_processing():

        :return: boolean flag which is True while the program is processing, and also once after the processing is done.
        """
        if self.start_time == 0:
            self._b_cont = self.res_handles.is_processing()
            self._b_last = not self._b_cont
            self.start_time = time.time()
        else:
            self._b_cont = self.res_handles.is_processing()
            self._b_last = not (self._b_cont or self._b_last)
        return self._b_cont or self._b_last

    def _format(self, data):
        if type(data) == np.ndarray:
            if type(data[0]) == np.void:
                if len(data.dtype) == 1:
                    data = data["value"]
        return data

    def get_start_time(self):
        """
        Gets time at which is_processing() was first called. To be used in progress_counter().

        :return: float for the time at which is_processing() was first called.
        """
        return self.start_time

    def fetch_all(self):
        """
        Fetch a result from the current result stream saved in server memory. The result stream is populated by the
        save() and save_all() statements. Note that if timestamps are saved with the `with_timestamp()` method, then
        the result will contain both the values and timestamps.
        **Example**: I, Q = my_results.fetch_all()

        :return: all result of current result stream as a list of python variables
        """
        if self.mode == "wait_for_all":
            self.res_handles.wait_for_all_values()
            for data in self.data_list:
                if hasattr(self.res_handles, data):
                    self.results.append(
                        self._format(self.res_handles.get(data).fetch_all())
                    )

        elif self.mode == "live":
            self.results = []
            for i in range(len(self.data_handles)):
                self.results.append(self._format(self.data_handles[i].fetch_all()))
        return self.results


def progress_counter(
    iteration, total, progress_bar=True, percent=True, start_time=None
):
    """Displays progress bar and prints remaining computation time.

    :param iteration: current iteration. Must be a python integer.
    :param total: total number of iteration. Must be a python integer.
    :param progress_bar: Flag enabling the progress bar display. Must be True or False. Default is True.
    :param percent: Flag enabling the progress percentage display. Must be True or False. Default is True.
    :param start_time: Starting time of the program enabling the elapsed time display. Must be the result of time.time(). Default is None.
    :return: None.
    """
    current_percent = (iteration + 1) / total * 100

    progress = "Progress: "
    if progress_bar:
        bar = "#" * int(current_percent / 2)
        progress += "[" + bar + " " * (50 - len(bar)) + "] "
    if percent:
        progress += f"{current_percent:.1f}%"
    if start_time is not None:
        progress += f" --> elapsed time: {time.time()-start_time:.2f}s"

    print(progress, end="\r")
    if current_percent == 100:
        print("")
