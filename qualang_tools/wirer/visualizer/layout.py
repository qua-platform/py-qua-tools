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
    "Octave": {"width": 3, "height": 1},
}

OPX_PLUS_ASPECT = INSTRUMENT_FIGURE_DIMENSIONS["OPX+"]["height"] / INSTRUMENT_FIGURE_DIMENSIONS["OPX+"]["width"]
OPX_1000_ASPECT = INSTRUMENT_FIGURE_DIMENSIONS["OPX1000"]["height"] / INSTRUMENT_FIGURE_DIMENSIONS["OPX1000"]["width"]
# Define the port positions for different modules
PORT_SPACING_FACTOR = 0.12
PORT_SIZE = 0.055

fem_analog_output_positions = [(0.05 + 0.25 * OPX_1000_ASPECT, 1.06 - i * PORT_SPACING_FACTOR) for i in range(8)]
fem_digital_output_positions = [(0.05 + 0.75 * OPX_1000_ASPECT, 0.86 - i * PORT_SPACING_FACTOR / 2.4) for i in range(8)]

PORT_POSITIONS = {
    "lf-fem": {
        "analog": {
            "output": fem_analog_output_positions,
            "input": [(0.05 + 0.75 * OPX_1000_ASPECT, 1.06 - (6 + i) * PORT_SPACING_FACTOR) for i in range(2)],
        },
        "digital": {"output": fem_digital_output_positions},
    },
    "mw-fem": {
        "analog": {
            "output": fem_analog_output_positions,
            "input": [(0.05 + 0.75 * OPX_1000_ASPECT, 1.06 - i * PORT_SPACING_FACTOR * 7) for i in range(2)],
        },
        "digital": {"output": fem_digital_output_positions},
    },
    "opx+": {
        "analog": {
            "input": [(1.1 * 3, 0.01 + 0.32 / (i + 1)) for i in range(2)],
            "output": [((0.7 + j * 0.06) * 3, 0.01 + 0.32 / (i + 1)) for j in range(5) for i in range(2)],
        },
        "digital": {
            "output": [((0.3 + j * 0.06) * 3, 0.01 + 0.32 / (i + 1)) for j in range(5) for i in range(2)],
        },
    },
    "octave": {
        "analog": {
            "input": [((0.19 + j * 0.06) * 3, 0.25) for j in range(2)],
            "output": [((0.3 + j * 0.06) * 3, 0.32) for j in range(5)],
            "inter_input": [(1.1 * 3, 0.01 + 0.32 / (i + 1)) for i in range(2)],
            "inter_output": [((0.7 + j * 0.06) * 3, 0.01 + 0.32 / (i + 1)) for j in range(5) for i in range(2)],
        },
        "digital": {
            "input": [((0.3 + j * 0.06) * 3, 0.18) for j in range(5)],
        },
    },
}
