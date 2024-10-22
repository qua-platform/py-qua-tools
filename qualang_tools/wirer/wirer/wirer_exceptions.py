from typing import List

from ..connectivity.channel_spec import ChannelSpec
from ..connectivity.wiring_spec import WiringSpec


class ConstraintsTooStrictException(Exception):
    def __init__(self, wiring_spec: WiringSpec, constraints: List[ChannelSpec]):
        message = (
            f"Failed to find a valid channel template for {wiring_spec.frequency} "
            f"{wiring_spec.io_type.value} channels on the "
            f"{wiring_spec.line_type.value} line for elements "
            f"{','.join([str(e.id) for e in wiring_spec.elements])} with the "
            f"following constraints: {constraints}"
        )
        super(ConstraintsTooStrictException, self).__init__(message)


class NotEnoughChannelsException(Exception):
    def __init__(self, wiring_spec: WiringSpec):
        message = (
            f"Couldn't find enough available {wiring_spec.frequency.value} "
            f"{wiring_spec.io_type.value} channels satisfying the wiring "
            f"specfication for the {wiring_spec.line_type.value} line for elements "
            f"{','.join([str(e.id) for e in wiring_spec.elements])}"
        )
        super(NotEnoughChannelsException, self).__init__(message)
