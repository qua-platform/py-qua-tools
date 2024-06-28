# Multi-user tools

This subpackage contains tools to be used when multiple users need to work
on the same QOP, and the queue functionality is insufficient since these
users need to work with different QMs or configs that share resources.

Currently, it contains a single method, `qm_session`, that allows a user to _try_ to
open a quantum machine, and if it is not possible since its resources are currently in use,
wait for them to free up. This is done by repeatedly polling the QM manager.

Once they are freed, execution will start automatically.
Once the context manager code block is exited, the QM will close automatically, freeing it up
for another user.

## Usage example

Note: `host`, `config` and `prog` are assumed to be supplied by user.

```python
from qm import QuantumMachinesManager
from qm import QmJob
from qualang_tools.multi_user import qm_session
qmm = QuantumMachinesManager(host)

with qm_session(qmm, config, timeout=100) as qm:
    job: QmJob = qm.execute(prog)
    print(job.execution_report())
# QM will close once this line is reached    
    
```