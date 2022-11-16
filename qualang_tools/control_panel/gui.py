from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import datetime
from qualang_tools.control_panel import ManualOutputControl


class ControlPanelGui(QWidget):

    def __init__(self, config, ports=None):


        super(ControlPanelGui, self).__init__()

        self.test = True

        self.config = config

        self.analogue_outputs = {}
        self.digital_outputs = {}

        self.ports = ports

        if not self.test:

            if self.ports:
                self.manual_output_control = ManualOutputControl.ports(**ports, host="172.16.2.103", port=85)

            else:
                self.manual_output_control = ManualOutputControl(self.config, host="172.16.2.103", port=85)

        self.initialise_ui()
        self._perform_health_check()

        self.show()


    def initialise_ui(self):

        self.main_layout = QVBoxLayout()

        self.layout = QHBoxLayout()



        self.text_layout_widget = pg.LayoutWidget()
        self.general_buttons = QWidget()
        self.general_buttons_layout = QVBoxLayout()
        self.general_buttons.setLayout(self.general_buttons_layout)
        self.elements_layout = pg.LayoutWidget()

        self.setLayout(self.main_layout)

        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)

        self.main_layout.addLayout(self.layout, stretch=3)
        self.main_layout.addWidget(self.text_layout_widget, stretch=1)

        # self.layout.addWidget(self.left, stretch=2)
        self.layout.addWidget(self.general_buttons, stretch=1)
        self.layout.addWidget(self.elements_layout, stretch=5)

        self.middle_buttons_setup()
        self.text_layout_widget.addWidget(self.info_box)

        # self.set_up_tabs()
        self.set_up_main_page()

        self.setGeometry(50, 50, 1300, 800)
        self.setWindowTitle('Control panel')

        self.add_info_to_box('Control panel set up')


    def _turn_off_all_digital(self):
        for _, widget in self.digital_outputs.items():
            widget.togglebutton.setChecked(False)

    def _turn_off_all_analogue(self):
        for _, widget in self.analogue_outputs.items():
            widget.togglebutton.setChecked(False)

    def middle_buttons_setup(self):
        self.general_buttons_layout.addWidget(QFrame())

        self.turn_off_analogue_button = QPushButton('Turn off analogue outputs')
        self.turn_off_analogue_button.clicked.connect(self._turn_off_all_analogue)
        self.general_buttons_layout.addWidget(self.turn_off_analogue_button)

        self.turn_off_digital_button = QPushButton('Turn off digital outputs')
        self.turn_off_digital_button.clicked.connect(self._turn_off_all_digital)
        self.general_buttons_layout.addWidget(self.turn_off_digital_button)

        self.turn_off_all_button = QPushButton('Turn off all outputs')
        self.turn_off_all_button.clicked.connect(self._turn_off_all)
        self.general_buttons_layout.addWidget(self.turn_off_all_button)


        self.perform_health_check = QPushButton('Perform health check')
        self.perform_health_check.clicked.connect(self._perform_health_check)
        self.general_buttons_layout.addWidget(self.perform_health_check)

        self.close_all = QPushButton('Close QMs')
        self.close_all.clicked.connect(self._close_all)
        self.general_buttons_layout.addWidget(self.close_all)

        self.general_buttons_layout.addWidget(QFrame())

    def _close_all(self):
        self.manual_output_control.close()
        self.add_info_to_box('Closed all Quantum Machines')

    def add_info_to_box(self, text_to_add):
        string = f'{datetime.datetime.now().strftime("%H:%M:%S")}'.ljust(15, ' ') + f'{text_to_add}'

        self.info_box.append(string)

    def _perform_health_check(self):

        if not self.test:
            health_check_result = self.manual_output_control.qmm.perform_healthcheck()
            health_check_string = 'passed' if health_check_result else 'failed'
            self.add_info_to_box(f'Health check result: {health_check_string}')
        else:
            self.add_info_to_box('in test mode - cannot perform health check')

    def _turn_off_all(self):
        self._turn_off_all_digital()
        self._turn_off_all_analogue()

    def set_up_main_page(self):

        title = 'Ports' if self.ports is not None else 'Elements'

        self.elements_widget = pg.LayoutWidget()

        self.make_elements_page(title)
        self.elements_layout.addWidget(self.elements_widget)

    def make_elements_page(self, title):

        elements_per_row = 4

        analogue_elements, digital_elements = self.get_elements()
        title_widget = QLabel(f'<b>{title}</b>')
        title_widget.setMaximumHeight(30)
        self.elements_widget.addWidget(title_widget)
        self.elements_widget.nextRow()

        for i, analogue_element in enumerate(analogue_elements, 1):

            self.elements_widget.addWidget(self.make_analogue_element_widget(analogue_element))

            if i % elements_per_row == 0:
                self.elements_widget.nextRow()

        for j, digital_element in enumerate(digital_elements, 1):

            self.elements_widget.addWidget(self.make_digital_element_widget(digital_element))

            if (i + j) % elements_per_row == 0:
                self.elements_widget.nextRow()


    def make_analogue_element_widget(self, name):

        widget = AnalogueElementWidget(name, self)
        self.analogue_outputs[name] = widget
        return widget

    def make_digital_element_widget(self, name):

        widget = DigitalElementWidget(name, self)
        self.digital_outputs[name] = widget
        return widget

    def get_elements(self):

        if self.test:
            elements = self.config.get('elements')
            analogue_elements = []
            digital_elements = []

            for key, dict in elements.items():
                if 'digitalInputs' in dict.keys():
                    digital_elements.append(key)
                else:
                    analogue_elements.append(key)

            return analogue_elements, digital_elements

        else:
            return self.manual_output_control.analog_elements, self.manual_output_control.digital_elements


class AnalogueElementWidget(QGroupBox):

    def __init__(self, name, app_window):
        super(AnalogueElementWidget, self).__init__(name)
        self.name = name
        self.app_window = app_window
        self.setAlignment(Qt.AlignCenter)
        self.vbox = QVBoxLayout()
        self.vbox.setAlignment(Qt.AlignCenter)
        self.setLayout(self.vbox)

        self.amplitude_label = QLabel('Amplitude (mV)')

        self.amplitude = QDoubleSpinBox()
        self.amplitude.valueChanged.connect(self.set_amplitude)
        self.amplitude.setRange(-500, 500)
        self.amplitude.setSingleStep(1)

        self.frequency_label = QLabel('Frequency (MHz)')

        self.frequency = QDoubleSpinBox()
        self.frequency.valueChanged.connect(self.set_frequency)
        self.frequency.setRange(-300, 300)
        self.frequency.setSingleStep(int(1))

        self.togglebutton = QPushButton('Off')
        self.togglebutton.setCheckable(True)
        self.togglebutton.setChecked(False)

        self.vbox.addWidget(self.amplitude_label)
        self.vbox.addWidget(self.amplitude)
        self.vbox.addWidget(self.frequency_label)
        self.vbox.addWidget(self.frequency)
        self.vbox.addWidget(self.togglebutton)

        self.togglebutton.toggled.connect(self.toggle_element_on_off)

    def set_amplitude(self):
        self.app_window.manual_output_control.set_amplitude(self.name, self.amplitude.value() * 1e-3) # given in mv
        # self.app_window.add_info_to_box(f'{self.name} set to {self.amplitude.value()} mV')

    def set_frequency(self):
        self.app_window.manual_output_control.set_frequency(self.name, self.frequency.value() * 1e6)
        # self.app_window.add_info_to_box(f'{self.name} set to {self.frequency.value()} MHz')

    def toggle_element_on_off(self):
        if self.togglebutton.isChecked():
            self.togglebutton.setText('On')

            if not self.app_window.test:
                print(self.app_window.manual_output_control.analog_status())
                self.set_amplitude()
                self.set_frequency()
                self.app_window.manual_output_control.turn_on_element(self.name)

            self.app_window.add_info_to_box(f'{self.name} turned on with amplitude {self.amplitude.value()}'
                                            f' mV and frequency {self.frequency.value()} MHz')


        else:
            self.togglebutton.setText('Off')

            if not self.app_window.test:
                self.app_window.manual_output_control.turn_off_elements(self.name)

            self.app_window.add_info_to_box(f'{self.name} turned off')


class DigitalElementWidget(QGroupBox):

    def __init__(self, name, app_window):
        super(DigitalElementWidget, self).__init__(name)


        self.name = name
        self.app_window = app_window
        self.setAlignment(Qt.AlignCenter)
        self.vbox = QVBoxLayout()
        self.vbox.setAlignment(Qt.AlignCenter)
        self.setLayout(self.vbox)

        self.togglebutton = QPushButton('Off')
        self.togglebutton.setCheckable(True)
        self.togglebutton.setChecked(False)

        self.vbox.addWidget(self.togglebutton)

        self.togglebutton.toggled.connect(self.toggle_element_on_off)

    def toggle_element_on_off(self):

        # currently on
        if self.togglebutton.isChecked():
            self.togglebutton.setText('On')

            if not self.app_window.test:
                self.app_window.manual_output_control.digital_on(self.name)

            self.app_window.add_info_to_box(f'{self.name} turned on')


        else:
            self.togglebutton.setText('Off')

            if not self.app_window.test:
                self.app_window.manual_output_control.digital_off(self.name)

            self.app_window.add_info_to_box(f'{self.name} turned off')



if __name__ == '__main__':
    qop_ip = "172.16.2.103"
    readout_time = 256  # ns

    config = {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.0},  # G1
                                   2: {"offset": 0.0},  # G2
                                   3: {"offset": 0.0},  # I qubit
                                   4: {"offset": 0.0},  # Q qubit
                                   5: {"offset": 0.0},  # I resonator
                                   6: {"offset": 0.0},  # Q resonator
                                   },
                "digital_outputs":
                    {i: {} for i in range(1, 11)},

                "analog_inputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                },
            },

        },
        "elements": {
            "G1_sticky": {
                "singleInput": {"port": ("con1", 1)},
                "hold_offset": {"duration": 12},
                "operations": {
                    "sweep": "sweep",
                },
            },
            "G2_sticky": {
                "singleInput": {"port": ("con1", 2)},
                "hold_offset": {"duration": 12},
                "operations": {
                    "sweep": "sweep",
                },
            },
            "G1": {
                "singleInput": {"port": ("con1", 1)},
                "operations": {
                    "sweep": "sweep",
                },
            },
            "G2": {
                "singleInput": {"port": ("con1", 2)},
                "operations": {
                    "sweep": "sweep",
                },
            },
            "RF": {
                "singleInput": {"port": ("con1", 3)},
                "time_of_flight": 200,
                "smearing": 0,
                "intermediate_frequency": 100e6,
                "outputs": {"out1": ("con1", 1)},
                "operations": {"measure": "measure"},
            },
            'trigger_x': {
                "digitalInputs": {
                    "trigger_qdac": {
                        'port': ('con1', 1),
                        'delay': 0,
                        'buffer': 0
                    }
                },
                'operations': {
                    'trig': 'trigger'
                }
            },
            'trigger_y': {
                "digitalInputs": {
                    "trigger_qdac": {
                        'port': ('con1', 2),
                        'delay': 0,
                        'buffer': 0
                    }
                },
                'operations': {
                    'trig': 'trigger'
                }
            },

        },
        "pulses": {
            "sweep": {
                "operation": "control",
                "length": 100,
                "waveforms": {
                    "single": "sweep",
                },
            },
            "trigger": {
                "operation": "control",
                "length": 100,
                "digital_marker": "ON",
            },
            "measure": {
                "operation": "measurement",
                "length": readout_time,
                "waveforms": {"single": "measure"},
                "digital_marker": "ON",
                "integration_weights": {
                    "cos": "cos",
                    "sin": "sin",
                },
            },
        }
        ,
        "waveforms": {
            "sweep": {"type": "constant", "sample": 0.5},
            "measure": {"type": "constant", "sample": 0.001},
            "zero": {"type": "constant", "sample": 0.00},
        },
        "digital_waveforms": {"ON": {"samples": [(1, 0)]}},
        "integration_weights": {
            "cos": {
                "cosine": [(1.0, readout_time)],
                "sine": [(0.0, readout_time)],
            },
            "sin": {
                "cosine": [(0.0, readout_time)],
                "sine": [(1.0, readout_time)],
            },
        },
    }

    def main():
        app = pg.mkQApp()
        # loader = multiQubitReadoutPresenter(results)
        loader = ControlPanelGui(config)#, ports={'analog_ports': [1, (4, 5), 6]})
        pg.exec()

    main()