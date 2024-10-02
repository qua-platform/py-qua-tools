import logging
import json
from PyQt5.QtGui import QFont
import pyperclip
import traceback
from typing import List, Dict, Any

from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QApplication
from PyQt5.QtCore import Qt, QEvent

from .widgets import VoltageSourceDialog, VoltageConfigDialog, Separator

logger = logging.getLogger(__name__)


STATES = ["up_down", "left_right", "none"]


class VoltageControlDialog(QDialog):
    def __init__(self, parameters: List[Any], mini: bool = False):
        # if len(parameters) > 10:
        #     raise ValueError("Can use at most 10 voltage sources")
        super().__init__(flags=Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.parameters = parameters
        self.mini = mini
        self.index_keys = {}
        self.state_parameters = {state: [] for state in ["up_down", "left_right", "none"]}
        self.voltage_source_dialogs: Dict[str, VoltageSourceDialog] = {}
        self.initUI()
        rect = QApplication.desktop().screenGeometry()
        self.move(rect.height() * 7 // 10, rect.width() * 3 // 10)

    def initUI(self):
        if not self.mini:
            self.layout = QHBoxLayout()
        else:
            self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.config_widget = VoltageConfigDialog(mini=self.mini)
        self.config_widget.ramp_button.clicked.connect(lambda clicked: self.ramp_voltages())
        self.config_widget.ramp_button.clicked.connect(self._clear_focus)
        self.config_widget.ramp_zero_button.clicked.connect(lambda clicked: self.ramp_voltages(0))
        self.config_widget.ramp_zero_button.clicked.connect(self._clear_focus)

        self.config_widget.copy_button = QPushButton("Copy from clipboard")
        self.config_widget.copy_button.clicked.connect(self._copy_from_clipboard)
        self.config_widget.copy_button.clicked.connect(self._clear_focus)
        self.config_widget.layout.addWidget(self.config_widget.copy_button)

        self.layout.addWidget(self.config_widget)

        for k, parameter in enumerate(self.parameters):
            idx = k + 1
            self.layout.addWidget(Separator())
            voltage_source_dialog = VoltageSourceDialog(parameter, idx=idx, mini=self.mini)
            
            # Wrap the VoltageSourceDialog in a QHBoxLayout to make it expand properly
            dialog_layout = QHBoxLayout()
            dialog_layout.addWidget(voltage_source_dialog)
            dialog_layout.setContentsMargins(0, 0, 0, 0)
            
            self.layout.addLayout(dialog_layout)
            
            if idx < 10:
                Qt_index_key = getattr(Qt, f"Key_{idx}")
                self.index_keys[Qt_index_key] = voltage_source_dialog
            self.voltage_source_dialogs[parameter.name] = voltage_source_dialog

            voltage_source_dialog.state_change.connect(self.update_parameters)
            self.config_widget.ramp_button.clicked.connect(voltage_source_dialog._reset_val_textbox)
            self.config_widget.ramp_zero_button.clicked.connect(voltage_source_dialog._reset_val_textbox)

    def keyPressEvent(self, event):
        try:
            if event.key() in self.index_keys:
                # Change state of VoltageSource dialog
                self.index_keys[event.key()].cycle_state()
            elif event.key() == Qt.Key_Escape:
                # Clear focus
                self._clear_focus()
            elif event.key() == Qt.Key_Up:
                # Increase voltage for blue (up_down) dialogs
                self.increase_voltages(self.state_parameters["up_down"], self.config_widget.step["up_down"])
            elif event.key() == Qt.Key_Down:
                # Decrease voltage for blue (up_down) dialogs
                self.increase_voltages(self.state_parameters["up_down"], -self.config_widget.step["up_down"])
            elif event.key() == Qt.Key_Right:
                # Increase voltage for green (left_right) dialogs
                self.increase_voltages(self.state_parameters["left_right"], self.config_widget.step["left_right"])
            elif event.key() == Qt.Key_Left:
                # Decrease voltage for green (left_right) dialogs
                self.increase_voltages(self.state_parameters["left_right"], -self.config_widget.step["left_right"])
            elif event.key() == Qt.Key_W:
                self.config_widget.decrease_step("up_down")
            elif event.key() == Qt.Key_S:
                self.config_widget.increase_step("up_down")
            elif event.key() == Qt.Key_A:
                self.config_widget.increase_step("left_right")
            elif event.key() == Qt.Key_D:
                self.config_widget.decrease_step("left_right")
        except:
            traceback.print_exc()

    def increase_voltages(self, parameters, val):
        for parameter in parameters:
            self.voltage_source_dialogs[parameter.name].increase_voltage(val)

    def update_parameters(self):
        logger.debug("updating parameters")
        # Clear parameters from self.state_parameters
        self.state_parameters = {state: [] for state in STATES}

        # Iterate through VoltageSource dialogs and add them to state_parameters
        for dialog in self.voltage_source_dialogs.values():
            self.state_parameters[dialog.state].append(dialog.parameter)

    def _copy_from_clipboard(self, *args):
        clipboard_dict = json.loads(pyperclip.paste())
        for parameter_name, val in clipboard_dict.items():
            self.voltage_source_dialogs[parameter_name].val_textbox.setText(str(val))

    def _clear_focus(self):
        logger.debug("clearing focus")
        focus_widget = QApplication.focusWidget()
        if focus_widget is not None:
            focus_widget.clearFocus()
        for dialog in self.voltage_source_dialogs.values():
            dialog._reset_val_textbox()

    def ramp_voltages(self, voltage=None, parameters=None):
        if voltage is not None:
            if parameters is None:
                parameters = self.parameters

            for parameter in parameters:
                parameter(voltage)
        else:
            for voltage_source_dialog in self.voltage_source_dialogs.values():
                if voltage_source_dialog.modified_val:
                    voltage_source_dialog.set_voltage(voltage_source_dialog.val_textbox.text())

    def changeEvent(self, event):
        # Correctly determines it is activated, but cannot clear focus
        super().changeEvent(event)
        if event.type() == QEvent.ActivationChange:
            if self.windowState() == Qt.WindowNoState:
                self._clear_focus()
                for voltage_source_dialog in self.voltage_source_dialogs.values():
                    voltage_source_dialog._reset_val_textbox()
