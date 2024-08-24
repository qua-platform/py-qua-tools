from ..connectivity.wiring_spec import WiringSpec


class WirerException(Exception):
    def __init__(self, wiring_spec: WiringSpec):
        message = (
            f"Couldn't find available {wiring_spec.frequency.value} {wiring_spec.io_type.value} channels "
            f"satisfying the following specfication for the {wiring_spec.line_type.value} line for elements "
            f"{','.join([str(e.id) for e in wiring_spec.elements])}"
        )
        super(WirerException, self).__init__(message)
