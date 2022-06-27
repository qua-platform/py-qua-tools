"""Tools to help handling plots from QUA programs.

Content:
    - interrupt_on_close: Allows to interrupt the execution and free the console when closing the live-plotting figure.
"""


def interrupt_on_close(figure, current_job):
    """
    Allows to interrupt the execution and free the console when closing the live-plotting figure.

    :param figure: the python figure instance correponding to the live-plotting figure.
    :param current_job: a ``QmJob`` object (see QM Job API) corresponding to the running job.
    :return: None.
    """

    def on_close(event):
        print("Execution stopped by user!")
        current_job.halt()
        event.canvas.stop_event_loop()

    figure.canvas.mpl_connect("close_event", on_close)
