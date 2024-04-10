# Deprecation Warning

ConfigGUI is no longer being actively developed and may not support all config functionality.
To use, you need to install the package using `pip instal qualang_tools[configbuilder]`

# Feature

GUI for creating configuration. It allows:
* Visualization of existing config
* Edits of existing fields
* Addition of components based on `ConfigBuilder` from `qualang_tools.config`

# Use

`python -m qualang_tools.config.gui`

When edits are made, user can download two files `config_edits.py` that contains all the edits. If needed, user can manually change this `config_edits.py` file, e.g. to delete unwanted additions of components.

# Restrictions

* While configuration can be explored when being build from `components` of `ConfigBuilder`, currently it cannot be directly edited if the items are initially added as objects. On the other hand, if configuration is purely config variable (no component objects are used in building it), it can be edited through the GUI.

# Possible future extensions

* Object view (currently just config file is seen)
* Raw file view in GUI
* Support for parameters in GUI
* Back views (show who uses some resource in GUI)
* Allow adding new field in direct config editing using OpenAPI schema (currently schema is used just to show docs)
* Restrict more tightly field value edits in direct config editing (currently it's not checking beyond general data type for correctness of entered values)
* Parsing initial raw config as minimal object model (so that we can see in object view even existing configs build before ConfigBuilder is used)
* Implement lazy addition to allow deletion of objects from config builder (currently there is no option to delete added element other than manually editing corresponding config_edits.py file)