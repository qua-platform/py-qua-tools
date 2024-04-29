from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class TransmonSettings:
    resonant_frequency: float
    anharmonicity: float
    rabi_frequency: float
