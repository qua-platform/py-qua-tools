import logging
from typing import Dict, Any
from functools import partial
import traceback

from PyQt5.QtGui import QPalette, QFont, QColor
from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QSizePolicy,
    QApplication,
    QStyleFactory,
)
from PyQt5.QtCore import Qt, pyqtSignal

from .utils import get_exponent, get_first_digit

logger = logging.getLogger(__name__)


text_font = "Arial"
font_size = 16


class VoltageSourceDialog(QFrame):
    state_change = pyqtSignal()

    def __init__(self, parameter: Any, idx: int = 1, mini: bool = True):
        super().__init__()
        self.parameter = parameter
        self.idx = idx
        self.mini = mini
        self._state = "none"
        self.min_step = 0.0001
        self.max_step = 0.05
        self.modified_val = False
        self.setMaximumWidth(170)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #f0f0f0;
                border-radius: 10px;
                # padding: 10px;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 5px;
                # padding: 3px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.initUI()
        self.name_label.mousePressEvent = self.cycle_state

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state not in ["none", "up_down", "left_right"]:
            logger.debug(f"State {state} not recognized")

        else:
            # Create palette for name color customization
            name_palette = QPalette()

        if state == "none":
            name_palette.setColor(QPalette.Foreground, Qt.black)
        elif state == "up_down":
            name_palette.setColor(QPalette.Foreground, Qt.blue)
        elif state == "left_right":
            name_palette.setColor(QPalette.Foreground, Qt.darkGreen)
        self._state = state
        self.name_label.setPalette(name_palette)

        # Emit signal that state has changed
        self.state_change.emit()

    def cycle_state(self, *args, **kwargs):
        logger.debug(f"Cycling gate {self.parameter.name}")
        if self.state == "none":
            self.state = "up_down"
        elif self.state == "up_down":
            self.state = "left_right"
        else:
            self.state = "none"

    def initUI(self):
        layout = QVBoxLayout()
        if self.mini:
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            layout.setContentsMargins(5, 0, 5, 0)
        self.setLayout(layout)

        # Set parameter name
        self.name_label = QLabel(f"{self.idx}: {self.parameter.name}")
        self.name_label.setAlignment(Qt.AlignCenter)

        if not self.mini:
            self.name_label.setFont(QFont("Arial", 16, QFont.Bold))
            layout.addWidget(self.name_label)

        # Add editable voltage
        val_hbox = QHBoxLayout()
        layout.addLayout(val_hbox)

        if not self.mini:
            val_descr_label = QLabel("Val:")
            val_descr_label.setFont(QFont(text_font, font_size))
            val_hbox.addWidget(val_descr_label)
        else:
            self.name_label.setFont(QFont(text_font, font_size))
            val_hbox.addWidget(self.name_label)

        self.val_textbox = QLineEdit(f"{self.parameter.get_latest():.5g}")
        self.val_textbox.setAlignment(Qt.AlignCenter)
        self.val_textbox.setFont(QFont(text_font, font_size))
        self.val_textbox.returnPressed.connect(lambda: self.set_voltage(self.val_textbox.text()))
        val_hbox.addWidget(self.val_textbox)

        val_units_label = QLabel("V")
        val_units_label.setFont(QFont(text_font, font_size))
        val_hbox.addWidget(val_units_label)

        # Add current val
        self.current_val_label = QLabel(f"")
        self.current_val_label.setAlignment(Qt.AlignCenter)
        self.current_val_label.setFont(QFont(text_font, font_size))
        layout.addWidget(self.current_val_label)

        self.val_textbox.textChanged.connect(self._val_textbox_changed)

        # Add voltage buttons
        if not self.mini:
            self.val_grid = QGridLayout()
            self.val_grid.setHorizontalSpacing(0)
            self.val_grid.setVerticalSpacing(0)
            layout.addLayout(self.val_grid)
            self.val_buttons = {}
            for column_idx, scale in enumerate([100, 10, 1]):
                for row_idx, sign in enumerate([1, -1]):
                    val = sign * scale
                    button = QPushButton(f"{['-','+'][sign==1]}{scale} mV")
                    self.val_grid.addWidget(button, row_idx, column_idx + 1)
                    width = button.fontMetrics().boundingRect(f"+100 mV").width() + 7
                    button.setMaximumWidth(width)
                    button.clicked.connect(partial(self.increase_voltage, val / 1000))
                    self.val_buttons[val] = button

            # Modify button styles
            for button in self.val_buttons.values():
                button.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """
                )

    def _val_textbox_changed(self):
        try:
            textbox_val = float(self.val_textbox.text())
            self.modified_val = textbox_val != self.parameter.get_latest()
        except:
            self.modified_val = True
        if self.modified_val:
            self.val_textbox.setStyleSheet("color: rgb(255, 0, 0);")
            if self.current_val_label.text() == "":
                self.current_val_label.setText(f"Current val: {self.parameter.get_latest()}")
        else:
            pass
            # self._reset_val_textbox()

    def set_voltage(self, val):
        try:
            val = round(float(val), 6)
            self.parameter(val)
        except:
            pass
        self._reset_val_textbox()

    def _reset_val_textbox(self):
        self.modified_val = False
        self.val_textbox.setText("{:.5g}".format(self.parameter.get_latest()))
        self.current_val_label.setText("")
        self.val_textbox.setStyleSheet("color: rgb(0, 0, 0);")

    def increase_voltage(self, increment):
        self.set_voltage(self.parameter.get_latest() + increment)


class VoltageConfigDialog(QFrame):
    def __init__(self, mini: bool = False):
        super().__init__()
        self.mini = mini
        self.step = {"up_down": 0.001, "left_right": 0.001}
        self.min_step = 0.0001
        self.max_step = 0.05
        self.setStyleSheet(
            """
            QFrame {
                background-color: #e6e6e6;
                # border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 3px;
            }
            QPushButton {
                background-color: #008CBA;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #007B9A;
            }
        """
        )
        self.initUI()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Add up, down, left, right color indication
        if not self.mini:
            key_grid = QGridLayout()
            key_grid.setVerticalSpacing(0)
            for k, (color, keys) in enumerate(
                [("blue", [("up", (0, 1)), ("down", (1, 1))]), ("darkGreen", [("left", (1, 0)), ("right", (1, 2))])]
            ):
                for key, pos in keys:
                    key_label = QLabel(key)
                    key_label.setAlignment(Qt.AlignCenter)
                    key_label.setFont(QFont(text_font, font_size, QFont.Bold))

                    key_palette = QPalette()
                    key_palette.setColor(QPalette.Foreground, getattr(Qt, color))
                    key_label.setPalette(key_palette)

                    key_grid.addWidget(key_label, *pos)
            self.layout.addLayout(key_grid)

            self.layout.addStretch(1)

            # Add step sizes

            step_label = QLabel("Step:")
            step_label.setAlignment(Qt.AlignCenter)
            step_label.setFont(QFont(text_font, font_size, QFont.Bold))
            self.layout.addWidget(step_label)

        step_hbox = QHBoxLayout()
        self.layout.addLayout(step_hbox)

        self.step_textbox = {}
        for k, (state, color) in enumerate([("up_down", "blue"), ("left_right", "darkGreen")]):
            step_hbox.addStretch(0.8)
            self.step_textbox[state] = QLineEdit(str(self.step[state]))
            self.step_textbox[state].setMaximumWidth(55)
            step_hbox.addWidget(self.step_textbox[state])
            self.step_textbox[state].returnPressed.connect(lambda: self.set_step(state, self.step_textbox.text()))
            step_unit_label = QLabel("V")
            if k == 0:
                step_unit_label.setContentsMargins(0, 0, 20, 0)
            step_hbox.addWidget(step_unit_label)

            for widget in [step_unit_label, self.step_textbox[state]]:
                # widget.setFont(QFont(text_font, 16, QFont.Bold))
                widget.setStyleSheet(f"color: {color};")

        self.layout.addStretch(1)

        # Add ramp buttons
        ramp_hbox = QHBoxLayout()
        self.ramp_button = QPushButton("Ramp")
        self.ramp_zero_button = QPushButton("Ramp to zero")
        ramp_hbox.addWidget(self.ramp_button)
        ramp_hbox.addWidget(self.ramp_zero_button)
        self.layout.addLayout(ramp_hbox)

        self.layout.addStretch(1)

    def set_step(self, state, val):
        try:
            val = round(float(val), 6)
            if val > self.max_step:
                val = self.max_step
            elif val < self.min_step:
                val = self.min_step
            self.step[state] = val
            self.step_textbox[state].setText(str(val))
            self._clear_focus()
        except:
            traceback.print_exc()

    def increase_step(self, state):
        current_val = self.step[state]
        exponent = get_exponent(current_val)
        first_digit = get_first_digit(current_val)
        if first_digit == 1:
            self.set_step(state, 2 * 10**exponent)
        elif first_digit < 4:
            self.set_step(state, 5 * 10**exponent)
        else:
            self.set_step(state, 1 * 10 ** (exponent + 1))

    def decrease_step(self, state):
        current_val = self.step[state]
        exponent = get_exponent(current_val)
        first_digit = get_first_digit(current_val)
        if first_digit == 1:
            self.set_step(state, 5 * 10 ** (exponent - 1))
        elif first_digit < 4:
            self.set_step(state, 1 * 10**exponent)
        else:
            self.set_step(state, 2 * 10**exponent)

    def _clear_focus(self):
        focus_widget = QApplication.focusWidget()
        if focus_widget is not None:
            focus_widget.clearFocus()


class Separator(QFrame):
    def __init__(self, mode: str = "vertical"):
        super().__init__()
        frame_shape = QFrame.VLine if mode == "vertical" else QFrame.HLine
        self.setFrameShape(frame_shape)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.setLineWidth(2)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #cccccc;
            }
        """
        )
