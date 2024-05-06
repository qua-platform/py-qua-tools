from qualang_tools.simulator.quantum.architectures.from_qua_channels import TransmonPairBackendChannelIQ, \
    TransmonPairBackendChannelReadout
from qualang_tools.simulator.quantum.architectures.transmon_pair_backend_from_qua import ConfigToTransmonPairBackendMap
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_IQ import TimelineIQ
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_schedules import \
    TimelineSchedules
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_single import \
    TimelineSingle

Element = str


class Context:
    def __init__(self, qua_config: dict):
        self.vars = {}
        self.qua_config: dict = qua_config
        self.schedules: TimelineSchedules = TimelineSchedules()

    def create_timelines_for_each_element(self, channel_map: ConfigToTransmonPairBackendMap):
        for element, channel in channel_map.items():
            if isinstance(channel, TransmonPairBackendChannelIQ):
                self.schedules.map[element] = [
                    TimelineIQ(
                        qubit_index=channel.qubit_index,
                        pulse_channel_i=channel.get_qiskit_pulse_channel(quadrature='I'),
                        pulse_channel_q=channel.get_qiskit_pulse_channel(quadrature='Q'),
                    )
                ]
            elif isinstance(channel, TransmonPairBackendChannelReadout):
                self.schedules.map[element] = [
                    TimelineSingle(
                        qubit_index=channel.qubit_index,
                        pulse_channel=channel.get_qiskit_pulse_channel()
                    )
                ]
