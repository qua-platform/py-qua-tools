from dataclasses import dataclass
from dataclasses_json import dataclass_json

from .transmon_settings import TransmonSettings


@dataclass_json
@dataclass
class TransmonPairSettings:
    transmon_1_settings: TransmonSettings
    transmon_2_settings: TransmonSettings
    coupling_strength: float
