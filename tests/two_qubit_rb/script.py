
# Single QUA script generated at 2024-12-16 19:16:39.981865
# QUA library version: 1.2.1+g2

from qm import CompilerOptionArguments
from qm.qua import *

with program() as prog:
    v1 = declare(int, )
    v2 = declare(int, )
    v3 = declare(int, )
    v4 = declare(int, )
    input_stream___gates_len_is__ = declare_input_stream(int, '__gates_len_is__', size=1)
    v5 = declare(bool, )
    v6 = declare(bool, )
    with for_(v4,0,(v4<15),(v4+1)):
        advance_input_stream(input_stream___gates_len_is__)
        assign(v3, input_stream___gates_len_is__[0])
        with for_(v1,0,(v1<100),(v1+1)):
            align()
            align()
            assign(v2, ((Cast.to_int(v6)<<1)+Cast.to_int(v5)))
            r1 = declare_stream()
            save(v2, r1)
    with stream_processing():
        r1.buffer(100).buffer(15).save("state")


config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                "1": {
                    "offset": 0.0,
                },
                "2": {
                    "offset": 0.0,
                },
                "3": {
                    "offset": 0.0,
                },
                "4": {
                    "offset": 0.0,
                },
                "5": {
                    "offset": 0.0,
                },
                "6": {
                    "offset": 0.0,
                },
                "7": {
                    "offset": 0.0,
                },
                "8": {
                    "offset": 0.0,
                },
            },
            "digital_outputs": {
                "1": {},
            },
            "analog_inputs": {
                "1": {
                    "offset": 0.0,
                    "gain_db": 0,
                },
                "2": {
                    "offset": 0.0,
                    "gain_db": 0,
                },
            },
        },
    },
    "elements": {
        "rr1": {
            "mixInputs": {
                "I": ('con1', 5),
                "Q": ('con1', 6),
                "lo_frequency": 6350000000,
                "mixer": "mixer_resonator",
            },
            "intermediate_frequency": 75000000,
            "operations": {
                "cw": "const_pulse",
                "readout": "readout_pulse_q1",
            },
            "outputs": {
                "out1": ('con1', 1),
                "out2": ('con1', 2),
            },
            "time_of_flight": 24,
            "smearing": 0,
        },
        "rr2": {
            "mixInputs": {
                "I": ('con1', 5),
                "Q": ('con1', 6),
                "lo_frequency": 6350000000,
                "mixer": "mixer_resonator",
            },
            "intermediate_frequency": 133000000,
            "operations": {
                "cw": "const_pulse",
                "readout": "readout_pulse_q2",
            },
            "outputs": {
                "out1": ('con1', 1),
                "out2": ('con1', 2),
            },
            "time_of_flight": 24,
            "smearing": 0,
        },
        "q1_xy": {
            "mixInputs": {
                "I": ('con1', 1),
                "Q": ('con1', 2),
                "lo_frequency": 3950000000,
                "mixer": "mixer_qubit_q1",
            },
            "intermediate_frequency": 50000000,
            "operations": {
                "cw": "const_pulse",
                "x180": "x180_pulse_q1",
                "x90": "x90_pulse_q1",
                "-x90": "-x90_pulse_q1",
                "y90": "y90_pulse_q1",
                "y180": "y180_pulse_q1",
                "-y90": "-y90_pulse_q1",
            },
        },
        "q2_xy": {
            "mixInputs": {
                "I": ('con1', 3),
                "Q": ('con1', 4),
                "lo_frequency": 3950000000,
                "mixer": "mixer_qubit_q2",
            },
            "intermediate_frequency": 75000000,
            "operations": {
                "cw": "const_pulse",
                "x180": "x180_pulse_q2",
                "x90": "x90_pulse_q2",
                "-x90": "-x90_pulse_q2",
                "y90": "y90_pulse_q2",
                "y180": "y180_pulse_q2",
                "-y90": "-y90_pulse_q2",
            },
        },
        "q1_z": {
            "singleInput": {
                "port": ('con1', 7),
            },
            "operations": {
                "const": "const_flux_pulse",
                "cz": "cz_flux_pulse",
            },
        },
        "q2_z": {
            "singleInput": {
                "port": ('con1', 8),
            },
            "operations": {
                "const": "const_flux_pulse",
            },
        },
    },
    "pulses": {
        "const_flux_pulse": {
            "operation": "control",
            "length": 200,
            "waveforms": {
                "single": "const_flux_wf",
            },
        },
        "cz_flux_pulse": {
            "operation": "control",
            "length": 48,
            "waveforms": {
                "single": "cz_wf",
            },
        },
        "const_pulse": {
            "operation": "control",
            "length": 1000,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
        },
        "x90_pulse_q1": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "x90_I_wf_q1",
                "Q": "x90_Q_wf_q1",
            },
        },
        "x180_pulse_q1": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "x180_I_wf_q1",
                "Q": "x180_Q_wf_q1",
            },
        },
        "-x90_pulse_q1": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "minus_x90_I_wf_q1",
                "Q": "minus_x90_Q_wf_q1",
            },
        },
        "y90_pulse_q1": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "y90_I_wf_q1",
                "Q": "y90_Q_wf_q1",
            },
        },
        "y180_pulse_q1": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "y180_I_wf_q1",
                "Q": "y180_Q_wf_q1",
            },
        },
        "-y90_pulse_q1": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "minus_y90_I_wf_q1",
                "Q": "minus_y90_Q_wf_q1",
            },
        },
        "readout_pulse_q1": {
            "operation": "measurement",
            "length": 4000,
            "waveforms": {
                "I": "readout_wf_q1",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "cosine_weights",
                "sin": "sine_weights",
                "minus_sin": "minus_sine_weights",
                "rotated_cos": "rotated_cosine_weights_q1",
                "rotated_sin": "rotated_sine_weights_q1",
                "rotated_minus_sin": "rotated_minus_sine_weights_q1",
            },
            "digital_marker": "ON",
        },
        "x90_pulse_q2": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "x90_I_wf_q2",
                "Q": "x90_Q_wf_q2",
            },
        },
        "x180_pulse_q2": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "x180_I_wf_q2",
                "Q": "x180_Q_wf_q2",
            },
        },
        "-x90_pulse_q2": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "minus_x90_I_wf_q2",
                "Q": "minus_x90_Q_wf_q2",
            },
        },
        "y90_pulse_q2": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "y90_I_wf_q2",
                "Q": "y90_Q_wf_q2",
            },
        },
        "y180_pulse_q2": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "y180_I_wf_q2",
                "Q": "y180_Q_wf_q2",
            },
        },
        "-y90_pulse_q2": {
            "operation": "control",
            "length": 40,
            "waveforms": {
                "I": "minus_y90_I_wf_q2",
                "Q": "minus_y90_Q_wf_q2",
            },
        },
        "readout_pulse_q2": {
            "operation": "measurement",
            "length": 4000,
            "waveforms": {
                "I": "readout_wf_q2",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "cosine_weights",
                "sin": "sine_weights",
                "minus_sin": "minus_sine_weights",
                "rotated_cos": "rotated_cosine_weights_q2",
                "rotated_sin": "rotated_sine_weights_q2",
                "rotated_minus_sin": "rotated_minus_sine_weights_q2",
            },
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "const_wf": {
            "type": "constant",
            "sample": 0.27,
        },
        "cz_wf": {
            "type": "constant",
            "sample": 0.1,
        },
        "const_flux_wf": {
            "type": "constant",
            "sample": 0.45,
        },
        "zero_wf": {
            "type": "constant",
            "sample": 0.0,
        },
        "x90_I_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, 0.001949241310123983, 0.004413915548392845, 0.007472594583518853, 0.011196733610227046, 0.015643466436002788, 0.02084755462917499, 0.02681309463841636, 0.033505780194862875, 0.04084665121377841, 0.04870829954770786, 0.05691441836828156, 0.06524336218999913, 0.07343603512723698, 0.08120797512191433, 0.0882650022071939, 0.09432131565894536, 0.09911853044769706, 0.10244390404459669] + [0.10414596838104996] * 2 + [0.10244390404459669, 0.09911853044769706, 0.09432131565894536, 0.0882650022071939, 0.08120797512191433, 0.07343603512723698, 0.06524336218999913, 0.05691441836828156, 0.04870829954770786, 0.04084665121377841, 0.033505780194862875, 0.02681309463841636, 0.02084755462917499, 0.015643466436002788, 0.011196733610227046, 0.007472594583518853, 0.004413915548392845, 0.001949241310123983, 0.0],
        },
        "x90_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
        },
        "x180_I_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, 0.003898482620247966, 0.00882783109678569, 0.014945189167037706, 0.022393467220454093, 0.031286932872005575, 0.04169510925834998, 0.05362618927683272, 0.06701156038972575, 0.08169330242755682, 0.09741659909541572, 0.11382883673656312, 0.13048672437999825, 0.14687207025447396, 0.16241595024382866, 0.1765300044143878, 0.18864263131789072, 0.1982370608953941, 0.20488780808919338] + [0.20829193676209992] * 2 + [0.20488780808919338, 0.1982370608953941, 0.18864263131789072, 0.1765300044143878, 0.16241595024382866, 0.14687207025447396, 0.13048672437999825, 0.11382883673656312, 0.09741659909541572, 0.08169330242755682, 0.06701156038972575, 0.05362618927683272, 0.04169510925834998, 0.031286932872005575, 0.022393467220454093, 0.014945189167037706, 0.00882783109678569, 0.003898482620247966, 0.0],
        },
        "x180_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
        },
        "minus_x90_I_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, -0.001949241310123983, -0.004413915548392845, -0.007472594583518853, -0.011196733610227046, -0.015643466436002788, -0.02084755462917499, -0.02681309463841636, -0.033505780194862875, -0.04084665121377841, -0.04870829954770786, -0.05691441836828156, -0.06524336218999913, -0.07343603512723698, -0.08120797512191433, -0.0882650022071939, -0.09432131565894536, -0.09911853044769706, -0.10244390404459669] + [-0.10414596838104996] * 2 + [-0.10244390404459669, -0.09911853044769706, -0.09432131565894536, -0.0882650022071939, -0.08120797512191433, -0.07343603512723698, -0.06524336218999913, -0.05691441836828156, -0.04870829954770786, -0.04084665121377841, -0.033505780194862875, -0.02681309463841636, -0.02084755462917499, -0.015643466436002788, -0.011196733610227046, -0.007472594583518853, -0.004413915548392845, -0.001949241310123983, 0.0],
        },
        "minus_x90_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
        },
        "y90_I_wf_q1": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
        },
        "y90_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, 0.001949241310123983, 0.004413915548392845, 0.007472594583518853, 0.011196733610227046, 0.015643466436002788, 0.02084755462917499, 0.02681309463841636, 0.033505780194862875, 0.04084665121377841, 0.04870829954770786, 0.05691441836828156, 0.06524336218999913, 0.07343603512723698, 0.08120797512191433, 0.0882650022071939, 0.09432131565894536, 0.09911853044769706, 0.10244390404459669] + [0.10414596838104996] * 2 + [0.10244390404459669, 0.09911853044769706, 0.09432131565894536, 0.0882650022071939, 0.08120797512191433, 0.07343603512723698, 0.06524336218999913, 0.05691441836828156, 0.04870829954770786, 0.04084665121377841, 0.033505780194862875, 0.02681309463841636, 0.02084755462917499, 0.015643466436002788, 0.011196733610227046, 0.007472594583518853, 0.004413915548392845, 0.001949241310123983, 0.0],
        },
        "y180_I_wf_q1": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
        },
        "y180_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, 0.003898482620247966, 0.00882783109678569, 0.014945189167037706, 0.022393467220454093, 0.031286932872005575, 0.04169510925834998, 0.05362618927683272, 0.06701156038972575, 0.08169330242755682, 0.09741659909541572, 0.11382883673656312, 0.13048672437999825, 0.14687207025447396, 0.16241595024382866, 0.1765300044143878, 0.18864263131789072, 0.1982370608953941, 0.20488780808919338] + [0.20829193676209992] * 2 + [0.20488780808919338, 0.1982370608953941, 0.18864263131789072, 0.1765300044143878, 0.16241595024382866, 0.14687207025447396, 0.13048672437999825, 0.11382883673656312, 0.09741659909541572, 0.08169330242755682, 0.06701156038972575, 0.05362618927683272, 0.04169510925834998, 0.031286932872005575, 0.022393467220454093, 0.014945189167037706, 0.00882783109678569, 0.003898482620247966, 0.0],
        },
        "minus_y90_I_wf_q1": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
        },
        "minus_y90_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, -0.001949241310123983, -0.004413915548392845, -0.007472594583518853, -0.011196733610227046, -0.015643466436002788, -0.02084755462917499, -0.02681309463841636, -0.033505780194862875, -0.04084665121377841, -0.04870829954770786, -0.05691441836828156, -0.06524336218999913, -0.07343603512723698, -0.08120797512191433, -0.0882650022071939, -0.09432131565894536, -0.09911853044769706, -0.10244390404459669] + [-0.10414596838104996] * 2 + [-0.10244390404459669, -0.09911853044769706, -0.09432131565894536, -0.0882650022071939, -0.08120797512191433, -0.07343603512723698, -0.06524336218999913, -0.05691441836828156, -0.04870829954770786, -0.04084665121377841, -0.033505780194862875, -0.02681309463841636, -0.02084755462917499, -0.015643466436002788, -0.011196733610227046, -0.007472594583518853, -0.004413915548392845, -0.001949241310123983, 0.0],
        },
        "readout_wf_q1": {
            "type": "constant",
            "sample": 0.07,
        },
        "x90_I_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, 0.001949241310123983, 0.004413915548392845, 0.007472594583518853, 0.011196733610227046, 0.015643466436002788, 0.02084755462917499, 0.02681309463841636, 0.033505780194862875, 0.04084665121377841, 0.04870829954770786, 0.05691441836828156, 0.06524336218999913, 0.07343603512723698, 0.08120797512191433, 0.0882650022071939, 0.09432131565894536, 0.09911853044769706, 0.10244390404459669] + [0.10414596838104996] * 2 + [0.10244390404459669, 0.09911853044769706, 0.09432131565894536, 0.0882650022071939, 0.08120797512191433, 0.07343603512723698, 0.06524336218999913, 0.05691441836828156, 0.04870829954770786, 0.04084665121377841, 0.033505780194862875, 0.02681309463841636, 0.02084755462917499, 0.015643466436002788, 0.011196733610227046, 0.007472594583518853, 0.004413915548392845, 0.001949241310123983, 0.0],
        },
        "x90_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
        },
        "x180_I_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, 0.003898482620247966, 0.00882783109678569, 0.014945189167037706, 0.022393467220454093, 0.031286932872005575, 0.04169510925834998, 0.05362618927683272, 0.06701156038972575, 0.08169330242755682, 0.09741659909541572, 0.11382883673656312, 0.13048672437999825, 0.14687207025447396, 0.16241595024382866, 0.1765300044143878, 0.18864263131789072, 0.1982370608953941, 0.20488780808919338] + [0.20829193676209992] * 2 + [0.20488780808919338, 0.1982370608953941, 0.18864263131789072, 0.1765300044143878, 0.16241595024382866, 0.14687207025447396, 0.13048672437999825, 0.11382883673656312, 0.09741659909541572, 0.08169330242755682, 0.06701156038972575, 0.05362618927683272, 0.04169510925834998, 0.031286932872005575, 0.022393467220454093, 0.014945189167037706, 0.00882783109678569, 0.003898482620247966, 0.0],
        },
        "x180_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
        },
        "minus_x90_I_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, -0.001949241310123983, -0.004413915548392845, -0.007472594583518853, -0.011196733610227046, -0.015643466436002788, -0.02084755462917499, -0.02681309463841636, -0.033505780194862875, -0.04084665121377841, -0.04870829954770786, -0.05691441836828156, -0.06524336218999913, -0.07343603512723698, -0.08120797512191433, -0.0882650022071939, -0.09432131565894536, -0.09911853044769706, -0.10244390404459669] + [-0.10414596838104996] * 2 + [-0.10244390404459669, -0.09911853044769706, -0.09432131565894536, -0.0882650022071939, -0.08120797512191433, -0.07343603512723698, -0.06524336218999913, -0.05691441836828156, -0.04870829954770786, -0.04084665121377841, -0.033505780194862875, -0.02681309463841636, -0.02084755462917499, -0.015643466436002788, -0.011196733610227046, -0.007472594583518853, -0.004413915548392845, -0.001949241310123983, 0.0],
        },
        "minus_x90_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
        },
        "y90_I_wf_q2": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
        },
        "y90_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, 0.001949241310123983, 0.004413915548392845, 0.007472594583518853, 0.011196733610227046, 0.015643466436002788, 0.02084755462917499, 0.02681309463841636, 0.033505780194862875, 0.04084665121377841, 0.04870829954770786, 0.05691441836828156, 0.06524336218999913, 0.07343603512723698, 0.08120797512191433, 0.0882650022071939, 0.09432131565894536, 0.09911853044769706, 0.10244390404459669] + [0.10414596838104996] * 2 + [0.10244390404459669, 0.09911853044769706, 0.09432131565894536, 0.0882650022071939, 0.08120797512191433, 0.07343603512723698, 0.06524336218999913, 0.05691441836828156, 0.04870829954770786, 0.04084665121377841, 0.033505780194862875, 0.02681309463841636, 0.02084755462917499, 0.015643466436002788, 0.011196733610227046, 0.007472594583518853, 0.004413915548392845, 0.001949241310123983, 0.0],
        },
        "y180_I_wf_q2": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
        },
        "y180_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, 0.003898482620247966, 0.00882783109678569, 0.014945189167037706, 0.022393467220454093, 0.031286932872005575, 0.04169510925834998, 0.05362618927683272, 0.06701156038972575, 0.08169330242755682, 0.09741659909541572, 0.11382883673656312, 0.13048672437999825, 0.14687207025447396, 0.16241595024382866, 0.1765300044143878, 0.18864263131789072, 0.1982370608953941, 0.20488780808919338] + [0.20829193676209992] * 2 + [0.20488780808919338, 0.1982370608953941, 0.18864263131789072, 0.1765300044143878, 0.16241595024382866, 0.14687207025447396, 0.13048672437999825, 0.11382883673656312, 0.09741659909541572, 0.08169330242755682, 0.06701156038972575, 0.05362618927683272, 0.04169510925834998, 0.031286932872005575, 0.022393467220454093, 0.014945189167037706, 0.00882783109678569, 0.003898482620247966, 0.0],
        },
        "minus_y90_I_wf_q2": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
        },
        "minus_y90_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, -0.001949241310123983, -0.004413915548392845, -0.007472594583518853, -0.011196733610227046, -0.015643466436002788, -0.02084755462917499, -0.02681309463841636, -0.033505780194862875, -0.04084665121377841, -0.04870829954770786, -0.05691441836828156, -0.06524336218999913, -0.07343603512723698, -0.08120797512191433, -0.0882650022071939, -0.09432131565894536, -0.09911853044769706, -0.10244390404459669] + [-0.10414596838104996] * 2 + [-0.10244390404459669, -0.09911853044769706, -0.09432131565894536, -0.0882650022071939, -0.08120797512191433, -0.07343603512723698, -0.06524336218999913, -0.05691441836828156, -0.04870829954770786, -0.04084665121377841, -0.033505780194862875, -0.02681309463841636, -0.02084755462917499, -0.015643466436002788, -0.011196733610227046, -0.007472594583518853, -0.004413915548392845, -0.001949241310123983, 0.0],
        },
        "readout_wf_q2": {
            "type": "constant",
            "sample": 0.07,
        },
    },
    "digital_waveforms": {
        "ON": {
            "samples": [(1, 0)],
        },
    },
    "integration_weights": {
        "cosine_weights": {
            "cosine": [(1.0, 4000)],
            "sine": [(0.0, 4000)],
        },
        "sine_weights": {
            "cosine": [(0.0, 4000)],
            "sine": [(1.0, 4000)],
        },
        "minus_sine_weights": {
            "cosine": [(0.0, 4000)],
            "sine": [(-1.0, 4000)],
        },
        "rotated_cosine_weights_q1": {
            "cosine": [(1.0, 4000)],
            "sine": [(0.0, 4000)],
        },
        "rotated_sine_weights_q1": {
            "cosine": [(-0.0, 4000)],
            "sine": [(1.0, 4000)],
        },
        "rotated_minus_sine_weights_q1": {
            "cosine": [(0.0, 4000)],
            "sine": [(-1.0, 4000)],
        },
        "rotated_cosine_weights_q2": {
            "cosine": [(1.0, 4000)],
            "sine": [(0.0, 4000)],
        },
        "rotated_sine_weights_q2": {
            "cosine": [(-0.0, 4000)],
            "sine": [(1.0, 4000)],
        },
        "rotated_minus_sine_weights_q2": {
            "cosine": [(0.0, 4000)],
            "sine": [(-1.0, 4000)],
        },
    },
    "mixers": {
        "mixer_qubit_q1": [{'intermediate_frequency': 50000000, 'lo_frequency': 3950000000, 'correction': [1.0, 0.0, 0.0, 1.0]}],
        "mixer_qubit_q2": [{'intermediate_frequency': 75000000, 'lo_frequency': 3950000000, 'correction': [1.0, 0.0, 0.0, 1.0]}],
        "mixer_resonator": [
            {'intermediate_frequency': 75000000, 'lo_frequency': 6350000000, 'correction': [1.0, -0.0, -0.0, 1.0]},
            {'intermediate_frequency': 133000000, 'lo_frequency': 6350000000, 'correction': [1.0, -0.0, -0.0, 1.0]},
        ],
    },
}

loaded_config = {
    "version": 1,
    "controllers": {
        "con1": {
            "type": "opx1",
            "analog_outputs": {
                "1": {
                    "offset": 0.0,
                    "delay": 0,
                    "shareable": False,
                    "filter": {
                        "feedforward": [],
                        "feedback": [],
                    },
                    "crosstalk": {},
                },
                "2": {
                    "offset": 0.0,
                    "delay": 0,
                    "shareable": False,
                    "filter": {
                        "feedforward": [],
                        "feedback": [],
                    },
                    "crosstalk": {},
                },
                "3": {
                    "offset": 0.0,
                    "delay": 0,
                    "shareable": False,
                    "filter": {
                        "feedforward": [],
                        "feedback": [],
                    },
                    "crosstalk": {},
                },
                "4": {
                    "offset": 0.0,
                    "delay": 0,
                    "shareable": False,
                    "filter": {
                        "feedforward": [],
                        "feedback": [],
                    },
                    "crosstalk": {},
                },
                "5": {
                    "offset": 0.0,
                    "delay": 0,
                    "shareable": False,
                    "filter": {
                        "feedforward": [],
                        "feedback": [],
                    },
                    "crosstalk": {},
                },
                "6": {
                    "offset": 0.0,
                    "delay": 0,
                    "shareable": False,
                    "filter": {
                        "feedforward": [],
                        "feedback": [],
                    },
                    "crosstalk": {},
                },
                "7": {
                    "offset": 0.0,
                    "delay": 0,
                    "shareable": False,
                    "filter": {
                        "feedforward": [],
                        "feedback": [],
                    },
                    "crosstalk": {},
                },
                "8": {
                    "offset": 0.0,
                    "delay": 0,
                    "shareable": False,
                    "filter": {
                        "feedforward": [],
                        "feedback": [],
                    },
                    "crosstalk": {},
                },
            },
            "analog_inputs": {
                "1": {
                    "offset": 0.0,
                    "gain_db": 0,
                    "shareable": False,
                    "sampling_rate": 1000000000.0,
                },
                "2": {
                    "offset": 0.0,
                    "gain_db": 0,
                    "shareable": False,
                    "sampling_rate": 1000000000.0,
                },
            },
            "digital_outputs": {
                "1": {
                    "shareable": False,
                    "inverted": False,
                    "level": "LVTTL",
                },
            },
            "digital_inputs": {},
        },
    },
    "oscillators": {},
    "elements": {
        "rr1": {
            "digitalInputs": {},
            "digitalOutputs": {},
            "outputs": {
                "out1": ('con1', 1, 1),
                "out2": ('con1', 1, 2),
            },
            "operations": {
                "cw": "const_pulse",
                "readout": "readout_pulse_q1",
            },
            "hold_offset": {
                "duration": 0,
            },
            "sticky": {
                "analog": False,
                "digital": False,
                "duration": 4,
            },
            "thread": "",
            "mixInputs": {
                "I": ('con1', 1, 5),
                "Q": ('con1', 1, 6),
                "mixer": "mixer_resonator",
                "lo_frequency": 6350000000.0,
            },
            "smearing": 0,
            "time_of_flight": 24,
            "intermediate_frequency": 75000000.0,
        },
        "rr2": {
            "digitalInputs": {},
            "digitalOutputs": {},
            "outputs": {
                "out1": ('con1', 1, 1),
                "out2": ('con1', 1, 2),
            },
            "operations": {
                "cw": "const_pulse",
                "readout": "readout_pulse_q2",
            },
            "hold_offset": {
                "duration": 0,
            },
            "sticky": {
                "analog": False,
                "digital": False,
                "duration": 4,
            },
            "thread": "",
            "mixInputs": {
                "I": ('con1', 1, 5),
                "Q": ('con1', 1, 6),
                "mixer": "mixer_resonator",
                "lo_frequency": 6350000000.0,
            },
            "smearing": 0,
            "time_of_flight": 24,
            "intermediate_frequency": 133000000.0,
        },
        "q1_xy": {
            "digitalInputs": {},
            "digitalOutputs": {},
            "outputs": {},
            "operations": {
                "cw": "const_pulse",
                "x180": "x180_pulse_q1",
                "x90": "x90_pulse_q1",
                "-x90": "-x90_pulse_q1",
                "y90": "y90_pulse_q1",
                "y180": "y180_pulse_q1",
                "-y90": "-y90_pulse_q1",
            },
            "hold_offset": {
                "duration": 0,
            },
            "sticky": {
                "analog": False,
                "digital": False,
                "duration": 4,
            },
            "thread": "",
            "mixInputs": {
                "I": ('con1', 1, 1),
                "Q": ('con1', 1, 2),
                "mixer": "mixer_qubit_q1",
                "lo_frequency": 3950000000.0,
            },
            "intermediate_frequency": 50000000.0,
        },
        "q2_xy": {
            "digitalInputs": {},
            "digitalOutputs": {},
            "outputs": {},
            "operations": {
                "cw": "const_pulse",
                "x180": "x180_pulse_q2",
                "x90": "x90_pulse_q2",
                "-x90": "-x90_pulse_q2",
                "y90": "y90_pulse_q2",
                "y180": "y180_pulse_q2",
                "-y90": "-y90_pulse_q2",
            },
            "hold_offset": {
                "duration": 0,
            },
            "sticky": {
                "analog": False,
                "digital": False,
                "duration": 4,
            },
            "thread": "",
            "mixInputs": {
                "I": ('con1', 1, 3),
                "Q": ('con1', 1, 4),
                "mixer": "mixer_qubit_q2",
                "lo_frequency": 3950000000.0,
            },
            "intermediate_frequency": 75000000.0,
        },
        "q1_z": {
            "digitalInputs": {},
            "digitalOutputs": {},
            "outputs": {},
            "operations": {
                "const": "const_flux_pulse",
                "cz": "cz_flux_pulse",
            },
            "hold_offset": {
                "duration": 0,
            },
            "sticky": {
                "analog": False,
                "digital": False,
                "duration": 4,
            },
            "thread": "",
            "singleInput": {
                "port": ('con1', 1, 7),
            },
        },
        "q2_z": {
            "digitalInputs": {},
            "digitalOutputs": {},
            "outputs": {},
            "operations": {
                "const": "const_flux_pulse",
            },
            "hold_offset": {
                "duration": 0,
            },
            "sticky": {
                "analog": False,
                "digital": False,
                "duration": 4,
            },
            "thread": "",
            "singleInput": {
                "port": ('con1', 1, 8),
            },
        },
    },
    "pulses": {
        "const_flux_pulse": {
            "length": 200,
            "waveforms": {
                "single": "const_flux_wf",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "cz_flux_pulse": {
            "length": 48,
            "waveforms": {
                "single": "cz_wf",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "const_pulse": {
            "length": 1000,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "x90_pulse_q1": {
            "length": 40,
            "waveforms": {
                "I": "x90_I_wf_q1",
                "Q": "x90_Q_wf_q1",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "x180_pulse_q1": {
            "length": 40,
            "waveforms": {
                "I": "x180_I_wf_q1",
                "Q": "x180_Q_wf_q1",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "-x90_pulse_q1": {
            "length": 40,
            "waveforms": {
                "I": "minus_x90_I_wf_q1",
                "Q": "minus_x90_Q_wf_q1",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "y90_pulse_q1": {
            "length": 40,
            "waveforms": {
                "I": "y90_I_wf_q1",
                "Q": "y90_Q_wf_q1",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "y180_pulse_q1": {
            "length": 40,
            "waveforms": {
                "I": "y180_I_wf_q1",
                "Q": "y180_Q_wf_q1",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "-y90_pulse_q1": {
            "length": 40,
            "waveforms": {
                "I": "minus_y90_I_wf_q1",
                "Q": "minus_y90_Q_wf_q1",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "readout_pulse_q1": {
            "length": 4000,
            "waveforms": {
                "I": "readout_wf_q1",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "cosine_weights",
                "sin": "sine_weights",
                "minus_sin": "minus_sine_weights",
                "rotated_cos": "rotated_cosine_weights_q1",
                "rotated_sin": "rotated_sine_weights_q1",
                "rotated_minus_sin": "rotated_minus_sine_weights_q1",
            },
            "operation": "measurement",
            "digital_marker": "ON",
        },
        "x90_pulse_q2": {
            "length": 40,
            "waveforms": {
                "I": "x90_I_wf_q2",
                "Q": "x90_Q_wf_q2",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "x180_pulse_q2": {
            "length": 40,
            "waveforms": {
                "I": "x180_I_wf_q2",
                "Q": "x180_Q_wf_q2",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "-x90_pulse_q2": {
            "length": 40,
            "waveforms": {
                "I": "minus_x90_I_wf_q2",
                "Q": "minus_x90_Q_wf_q2",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "y90_pulse_q2": {
            "length": 40,
            "waveforms": {
                "I": "y90_I_wf_q2",
                "Q": "y90_Q_wf_q2",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "y180_pulse_q2": {
            "length": 40,
            "waveforms": {
                "I": "y180_I_wf_q2",
                "Q": "y180_Q_wf_q2",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "-y90_pulse_q2": {
            "length": 40,
            "waveforms": {
                "I": "minus_y90_I_wf_q2",
                "Q": "minus_y90_Q_wf_q2",
            },
            "integration_weights": {},
            "operation": "control",
        },
        "readout_pulse_q2": {
            "length": 4000,
            "waveforms": {
                "I": "readout_wf_q2",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "cosine_weights",
                "sin": "sine_weights",
                "minus_sin": "minus_sine_weights",
                "rotated_cos": "rotated_cosine_weights_q2",
                "rotated_sin": "rotated_sine_weights_q2",
                "rotated_minus_sin": "rotated_minus_sine_weights_q2",
            },
            "operation": "measurement",
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "const_wf": {
            "type": "constant",
            "sample": 0.27,
        },
        "cz_wf": {
            "type": "constant",
            "sample": 0.1,
        },
        "const_flux_wf": {
            "type": "constant",
            "sample": 0.45,
        },
        "zero_wf": {
            "type": "constant",
            "sample": 0.0,
        },
        "x90_I_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, 0.001949241310123983, 0.004413915548392845, 0.007472594583518853, 0.011196733610227046, 0.015643466436002788, 0.02084755462917499, 0.02681309463841636, 0.033505780194862875, 0.04084665121377841, 0.04870829954770786, 0.05691441836828156, 0.06524336218999913, 0.07343603512723698, 0.08120797512191433, 0.0882650022071939, 0.09432131565894536, 0.09911853044769706, 0.10244390404459669] + [0.10414596838104996] * 2 + [0.10244390404459669, 0.09911853044769706, 0.09432131565894536, 0.0882650022071939, 0.08120797512191433, 0.07343603512723698, 0.06524336218999913, 0.05691441836828156, 0.04870829954770786, 0.04084665121377841, 0.033505780194862875, 0.02681309463841636, 0.02084755462917499, 0.015643466436002788, 0.011196733610227046, 0.007472594583518853, 0.004413915548392845, 0.001949241310123983, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "x90_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "x180_I_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, 0.003898482620247966, 0.00882783109678569, 0.014945189167037706, 0.022393467220454093, 0.031286932872005575, 0.04169510925834998, 0.05362618927683272, 0.06701156038972575, 0.08169330242755682, 0.09741659909541572, 0.11382883673656312, 0.13048672437999825, 0.14687207025447396, 0.16241595024382866, 0.1765300044143878, 0.18864263131789072, 0.1982370608953941, 0.20488780808919338] + [0.20829193676209992] * 2 + [0.20488780808919338, 0.1982370608953941, 0.18864263131789072, 0.1765300044143878, 0.16241595024382866, 0.14687207025447396, 0.13048672437999825, 0.11382883673656312, 0.09741659909541572, 0.08169330242755682, 0.06701156038972575, 0.05362618927683272, 0.04169510925834998, 0.031286932872005575, 0.022393467220454093, 0.014945189167037706, 0.00882783109678569, 0.003898482620247966, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "x180_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "minus_x90_I_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, -0.001949241310123983, -0.004413915548392845, -0.007472594583518853, -0.011196733610227046, -0.015643466436002788, -0.02084755462917499, -0.02681309463841636, -0.033505780194862875, -0.04084665121377841, -0.04870829954770786, -0.05691441836828156, -0.06524336218999913, -0.07343603512723698, -0.08120797512191433, -0.0882650022071939, -0.09432131565894536, -0.09911853044769706, -0.10244390404459669] + [-0.10414596838104996] * 2 + [-0.10244390404459669, -0.09911853044769706, -0.09432131565894536, -0.0882650022071939, -0.08120797512191433, -0.07343603512723698, -0.06524336218999913, -0.05691441836828156, -0.04870829954770786, -0.04084665121377841, -0.033505780194862875, -0.02681309463841636, -0.02084755462917499, -0.015643466436002788, -0.011196733610227046, -0.007472594583518853, -0.004413915548392845, -0.001949241310123983, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "minus_x90_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "y90_I_wf_q1": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "y90_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, 0.001949241310123983, 0.004413915548392845, 0.007472594583518853, 0.011196733610227046, 0.015643466436002788, 0.02084755462917499, 0.02681309463841636, 0.033505780194862875, 0.04084665121377841, 0.04870829954770786, 0.05691441836828156, 0.06524336218999913, 0.07343603512723698, 0.08120797512191433, 0.0882650022071939, 0.09432131565894536, 0.09911853044769706, 0.10244390404459669] + [0.10414596838104996] * 2 + [0.10244390404459669, 0.09911853044769706, 0.09432131565894536, 0.0882650022071939, 0.08120797512191433, 0.07343603512723698, 0.06524336218999913, 0.05691441836828156, 0.04870829954770786, 0.04084665121377841, 0.033505780194862875, 0.02681309463841636, 0.02084755462917499, 0.015643466436002788, 0.011196733610227046, 0.007472594583518853, 0.004413915548392845, 0.001949241310123983, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "y180_I_wf_q1": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "y180_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, 0.003898482620247966, 0.00882783109678569, 0.014945189167037706, 0.022393467220454093, 0.031286932872005575, 0.04169510925834998, 0.05362618927683272, 0.06701156038972575, 0.08169330242755682, 0.09741659909541572, 0.11382883673656312, 0.13048672437999825, 0.14687207025447396, 0.16241595024382866, 0.1765300044143878, 0.18864263131789072, 0.1982370608953941, 0.20488780808919338] + [0.20829193676209992] * 2 + [0.20488780808919338, 0.1982370608953941, 0.18864263131789072, 0.1765300044143878, 0.16241595024382866, 0.14687207025447396, 0.13048672437999825, 0.11382883673656312, 0.09741659909541572, 0.08169330242755682, 0.06701156038972575, 0.05362618927683272, 0.04169510925834998, 0.031286932872005575, 0.022393467220454093, 0.014945189167037706, 0.00882783109678569, 0.003898482620247966, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "minus_y90_I_wf_q1": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "minus_y90_Q_wf_q1": {
            "type": "arbitrary",
            "samples": [0.0, -0.001949241310123983, -0.004413915548392845, -0.007472594583518853, -0.011196733610227046, -0.015643466436002788, -0.02084755462917499, -0.02681309463841636, -0.033505780194862875, -0.04084665121377841, -0.04870829954770786, -0.05691441836828156, -0.06524336218999913, -0.07343603512723698, -0.08120797512191433, -0.0882650022071939, -0.09432131565894536, -0.09911853044769706, -0.10244390404459669] + [-0.10414596838104996] * 2 + [-0.10244390404459669, -0.09911853044769706, -0.09432131565894536, -0.0882650022071939, -0.08120797512191433, -0.07343603512723698, -0.06524336218999913, -0.05691441836828156, -0.04870829954770786, -0.04084665121377841, -0.033505780194862875, -0.02681309463841636, -0.02084755462917499, -0.015643466436002788, -0.011196733610227046, -0.007472594583518853, -0.004413915548392845, -0.001949241310123983, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "readout_wf_q1": {
            "type": "constant",
            "sample": 0.07,
        },
        "x90_I_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, 0.001949241310123983, 0.004413915548392845, 0.007472594583518853, 0.011196733610227046, 0.015643466436002788, 0.02084755462917499, 0.02681309463841636, 0.033505780194862875, 0.04084665121377841, 0.04870829954770786, 0.05691441836828156, 0.06524336218999913, 0.07343603512723698, 0.08120797512191433, 0.0882650022071939, 0.09432131565894536, 0.09911853044769706, 0.10244390404459669] + [0.10414596838104996] * 2 + [0.10244390404459669, 0.09911853044769706, 0.09432131565894536, 0.0882650022071939, 0.08120797512191433, 0.07343603512723698, 0.06524336218999913, 0.05691441836828156, 0.04870829954770786, 0.04084665121377841, 0.033505780194862875, 0.02681309463841636, 0.02084755462917499, 0.015643466436002788, 0.011196733610227046, 0.007472594583518853, 0.004413915548392845, 0.001949241310123983, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "x90_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "x180_I_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, 0.003898482620247966, 0.00882783109678569, 0.014945189167037706, 0.022393467220454093, 0.031286932872005575, 0.04169510925834998, 0.05362618927683272, 0.06701156038972575, 0.08169330242755682, 0.09741659909541572, 0.11382883673656312, 0.13048672437999825, 0.14687207025447396, 0.16241595024382866, 0.1765300044143878, 0.18864263131789072, 0.1982370608953941, 0.20488780808919338] + [0.20829193676209992] * 2 + [0.20488780808919338, 0.1982370608953941, 0.18864263131789072, 0.1765300044143878, 0.16241595024382866, 0.14687207025447396, 0.13048672437999825, 0.11382883673656312, 0.09741659909541572, 0.08169330242755682, 0.06701156038972575, 0.05362618927683272, 0.04169510925834998, 0.031286932872005575, 0.022393467220454093, 0.014945189167037706, 0.00882783109678569, 0.003898482620247966, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "x180_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "minus_x90_I_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, -0.001949241310123983, -0.004413915548392845, -0.007472594583518853, -0.011196733610227046, -0.015643466436002788, -0.02084755462917499, -0.02681309463841636, -0.033505780194862875, -0.04084665121377841, -0.04870829954770786, -0.05691441836828156, -0.06524336218999913, -0.07343603512723698, -0.08120797512191433, -0.0882650022071939, -0.09432131565894536, -0.09911853044769706, -0.10244390404459669] + [-0.10414596838104996] * 2 + [-0.10244390404459669, -0.09911853044769706, -0.09432131565894536, -0.0882650022071939, -0.08120797512191433, -0.07343603512723698, -0.06524336218999913, -0.05691441836828156, -0.04870829954770786, -0.04084665121377841, -0.033505780194862875, -0.02681309463841636, -0.02084755462917499, -0.015643466436002788, -0.011196733610227046, -0.007472594583518853, -0.004413915548392845, -0.001949241310123983, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "minus_x90_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "y90_I_wf_q2": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "y90_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, 0.001949241310123983, 0.004413915548392845, 0.007472594583518853, 0.011196733610227046, 0.015643466436002788, 0.02084755462917499, 0.02681309463841636, 0.033505780194862875, 0.04084665121377841, 0.04870829954770786, 0.05691441836828156, 0.06524336218999913, 0.07343603512723698, 0.08120797512191433, 0.0882650022071939, 0.09432131565894536, 0.09911853044769706, 0.10244390404459669] + [0.10414596838104996] * 2 + [0.10244390404459669, 0.09911853044769706, 0.09432131565894536, 0.0882650022071939, 0.08120797512191433, 0.07343603512723698, 0.06524336218999913, 0.05691441836828156, 0.04870829954770786, 0.04084665121377841, 0.033505780194862875, 0.02681309463841636, 0.02084755462917499, 0.015643466436002788, 0.011196733610227046, 0.007472594583518853, 0.004413915548392845, 0.001949241310123983, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "y180_I_wf_q2": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "y180_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, 0.003898482620247966, 0.00882783109678569, 0.014945189167037706, 0.022393467220454093, 0.031286932872005575, 0.04169510925834998, 0.05362618927683272, 0.06701156038972575, 0.08169330242755682, 0.09741659909541572, 0.11382883673656312, 0.13048672437999825, 0.14687207025447396, 0.16241595024382866, 0.1765300044143878, 0.18864263131789072, 0.1982370608953941, 0.20488780808919338] + [0.20829193676209992] * 2 + [0.20488780808919338, 0.1982370608953941, 0.18864263131789072, 0.1765300044143878, 0.16241595024382866, 0.14687207025447396, 0.13048672437999825, 0.11382883673656312, 0.09741659909541572, 0.08169330242755682, 0.06701156038972575, 0.05362618927683272, 0.04169510925834998, 0.031286932872005575, 0.022393467220454093, 0.014945189167037706, 0.00882783109678569, 0.003898482620247966, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "minus_y90_I_wf_q2": {
            "type": "arbitrary",
            "samples": [-0.0] * 40,
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "minus_y90_Q_wf_q2": {
            "type": "arbitrary",
            "samples": [0.0, -0.001949241310123983, -0.004413915548392845, -0.007472594583518853, -0.011196733610227046, -0.015643466436002788, -0.02084755462917499, -0.02681309463841636, -0.033505780194862875, -0.04084665121377841, -0.04870829954770786, -0.05691441836828156, -0.06524336218999913, -0.07343603512723698, -0.08120797512191433, -0.0882650022071939, -0.09432131565894536, -0.09911853044769706, -0.10244390404459669] + [-0.10414596838104996] * 2 + [-0.10244390404459669, -0.09911853044769706, -0.09432131565894536, -0.0882650022071939, -0.08120797512191433, -0.07343603512723698, -0.06524336218999913, -0.05691441836828156, -0.04870829954770786, -0.04084665121377841, -0.033505780194862875, -0.02681309463841636, -0.02084755462917499, -0.015643466436002788, -0.011196733610227046, -0.007472594583518853, -0.004413915548392845, -0.001949241310123983, 0.0],
            "is_overridable": False,
            "max_allowed_error": 0.0001,
        },
        "readout_wf_q2": {
            "type": "constant",
            "sample": 0.07,
        },
    },
    "digital_waveforms": {
        "ON": {
            "samples": [(1, 0)],
        },
    },
    "integration_weights": {
        "cosine_weights": {
            "cosine": [(1.0, 4000)],
            "sine": [(0.0, 4000)],
        },
        "sine_weights": {
            "cosine": [(0.0, 4000)],
            "sine": [(1.0, 4000)],
        },
        "minus_sine_weights": {
            "cosine": [(0.0, 4000)],
            "sine": [(-1.0, 4000)],
        },
        "rotated_cosine_weights_q1": {
            "cosine": [(1.0, 4000)],
            "sine": [(0.0, 4000)],
        },
        "rotated_sine_weights_q1": {
            "cosine": [(-0.0, 4000)],
            "sine": [(1.0, 4000)],
        },
        "rotated_minus_sine_weights_q1": {
            "cosine": [(0.0, 4000)],
            "sine": [(-1.0, 4000)],
        },
        "rotated_cosine_weights_q2": {
            "cosine": [(1.0, 4000)],
            "sine": [(0.0, 4000)],
        },
        "rotated_sine_weights_q2": {
            "cosine": [(-0.0, 4000)],
            "sine": [(1.0, 4000)],
        },
        "rotated_minus_sine_weights_q2": {
            "cosine": [(0.0, 4000)],
            "sine": [(-1.0, 4000)],
        },
    },
    "mixers": {
        "mixer_qubit_q1": [{'intermediate_frequency': 50000000.0, 'lo_frequency': 3950000000.0, 'correction': (1.0, 0.0, 0.0, 1.0)}],
        "mixer_qubit_q2": [{'intermediate_frequency': 75000000.0, 'lo_frequency': 3950000000.0, 'correction': (1.0, 0.0, 0.0, 1.0)}],
        "mixer_resonator": [
            {'intermediate_frequency': 75000000.0, 'lo_frequency': 6350000000.0, 'correction': (1.0, -0.0, -0.0, 1.0)},
            {'intermediate_frequency': 133000000.0, 'lo_frequency': 6350000000.0, 'correction': (1.0, -0.0, -0.0, 1.0)},
        ],
    },
}

