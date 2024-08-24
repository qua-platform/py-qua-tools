class ChannelSpec:
    """ A specification for fixed channel requirements. """
    def __init__(self):
        self.channel_templates = None

    def __and__(self, other: 'ChannelSpec') -> 'ChannelSpec':
        combined_channel_spec = ChannelSpec()
        combined_channel_spec.channel_templates = self.channel_templates + other.channel_templates
        return combined_channel_spec

    def is_empty(self):
        return self.channel_templates is None or self.channel_templates == []
