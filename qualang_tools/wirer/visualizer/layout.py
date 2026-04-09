# Map InstrumentChannel.instrument_id to containing instrument type
instrument_id_mapping = {
    "lf-fem": "OPX1000",
    "mw-fem": "OPX1000",
    "opx+": "OPX+",
    "octave": "Octave",
    "external-mixer": "Mixers",
    "qdac2": "QDAC2",
}

# Define the chassis dimensions
INSTRUMENT_FIGURE_DIMENSIONS = {
    "OPX1000": {"width": 8, "height": 3},
    "OPX+": {"width": 8, "height": 1},
    "Octave": {"width": 3, "height": 1},
    "Mixers": {"width": 1, "height": 1},
    "QDAC2": {"width": 12, "height": 3},
}

OPX_PLUS_ASPECT = INSTRUMENT_FIGURE_DIMENSIONS["OPX+"]["height"] / INSTRUMENT_FIGURE_DIMENSIONS["OPX+"]["width"]
OPX_1000_ASPECT = INSTRUMENT_FIGURE_DIMENSIONS["OPX1000"]["height"] / INSTRUMENT_FIGURE_DIMENSIONS["OPX1000"]["width"]
# Define the port positions for different modules
PORT_SPACING_FACTOR = 0.12
PORT_SIZE = 0.055

fem_analog_output_positions = [(0.05 + 0.25 * OPX_1000_ASPECT, 1.06 - i * PORT_SPACING_FACTOR) for i in range(8)]
fem_digital_output_positions = [(0.05 + 0.75 * OPX_1000_ASPECT, 0.86 - i * PORT_SPACING_FACTOR / 2.4) for i in range(8)]

# QDAC-II style: three front-panel rows of eight DC outputs (channels 1–24, top to bottom),
# plus a row of four external trigger inputs along the lower edge.
# X positions must stay inside the QDAC2 axes xlim (see instrument_figure_manager) so port labels
# (drawn slightly left of each port) are not clipped in the margin.
_QDAC2_X_SCALE = 3.0
_QDAC2_X0_NORM = 0.155  # left edge of 8-column grid (normalized, before * _QDAC2_X_SCALE)
_QDAC2_X_SPAN_NORM = 0.745  # (x_last - x_first) for the eight columns
qdac2_analog_output_positions = [
    (
        (_QDAC2_X0_NORM + col * (_QDAC2_X_SPAN_NORM / 7)) * _QDAC2_X_SCALE,
        0.8 - row * 0.24,
    )
    for row in range(3)
    for col in range(8)
]
_qdac2_trig_u0 = 0.22
_qdac2_trig_span = 0.52
qdac2_digital_input_positions = [
    ((_qdac2_trig_u0 + i * (_qdac2_trig_span / 3)) * _QDAC2_X_SCALE, 0.11) for i in range(4)
]

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
    "external-mixer": {
        "analog": {
            "input": [(0.75, 0.45)],
            "output": [(0.25, 0.45)],
        },
        "digital": {
            "input": [(0.25, 0.85)],
        },
    },
    "qdac2": {
        "analog": {"output": qdac2_analog_output_positions},
        "digital": {"input": qdac2_digital_input_positions},
    },
}
