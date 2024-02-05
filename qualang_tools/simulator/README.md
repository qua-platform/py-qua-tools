# Simulator tools
This library includes tools to help simulate programs

## create_simulator_controller_connections
Creates a list of :class:`~qm.simulate.interface.ControllerConnection` objects with the Inter-controllers connections between controllers in a way which maximizes the optical links connectivity.
For use inside the :class:`~qm.simulate.interface.SimulationConfig` for simulating the controllers' behavior.
It can be used to also simulate part of a small cluster: For example, the following command would create all the connections
needed to run a simulation on 'con1', 'con4', 'con5' which are part of a 9 OPX cluster: `create_simulator_controller_connections(9, [1,4,5])`

### Usage example
A simple example for a 3 OPX cluster:
```python
from qualang_tools.simulator import create_simulator_controller_connections

with program() as prog:
    # QUA program 

qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name)
job = qmm.simulate(config,
                   prog,
                   SimulationConfig(simulation_duration,
                                    controller_connections=create_simulator_controller_connections(3)))
```
 
A simulation running on 'con1', 'con4', 'con5' which are part of a 9 OPX cluster, which also has loopback connected between the controllers:
```python
from qualang_tools.simulator import create_simulator_controller_connections

with program() as prog:
    # QUA program 

qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name)
job = qmm.simulate(config,
                   prog,
                   SimulationConfig(simulation_duration,
                                    simulation_interface=LoopbackInterface([('con1', 1, 'con4', 1),
                                                                            ('con1', 2, 'con4', 2),
                                                                            ('con4', 1, 'con1', 1),
                                                                            ('con4', 2, 'con1', 2),
                                                                            ],
                                                                           latency=168),
                                    controller_connections=create_simulator_controller_connections(9, [1,4,5])))
```