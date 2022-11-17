import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import time
import numpy as np


class ActiveResetGUI(QWidget):
    def __init__(self, reset_results_dictionary):
        super(ActiveResetGUI, self).__init__()

        self.reset_results_dictionary = reset_results_dictionary
        self.num_qubits = len(list(self.reset_results_dictionary.values())[0])

        self._initialise_ui()

        self._populate_list()

        self.hbox.addWidget(self.information)
        self.hbox.addWidget(self.plot_area)

        self.setLayout(self.hbox)
        self.show()

    def _initialise_ui(self):
        """
        Initialise the user interface of the GUI. Sets the colour scheme, qapplication style, and the geometry
        of the window. The two main parts of the GUI are the info_area (on the left) and the plot_area (on the right).

        The info area contains the dropdown list so we can select a specific qubit, a table with information about the
        qubit being looked at, a legend for the colours on the plots, and check boxes to select which plots are being
        shown. The plot area contains a column for each readout type, with each of these boxes containing rotated
        IQ blobs and a histogram of the I-projected data.

        @return:
        """

        self.hbox = QHBoxLayout(self)

        self.ground_state_colour = (100, 149, 237)
        self.excited_state_colour = (255, 185, 15)

        QApplication.setStyle(QStyleFactory.create("Cleanlooks"))

        self.setGeometry(100, 100, 1200, 500)
        self.setWindowTitle("Qubit reset comparison")

        self._initialise_info_area()
        self._initialise_plot_area()

        # connect buttons
        for check_box in self.check_boxes:
            check_box.toggled.connect(self.toggle_views)
            check_box.setChecked(True)

        self.qubit_list.currentIndexChanged.connect(self.update_plots)

        self.show()

    def _initialise_plot_area(self):
        """
        Sets up the plot area. It's a horizontal box layout, meaning widgets are added in a row until a new row is called.
        For each type of reset (name in self.reset_results_dictionary.keys()), we add a column containing two plots:
        the IQ blob and the 1d histogram.
        """

        self.plot_area = QWidget()
        self.plot_layout = QHBoxLayout()
        self.plot_area.setLayout(self.plot_layout)

        # plot_regions are each two-plot window for a specific reset type
        self.plot_regions = []

        for name in self.reset_results_dictionary.keys():
            plot_region = pg.GraphicsLayoutWidget()
            self.plot_layout.addWidget(plot_region, stretch=1)
            self.plot_regions.append(plot_region)
            plot_region.addItem(
                pg.PlotItem(
                    title=f'<font size="+1"><b>{name}</b></font>'.replace("_", " ")
                ),
                0,
                0,
            )
            plot_region.addItem(pg.PlotItem(), 1, 0)

    def _initialise_info_area(self):
        """
        Sets up the info area with the required widgets. It's a vbox layout which means widgets are added row-by-row in
        a single column until a new column is called.
        """

        # create some widgets
        self.information = QWidget()
        self.information_layout = QVBoxLayout()
        self.information.setLayout(self.information_layout)

        self.qubit_list = QComboBox()

        self.check_boxes = []
        for key in self.reset_results_dictionary.keys():
            self.check_boxes.append(QCheckBox(str(key).replace("_", " ")))

        self.info_box = pg.TableWidget(3, len(self.reset_results_dictionary))
        self.set_table()

        self.information_layout.addWidget(self.qubit_list)
        self.information_layout.addWidget(self.info_box)

        self.info_box.horizontalHeader().setVisible(False)
        self.info_box.verticalHeader().setVisible(False)

        # width of table + 3 pixels means we do not get a horizontal scroll bar. +3 to prevent
        # wider characters bringing a scroll bar in
        table_size = self.info_box.sizeHint()
        self.info_box.setMaximumHeight(int(table_size.height()))
        self.info_box.setMinimumWidth(int(table_size.width()))
        self.info_box.setMaximumWidth(int(table_size.width()))
        self.qubit_list.setMaximumWidth(int(table_size.width()))
        self.info_box.setShowGrid(False)

        self.ground_state_label = QLabel("Ground state")
        self.excited_state_label = QLabel("Excited state")

        self.ground_state_label.setAlignment(Qt.AlignCenter)
        self.excited_state_label.setAlignment(Qt.AlignCenter)

        self.ground_state_label.setStyleSheet(
            f"background-color:rgb{self.ground_state_colour}; border-radius:5px"
        )
        self.excited_state_label.setStyleSheet(
            f"background-color:rgb{self.excited_state_colour}; border-radius:5px"
        )

        self.information_layout.addWidget(self.ground_state_label)
        self.information_layout.addWidget(self.excited_state_label)

        self.excited_state_label.setMaximumWidth(int(table_size.width()))
        self.ground_state_label.setMaximumWidth(int(table_size.width()))

        self.excited_state_label.setMaximumHeight(80)
        self.ground_state_label.setMaximumHeight(80)

        for check_box in self.check_boxes:
            self.information_layout.addWidget(check_box)

        self.information_layout.addWidget(QFrame())

    def toggle_views(self):
        """
        All check boxes are connected to this function so whenever any of them are changed, it is called. This saves
        having multiple functions at very low time overhead. If a checkbox isChecked()==True, this shows the respective
        plots in the plot area. If it is not checked, the plots it corresponds to are hidden.
        """

        for check_box, plot_region in zip(self.check_boxes, self.plot_regions):
            if check_box.isChecked():
                plot_region.show()
            else:
                plot_region.hide()

    def generate_table(self):
        """
        Data in the QTableWidget is added in rows as a nested list. To keep the headers large I have added them as
        the first row of the table and turned off the actual headers.

        @return: the list of lists representing rows of the table.
        """
        overall_table = [["", "Fidelity (%)", "Time (ns)"]]

        for reset_type, results_datasets in self.reset_results_dictionary.items():
            qubit_data = results_datasets[self.qubit_list.currentIndex()]
            row = [
                reset_type,
                f"{qubit_data.fidelity:.2f}",
                f"{qubit_data.runtime:.2f}",
            ]
            overall_table.append(row)

        return overall_table

    def set_table(self):
        """
        Sets the values for the table in the info area.
        """
        data = self.generate_table()
        self.info_box.setData(data)

    def plot_to_scatter(self, scatter_plot, result_dataclass):
        """
        Adds the required data (IQ blobs) from the result_dataclass to the scatter_plot object
        @param scatter_plot: the plot onto which the data will be added
        @param result_dataclass: the dataclass containing the IQ DATA
        """

        rotated_data_g = pg.ScatterPlotItem(
            result_dataclass.ig_rotated,
            result_dataclass.qg_rotated,
            brush=(*self.ground_state_colour, 100),
            symbol="s",
            size="2",
            pen=pg.mkPen(None),
        )

        rotated_data_e = pg.ScatterPlotItem(
            result_dataclass.ie_rotated,
            result_dataclass.qe_rotated,
            brush=(*self.excited_state_colour, 100),
            symbol="s",
            size="2",
            pen=pg.mkPen(None),
        )

        scatter_plot.addItem(rotated_data_g)
        scatter_plot.addItem(rotated_data_e)

        scatter_plot.addLine(
            x=result_dataclass.threshold,
            label=f"{result_dataclass.threshold:.2f}, θ={(np.random.rand() * 1000) % 90:.2f}°",
            labelOpts={"position": 0.9},
            pen={"color": "white", "dash": [20, 20]},
        )

        scatter_plot.setAspectLocked()
        return scatter_plot

    def plot_to_histogram(self, histogram_plot, result_dataclass):
        """
        Processes and adds the 1d histogram data stored in result_dataclass to the histogram_plot object
        @param histogram_plot: histogram plot onto which the data will be added
        @param result_dataclass: dataclass containing the IQ blob data that will then be processed into histogram data
        @return:
        """

        y, x = np.histogram(
            result_dataclass.ig_rotated, bins=80
        )  # , bins=np.linspace(-3, 8, 80))
        y2, x2 = np.histogram(
            result_dataclass.ie_rotated, bins=80
        )  # , bins=np.linspace(-3, 8, 80))

        histogram_plot.plot(
            x,
            y,
            stepMode="center",
            fillLevel=0,
            fillOutline=True,
            brush=(*self.ground_state_colour, 200),
            pen=pg.mkPen(None),
        )
        histogram_plot.plot(
            x2,
            y2,
            stepMode="center",
            fillLevel=0,
            fillOutline=True,
            brush=(*self.excited_state_colour, 200),
            pen=pg.mkPen(None),
        )

        histogram_plot.addLine(
            x=result_dataclass.threshold,
            label=f"{result_dataclass.threshold:.2f}",
            labelOpts={"position": 0.95},
            pen={"color": "white", "dash": [20, 20]},
        )

        return histogram_plot

    def update_plots(self):
        """
        Updater function that selects the correct data values to present on the screen when a different qubit is
        selected from the qubit list
        """

        qubit_id = self.qubit_list.currentIndex()

        for plot_region, (data_key, data_list) in zip(
            self.plot_regions, self.reset_results_dictionary.items()
        ):
            data = data_list[qubit_id]
            scatter = plot_region.getItem(0, 0)
            histogram = plot_region.getItem(1, 0)

            scatter.clear()
            histogram.clear()

            self.plot_to_scatter(scatter, data)
            self.plot_to_histogram(histogram, data)

        self.set_table()

    def _populate_list(self):
        """
        Populates the dropdown list with the qubit names given as the name attributes of the result dataclasses.
        """

        key = list(self.reset_results_dictionary.keys())[0]

        dataclasses = self.reset_results_dictionary[key]

        for result in dataclasses:
            self.qubit_list.addItem(result.name)


def launch_reset_gui(data_dictionary):

    app = QApplication(sys.argv)
    program = ActiveResetGUI(data_dictionary)
    app.exec_()
