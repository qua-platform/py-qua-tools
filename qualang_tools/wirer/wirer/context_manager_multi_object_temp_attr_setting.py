class MultiObjectTempAttrUpdater:
    def __init__(self, objects, **temp_attrs):
        """
        Initialize the MultiObjectTempAttrUpdater context manager.

        Parameters:
        - objects: A list of objects whose attributes will be temporarily updated.
        - temp_attrs: The temporary attributes and their values to be set.
        """
        self.objects = objects
        self.temp_attrs = temp_attrs
        self.original_attrs = []

    def __enter__(self):
        """
        Enter the runtime context related to this object.
        Temporarily set the objects' attributes to the new values.
        """
        # Store original attributes
        for obj in self.objects:
            original_attrs = {}
            for attr, value in self.temp_attrs.items():
                if hasattr(obj, attr):
                    original_attrs[attr] = getattr(obj, attr)
                else:
                    original_attrs[attr] = None

                # Set new temporary attribute value
                setattr(obj, attr, value)

            self.original_attrs.append((obj, original_attrs))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context.
        Restore the objects' original attributes.
        """
        for obj, original_attrs in self.original_attrs:
            for attr, value in original_attrs.items():
                setattr(obj, attr, value)
