# Map InstrumentChannel.instrument_id to containing instrument type
instrument_id_mapping = {
    "lf-fem": "OPX1000",
    "mw-fem": "OPX1000",
    "opx+": "OPX+",
    "octave": "Octave",
}

# Define the chassis dimensions
INSTRUMENT_FIGURE_DIMENSIONS = {
    "OPX1000": {"width": 8, "height": 3},
    "OPX+": {"width": 8, "height": 1},
    "Octave": {"width": 3, "height": 1}
}

OPX_PLUS_ASPECT = (INSTRUMENT_FIGURE_DIMENSIONS["OPX+"]["height"] /
                   INSTRUMENT_FIGURE_DIMENSIONS["OPX+"]["width"])
OPX_1000_ASPECT = (INSTRUMENT_FIGURE_DIMENSIONS["OPX1000"]["height"] /
                   INSTRUMENT_FIGURE_DIMENSIONS["OPX1000"]["width"])
# Define the port positions for different modules
PORT_SPACING_FACTOR = 0.1
PORT_SIZE = 0.04
PORT_POSITIONS = {
    "lf-fem": {
        "output": [(0.05 + 0.25 * OPX_1000_ASPECT, 1 - i * PORT_SPACING_FACTOR) for i in range(8)],
        "input": [(0.05 + 0.75 * OPX_1000_ASPECT, 1 - (6+i) * PORT_SPACING_FACTOR) for i in range(2)],
    },
    "mw-fem": {
        "output": [(0.05 + 0.25 * OPX_1000_ASPECT, 1 - i * PORT_SPACING_FACTOR) for i in range(8)],
        "input": [(0.05 + 0.75 * OPX_1000_ASPECT, 1 - i * PORT_SPACING_FACTOR * 7) for i in range(2)],
    },
    "opx+": {
        "input": [(0.75, 1 - i * PORT_SPACING_FACTOR * 2) for i in range(2)],
        "output": [(0.25 + j * PORT_SPACING_FACTOR, 1 - i * PORT_SPACING_FACTOR * 5) for i in range(2) for j in range(5)],
        "digital_output": [(0.25 + j * 0.2, 1 - i * PORT_SPACING_FACTOR * 10) for i in range(2) for j in range(5)],
    },
    "octave": {
        "input": [(0.75, 1 - i * PORT_SPACING_FACTOR * 2) for i in range(2)],
        "output": [(0.25 + j * 0.2, 1 - i * PORT_SPACING_FACTOR * 10) for i in range(2) for j in range(5)],
        "digital_output": [(0.25 + j * 0.2, 1 - i * PORT_SPACING_FACTOR * 10) for i in range(2) for j in range(5)],
    }
}

