from typing import Dict, Optional
from qm.api.models.compiler import CompilerOptionArguments
from qm.jobs.running_qm_job import RunningQmJob


from qm.program import Program
from qm.qua._dsl import _ProgramScope as _ProgramScope_qua
from qm.QuantumMachine import QuantumMachine
from qm.simulate.interface import SimulationConfig


__all__ = [
    "patch_qua_program_addons",
]


class _ProgramScope(_ProgramScope_qua):
    def __enter__(self) -> Program:
        program = super().__enter__()

        # Instantiate all addons
        program.addons = {name: addon() for name, addon in Program.addons.items()}

        # TODO Should we add exception handling?
        for addon in self.program.addons.values():
            addon.enter_program(program)

        return self.program

    def __exit__(self, exc_type, exc_val, exc_tb):
        for addon in self.program.addons.values():
            # TODO Should we add exception handling?
            addon.exit_program(exc_type, exc_val, exc_tb)

        exit_result = super().__exit__(exc_type, exc_val, exc_tb)

        return exit_result


QM_execute = QuantumMachine.execute


def QM_execute_patched(
    self,
    program: Program,
    duration_limit: int = 1000,
    data_limit: int = 20000,
    force_execution: int = False,
    dry_run: int = False,
    simulate: Optional[SimulationConfig] = None,
    compiler_options: Optional[CompilerOptionArguments] = None,
) -> RunningQmJob:
    return_val = QM_execute(
        self,
        program,
        duration_limit,
        data_limit,
        force_execution,
        dry_run,
        simulate,
        compiler_options,
    )

    for program_addon in program.addons.values():
        program_addon.execute_program(program=program, quantum_machine=self)

    return return_val


def patch_qua_program_addons():
    import qm.qua._dsl

    if hasattr(Program, "addons"):
        print("qm.program.Program already has 'addons' attribute, not patching")
    else:
        from qualang_tools.callable_from_qua import ProgramAddon

        Program.addons: Dict[str, ProgramAddon] = {}

    if qm.qua._dsl._ProgramScope is _ProgramScope:
        print("qm.qua._dsl._ProgramScope already patched, not patching")
    else:
        qm.qua._dsl._ProgramScope = _ProgramScope

    if qm.QuantumMachine.execute is QM_execute_patched:
        print("qm.QuantumMachine.QuantumMachine.execute already patched, not patching")
    else:
        qm.QuantumMachine.execute = QM_execute_patched
