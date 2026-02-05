from typing import Dict, Optional

import qm.api
from packaging.version import Version
from qm import QuantumMachine
from qm.api.models.compiler import CompilerOptionArguments
from qm.jobs.running_qm_job import RunningQmJob
from qm.program import Program
from qm.simulate.interface import SimulationConfig
import qm

# TODO: Remove this if block when we drop support for qm < 1.2.3 (and keep only the import that is currently in the
#  else block)
qua_below_1_2_3 = Version(qm.__version__) < Version("1.2.3")
if qua_below_1_2_3:
    from qm.qua._dsl import _ProgramScope as _ProgramScope_qua
else:
    from qm.qua._scope_management._core_scopes import _ProgramScope as _ProgramScope_qua

__all__ = [
    "patch_qua_program_addons",
]


class _ProgramScope(_ProgramScope_qua):
    def __enter__(self) -> Program:
        program = super().__enter__()

        # Instantiate all addons
        program.addons = {name: addon() for name, addon in Program.addons.items()}

        # TODO Should we add exception handling?
        for addon in self._program.addons.values():
            addon.enter_program(program)

        return self._program

    def __exit__(self, exc_type, exc_val, exc_tb):
        for addon in self._program.addons.values():
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


QM_execute_old_api = qm.api.v2.qm_api_old.QmApiWithDeprecations.execute


def QM_execute_patched_old_api(
    self,
    program: Program,
    duration_limit: int = 1000,
    data_limit: int = 20000,
    force_execution: int = False,
    dry_run: int = False,
    simulate: Optional[SimulationConfig] = None,
    compiler_options: Optional[CompilerOptionArguments] = None,
) -> RunningQmJob:
    return_val = QM_execute_old_api(
        self,
        program,
        duration_limit,
        data_limit,
        force_execution,
        dry_run,
        simulate,
        compiler_options=compiler_options,
    )

    for program_addon in program.addons.values():
        program_addon.execute_program(program=program, quantum_machine=self)

    return return_val


def patch_qua_program_addons():

    if hasattr(Program, "addons"):
        print("qm.program.Program already has 'addons' attribute, not patching")
    else:
        from qualang_tools.callable_from_qua import ProgramAddon

        Program.addons: Dict[str, ProgramAddon] = {}

    # TODO: Remove this if block when we drop support for qm < 1.2.3 (and keep only the import that is currently in the
    #  else block)
    if qua_below_1_2_3:
        import qm.qua._dsl

        if qm.qua._dsl._ProgramScope is _ProgramScope:
            print("qm.qua._dsl._ProgramScope already patched, not patching")
        else:
            qm.qua._dsl._ProgramScope = _ProgramScope
    else:
        # QUA >= 1.2.3: program() constructs _ProgramScope from qm.qua._dsl.scope_functions
        # To avoid class identity mismatches, patch the factory used by program() only.
        from qm.qua._dsl import scope_functions as _scope_functions

        if _scope_functions._ProgramScope is _ProgramScope:
            print("qm.qua._dsl.scope_functions._ProgramScope already patched, not patching")
        else:
            _scope_functions._ProgramScope = _ProgramScope

    # Patch QuantumMachine.execute without referencing the module name to avoid local scope confusion
    if QuantumMachine.execute is QM_execute_patched:
        print("qm.QuantumMachine.QuantumMachine.execute already patched, not patching")
    else:
        QuantumMachine.execute = QM_execute_patched

    # Patch old API execute by importing the class explicitly
    from qm.api.v2.qm_api_old import QmApiWithDeprecations as _QmApiWithDeprecations

    if _QmApiWithDeprecations.execute is QM_execute_patched_old_api:
        print("qm.QuantumMachine.QuantumMachine.execute already patched, not patching")
    else:
        _QmApiWithDeprecations.execute = QM_execute_patched_old_api
