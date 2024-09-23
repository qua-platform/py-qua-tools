from qm.qua import *
from qualang_tools.callable_from_qua import *

patch_qua_program_addons()


registered_calls = []


@callable_from_qua
def register_calls(*args, **kwargs):
    registered_calls.append({"args": args, "kwargs": kwargs})


def test_qua_callable_no_args(qmm, config):
    registered_calls.clear()
    with program() as prog:
        register_calls()

    assert not registered_calls
    qm = qmm.open_qm(config)
    job = qm.execute(prog)

    from time import sleep

    sleep(10)
    assert registered_calls == [{"args": (), "kwargs": {}}]
