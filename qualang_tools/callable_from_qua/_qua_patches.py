from abc import ABC, abstractmethod
from typing import Dict, Optional
from qm.api.models.compiler import CompilerOptionArguments
from qm.jobs.running_qm_job import RunningQmJob


from qm.program import Program  # as _Program_qua
from qm.qua._dsl import _ProgramScope as _ProgramScope_qua
from qm.QuantumMachine import QuantumMachine as _QuantumMachine_qua
from qm.simulate.interface import SimulationConfig


__all__ = [
    "ProgramAddon",
    "patch_callable_from_qua",
]


class ProgramAddon(ABC):
    @abstractmethod
    def enter_program(self, program: Program):
        ...

    @abstractmethod
    def exit_program(self, exc_type, exc_val, exc_tb):
        ...

    @abstractmethod
    def execute_program(self, program: Program, quantum_machine: _QuantumMachine_qua):
        ...


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


class QuantumMachine(_QuantumMachine_qua):
    def execute(
        self,
        program: Program,
        duration_limit: int = 1000,
        data_limit: int = 20000,
        force_execution: int = False,
        dry_run: int = False,
        simulate: Optional[SimulationConfig] = None,
        compiler_options: Optional[CompilerOptionArguments] = None,
    ) -> RunningQmJob:
        return_val = super().execute(
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


def patch_callable_from_qua():
    import qm.qua._dsl

    # from qm.qua import _dsl as qm_qua_dsl
    import qm.QuantumMachine

    # from qm.QuantumMachine import QuantumMachine as _QuantumMachine_qua

    if hasattr(Program, "addons"):
        print("qm.program.Program already has 'addons' attribute, not patching")
    else:
        Program.addons: Dict[str, ProgramAddon] = {}

    if qm.qua._dsl._ProgramScope is _ProgramScope:
        print("qm.qua._dsl._ProgramScope already patched, not patching")
    else:
        qm.qua._dsl._ProgramScope = _ProgramScope

    if qm.QuantumMachine.execute is QuantumMachine.execute:
        print("qm.QuantumMachine.QuantumMachine already patched, not patching")
    else:
        qm.QuantumMachine.execute = QuantumMachine.execute
