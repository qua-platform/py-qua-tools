from collections import Counter

from qualang_tools.wirer.connectivity.wiring_spec import WiringSpec
from qualang_tools.wirer.instruments.instrument_channel import AnyInstrumentChannel


class ChannelSpec:
    """A specification for fixed channel requirements."""

    def __init__(self):
        self.channel_templates = None

    def __and__(self, other: "ChannelSpec") -> "ChannelSpec":
        combined_channel_spec = ChannelSpec()
        combined_channel_spec.channel_templates = self.channel_templates + other.channel_templates
        return combined_channel_spec

    def is_empty(self):
        return self.channel_templates is None or self.channel_templates == []

    def filter_by_wiring_spec(self, wiring_spec: WiringSpec) -> "ChannelSpec":
        """
        Filters out channels from the specification if:
            1. Their I/O type is not required by the wiring specification
            2. They are digital but the wiring specification doesn't require triggering
        """

        def filter_func(channel: AnyInstrumentChannel):
            analog_channel_matches_io_type = (
                channel.signal_type == "digital" or channel.io_type in wiring_spec.io_type.value
            )
            digital_channel_only_if_triggered = channel.signal_type == "analog" or wiring_spec.triggered
            return analog_channel_matches_io_type and digital_channel_only_if_triggered

        filtered_channel_spec = ChannelSpec()
        filtered_channel_spec.channel_templates = list(filter(filter_func, self.channel_templates))

        return filtered_channel_spec

    def apply_constraints(self, constraints: "ChannelSpec") -> bool:
        """
        Attempt to constrain the channel specifications according to the
        filled attributes of all the specs in the `constraints` list.

        Returns:
            True: if constraints are successful, modifying the spec.
            False: if any of the constraints cannot be applied and are not already met.
        """
        # make sure there are at least enough channel templates in this object
        # of the correct type to satisfy each of the provided constraints.
        # e.g., it is invalid to apply a MW-FEM mask if there are only OPX+
        # channel templates present in this object.
        counts_templates = Counter([type(spec) for spec in self.channel_templates])
        counts_constraints = Counter([type(spec) for spec in constraints.channel_templates])

        for _type, count_constraints in counts_constraints.items():
            if count_constraints > counts_templates.get(_type, 0):
                return False

        # try to constraints to any possible spec in the list in order that
        # the constraint is provided.
        constrained_templates = []
        for constraint in constraints.channel_templates:
            constrained = False
            for template in self.channel_templates:
                if template in constrained_templates:
                    # can't constrain already constrained spec
                    continue
                if type(template) != type(constraint):
                    # can't constrain a spec of a different type
                    continue
                else:
                    attrs_to_constrain = ["con", "slot", "port"]
                    attrs_constrainable = 0
                    # make sure every filled attribute of the constraint can be
                    # applied to the spec without interfering with existing
                    # constraints.
                    for attr in attrs_to_constrain:
                        spec_attr = getattr(template, attr, None)
                        constraint_attr = getattr(constraint, attr, None)

                        constrainable = spec_attr is None
                        nothing_to_constrain = constraint_attr is None
                        constrained_already_met = constraint_attr == spec_attr

                        if constrainable or nothing_to_constrain or constrained_already_met:
                            attrs_constrainable += 1
                        else:
                            break

                    if attrs_constrainable == len(attrs_to_constrain):
                        for attr in attrs_to_constrain:
                            setattr(template, attr, getattr(constraint, attr, None))
                        constrained = True
                        constrained_templates.append(template)
                        break

            if not constrained:
                return False

        return True
