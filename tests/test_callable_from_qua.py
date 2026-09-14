from qualang_tools.callable_from_qua import callable_from_qua, patch_qua_program_addons
from qm.qua import program


patch_qua_program_addons()

called = []


@callable_from_qua
def record_call(*args, **kwargs):
    called.append({"args": args, "kwargs": kwargs})


def test_callable_from_qua_does_not_run_python_while_compiling():
    called.clear()
    with program() as _prog:
        record_call()

    assert called == []
