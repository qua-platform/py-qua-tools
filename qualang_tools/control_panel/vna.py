"""calling function libraries"""
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
import numpy as np
import matplotlib.pyplot as plt


class VNA:
    """
    Configures the OPX as a vector network analyzer (VNA) allowing to quickly perform basic VNA measurements:
        - S-parameter (S11 and S12)
        - Spectrum analyzer
    """

    def __init__(self, config: dict, element: str, operation: str, Q: int = None):
        """
        Gets a QUA configuration file and configure the OPX to perform VNA measurements.

        :param config: configuration file
        :param element: name of the element to be measured (defined in the configuration)
        :param operation: name of the measurement operation associated to the element (defined in the configuration)
        :param Q: value of the resonator quality factor for estimating the cavity relaxation time (optional).
        """
        # Check inputs errors
        if not (element in config["elements"]):
            raise KeyError(f"element {element} is not in the config")
        elif not (operation in config["elements"][element]["operations"]):
            raise KeyError(f"Operation {operation} is not in the config")

        self.qmm = None
        self.config = config
        self.element = element
        self.operation = operation
        self.inputs = [
            config["elements"][element]["outputs"][out][1]
            for out in config["elements"][element]["outputs"].keys()
        ]

        if Q is not None:
            self.relax_time = int(
                Q
                / (
                    2
                    * np.pi
                    * config["elements"][element]["mixInputs"]["lo_frequency"]
                    * 1e-9
                )
                / 4
            )
        else:
            self.relax_time = 4
        self.measurements = []
        self.calibration = {}
        self.meas_list = []
        self.results = {}

    def __str__(self):
        s = f"\nVNA mode initialized for element '{self.element}'"
        s += f" and operation '{self.operation}'"
        s += f" with {len(self.measurements)} measurements:\n"
        for M in self.measurements:
            s += str(M) + "\n"
        return s

    def _add_S_measurement(self, measurement: str, outputs, int_weights):
        """
        Add measurement outputs and integration weights and initialize self.results.

        :param measurement: name of the measurement type ('S11' or 'S21')
        :param outputs: name of the output port of the element (defined in the configuration)
        :param int_weights:  name of the integration weights used for integration
        :return: None
        """
        self.measurements.append(
            {
                "measurement": measurement,
                "integration_weights": int_weights,
                "outputs": outputs,
            }
        )
        self.meas_list.append(measurement)
        self.results[measurement] = {"f": [], "S": [], "phase": []}

    def add_envelope_detector(self, measurement: str, outputs: str, int_weights: str):
        """
        Adds an S-measurement down-converted with an envelope detector.

        :param measurement: name of the measurement type ('S11' or 'S21')
        :param outputs: name of the output port of the element (defined in the configuration). For instance outputs="out1"
        :param int_weights: name of the integration weights used for integration. For instance int_weights="Wc"
        :return: None
        """
        # Check inputs errors
        if not (outputs in self.config["elements"][self.element]["outputs"]):
            raise KeyError(f"Output '{outputs}' is not in the config")
        elif not (
            int_weights
            in self.config["pulses"][
                self.config["elements"][self.element]["operations"][self.operation]
            ]["integration_weights"]
        ):
            raise KeyError(f"Integration weights '{int_weights}' is not in the config")
        elif not (measurement in ["S11", "S21"]):
            raise KeyError(
                f"Measurement '{measurement}' not implemented yet, must be in ['S11', 'S21']"
            )

        self._add_S_measurement(measurement, outputs, int_weights)
        self.measurements[-1]["down_converter"] = "ED"

    def add_IR_mixer(self, measurement: str, outputs: str, int_weights: list):
        """
        Adds an S-measurement down-converted with an image rejection mixer.

        :param measurement: name of the measurement type ('S11' or 'S21')
        :param outputs: name of the output port of the element (defined in the configuration). for instance: outputs="out1"
        :param int_weights: names of the integration weights used for integration. For instance int_weights=["Wc", "Ws"]
        :return: None
        """
        # Check inputs errors
        if not (outputs in self.config["elements"][self.element]["outputs"]):
            raise KeyError(f"Output '{outputs}' is not in the config")
        elif not (
            all(
                [
                    iw
                    in self.config["pulses"][
                        self.config["elements"][self.element]["operations"][
                            self.operation
                        ]
                    ]["integration_weights"]
                    for iw in int_weights
                ]
            )
        ):
            raise KeyError(f"Integration weights '{int_weights}' are not in the config")
        elif not (measurement in ["S11", "S21"]):
            raise KeyError(
                f"Measurement '{measurement}' not implemented yet, must be in ['S11', 'S21']"
            )

        self._add_S_measurement(measurement, outputs, int_weights)
        self.measurements[-1]["down_converter"] = "IR"

    def add_IQ_mixer(self, measurement: str, outputs: list, int_weights: list):
        """
        Adds an S-measurement down-converted with an IQ mixer.

        :param measurement: name of the measurement type ('S11' or 'S21')
        :param outputs: name of the output ports of the element (defined in the configuration). For instance out=["out1", "out2"]
        :param int_weights: names of the integration weights used for integration. for instance int_weights=[["Wc", "Ws"], ["-Ws", "Wc"]]
        :return: None
        """
        # Check inputs errors
        if len(outputs) != 2:
            raise TypeError(f"Output '{outputs}' must be a list of two  outputs.")
        if np.array(int_weights).shape != (2, 2):
            raise TypeError(f"Output '{int_weights}' must be a 2x2 list.")
        if not (
            all(
                [
                    out in self.config["elements"][self.element]["outputs"]
                    for out in outputs
                ]
            )
        ):
            raise KeyError(f"Integration weights '{outputs}' are not in the config")
        elif not (
            all(
                [
                    iw
                    in self.config["pulses"][
                        self.config["elements"][self.element]["operations"][
                            self.operation
                        ]
                    ]["integration_weights"]
                    for iw in np.array(int_weights).reshape(1, 4)[0]
                ]
            )
        ):
            raise KeyError(f"Integration weights '{int_weights}' are not in the config")
        elif not (measurement in ["S11", "S21"]):
            raise KeyError(
                f"Measurement '{measurement}' not implemented yet, must be in ['S11', 'S21']"
            )

        self._add_S_measurement(measurement, outputs, int_weights)
        self.measurements[-1]["down_converter"] = "IQ"

    def add_spectrum_analyzer(self, bandwidth: int):
        """
        Add the spectrum analyzer measurement which will store its results under self.results["SA"]:
            - 'raw': raw_adc data [V]
            - 'fft': fft data [V]
            - 'f': frequency [Hz]

        :param bandwidth: Spectrum analyzer bandwidth [Hz]
        :return: None
        """
        self.meas_list.append("spectrum_analyzer")
        self.calibration["SA"] = {"pulse_length": int(2e9 / bandwidth)}
        self.results["SA"] = {"f": [], "raw": [], "fft": []}

    def _define_spectrum_analyzer(self, n_avg: int):
        """
        Define the spectrum analyzer QUA program

        :param n_avg: number of iterations for averaging.
        :return: Corresponding QUA program
        """
        with program() as Prog_spectro:
            n = declare(int)
            adc_st = declare_stream(adc_trace=True)

            with for_(n, 0, n < n_avg, n + 1):
                measure(self.operation, self.element, adc_st)

            with stream_processing():
                if 1 in self.inputs:
                    adc_st.input1().average().save("adc1_raw")
                    adc_st.input1().fft(output="abs").average().save("adc1_fft")
                if 2 in self.inputs:
                    adc_st.input2().average().save("adc2_raw")
                    adc_st.input2().fft(output="abs").average().save("adc2_fft")

        return Prog_spectro

    def _run_spectrum_analyzer(self, qm, n_avg: int):
        """
        Record raw adc and corresponding FFT.

        :param qm: opened quantum machine
        :param n_avg: number of averaged iterations
        :return: None
        """

        # Execute spectrum_analyzer calibration program
        job = qm.execute(self._define_spectrum_analyzer(n_avg))
        # Get results
        res_handles = job.result_handles
        res_handles.wait_for_all_values()
        fft = []
        raw = []
        for inp in self.inputs:
            # fft data
            # When doing fft, the frequency goes from -1/(2*dt) to 1/(2*dt) in jumps of  1/(maxT).
            # In our case, dt = 1ns and maxT = pulse_len.
            # In addition, the resulting fft data is shifted such that the order is [0:1/(2*dt), -1/(2*dt):0].
            # Here, instead of shifting the data, we just look only at the positive part.
            fft.append(res_handles.get(f"adc{inp}_fft").fetch_all())
            # raw data
            raw.append(res_handles.get(f"adc{inp}_raw").fetch_all())
        # Reformat fft and raw data
        fft = np.array(fft)
        raw = np.array(raw)
        # Store data in self.results
        self.results["SA"]["raw"] = raw / 4096
        self.results["SA"]["fft"] = (
            fft / 4096 * (2 / self.calibration["SA"]["pulse_length"])
        )
        self.results["SA"]["f"] = np.arange(
            0, 0.5 * 1e9, 1e9 / self.calibration["SA"]["pulse_length"]
        )

    def _define_single_measurement(self, sequence: dict, freq_sweep: dict, n_avg: int):
        """
        Define a single S-measurement as a QUA program

        :param sequence: single measurement sequence
        :param freq_sweep: dictionary containing the frequency sweep information (fmin, fmax, step)
        :param n_avg: number of averaged iterations
        :return: corresponding QUA program
        """
        n_steps = (freq_sweep["f_max"] - freq_sweep["f_min"]) / freq_sweep["step"] + 1

        with program() as Prog_single:
            n = declare(int)
            f = declare(int)
            I = declare(fixed)
            Q = declare(fixed)
            I_st = declare_stream()
            Q_st = declare_stream()
            f_st = declare_stream()

            # Repeat the sequence n_avg times for averaging purposes
            with for_(n, 0, n < n_avg, n + 1):
                # Frequency sweep
                with for_(
                    f,
                    freq_sweep["f_min"],
                    f < freq_sweep["f_max"] + freq_sweep["step"] / 2,
                    f + freq_sweep["step"],
                ):
                    # Wait 3 photons lifetime until the resonator relaxes to vacuum (clock cycles)
                    wait(3 * self.relax_time, self.element)
                    # Update the IF
                    update_frequency(self.element, f, units="Hz")
                    # Measure and demodulate the transmitted signal
                    if sequence["down_converter"] == "ED":
                        measure(
                            self.operation,
                            self.element,
                            None,
                            integration.full(
                                sequence["integration_weights"], I, sequence["outputs"]
                            ),
                        )

                    elif sequence["down_converter"] == "IR":
                        measure(
                            self.operation,
                            self.element,
                            None,
                            demod.full(
                                sequence["integration_weights"][0],
                                I,
                                sequence["outputs"],
                            ),
                            demod.full(
                                sequence["integration_weights"][1],
                                Q,
                                sequence["outputs"],
                            ),
                        )

                    elif sequence["down_converter"] == "IQ":
                        measure(
                            self.operation,
                            self.element,
                            None,
                            dual_demod.full(
                                sequence["integration_weights"][0][0],
                                sequence["outputs"][0],
                                sequence["integration_weights"][0][1],
                                sequence["outputs"][1],
                                I,
                            ),
                            dual_demod.full(
                                sequence["integration_weights"][1][0],
                                sequence["outputs"][0],
                                sequence["integration_weights"][1][1],
                                sequence["outputs"][1],
                                Q,
                            ),
                        )
                    save(I, I_st)
                    save(Q, Q_st)
                    save(f, f_st)

            with stream_processing():
                I_st.buffer(n_steps).average().save("I")
                Q_st.buffer(n_steps).average().save("Q")
                f_st.buffer(n_steps).save("f")
        return Prog_single

    def _run_single_measurement(self, qm, sequence: dict, freq_sweep: dict, n_avg: int):
        """
        Execute the single_measurement QUA program

        :param qm: opened quantum machine
        :param sequence: single measurement sequence
        :param freq_sweep: dictionary containing the frequency sweep information (fmin, fmax, step)
        :param n_avg: number of averaged iterations
        :return: None
        """

        print(f"Run {sequence['measurement']} measurement...")
        # Execute the measurement program
        job = qm.execute(self._define_single_measurement(sequence, freq_sweep, n_avg))
        # Fetch results
        print("Fetching data...")
        res_handles = job.result_handles
        res_handles.wait_for_all_values()
        I = res_handles.get("I").fetch_all()
        Q = res_handles.get("Q").fetch_all()
        f = res_handles.get("f").fetch_all()

        self.results[sequence["measurement"]]["f"] = f
        if sequence["down_converter"] == "ED":
            self.results[sequence["measurement"]]["S"] = (
                np.abs(I)
                * 4096
                / (
                    self.config["pulses"][
                        self.config["elements"][self.element]["operations"][
                            self.operation
                        ]
                    ]["length"]
                )
            )
            self.results[sequence["measurement"]]["phase"] = 0 * np.abs(I)
        else:
            self.results[sequence["measurement"]]["S"] = np.sqrt(I**2 + Q**2)
            self.results[sequence["measurement"]]["phase"] = np.unwrap(np.arctan2(I, Q))

    def _define_dual_measurement(self, freq_sweep: dict, n_avg: int):
        """
        Define a dual S-measurement (simultaneous S11 and S21) as a QUA program

        :param freq_sweep: dictionary containing the frequency sweep information (fmin, fmax, step)
        :param n_avg: number of averaged iterations
        :return: corresponding QUA program
        """
        n_steps = (freq_sweep["f_max"] - freq_sweep["f_min"]) / freq_sweep["step"] + 1

        with program() as Prog_dual:
            n = declare(int)
            f = declare(int)
            I = declare(fixed)
            Q = declare(fixed)
            I2 = declare(fixed)
            Q2 = declare(fixed)
            I_st = declare_stream()
            Q_st = declare_stream()
            I2_st = declare_stream()
            Q2_st = declare_stream()
            f_st = declare_stream()

            # Repeat the sequence n_avg times for averaging purposes
            with for_(n, 0, n < n_avg, n + 1):
                # Frequency sweep
                with for_(
                    f,
                    freq_sweep["f_min"],
                    f < freq_sweep["f_max"] + freq_sweep["step"] / 2,
                    f + freq_sweep["step"],
                ):
                    # Wait 3 photons lifetime until the resonator relaxes to vacuum (clock cycles)
                    wait(3 * self.relax_time, self.element)
                    # Update the IF
                    update_frequency(self.element, f, units="Hz")
                    # Measure and demodulate the transmitted signal
                    if (
                        self.measurements[0]["down_converter"] == "ED"
                        and self.measurements[1]["down_converter"] == "ED"
                    ):
                        measure(
                            self.operation,
                            self.element,
                            None,
                            integration.full(
                                self.measurements[0]["integration_weights"],
                                I,
                                self.measurements[0]["outputs"],
                            ),
                            integration.full(
                                self.measurements[1]["integration_weights"],
                                I2,
                                self.measurements[1]["outputs"],
                            ),
                        )

                    elif (
                        self.measurements[0]["down_converter"] == "IR"
                        and self.measurements[1]["down_converter"] == "IR"
                    ):
                        measure(
                            self.operation,
                            self.element,
                            None,
                            demod.full(
                                self.measurements[0]["integration_weights"][0],
                                I,
                                self.measurements[0]["outputs"],
                            ),
                            demod.full(
                                self.measurements[0]["integration_weights"][1],
                                Q,
                                self.measurements[0]["outputs"],
                            ),
                            demod.full(
                                self.measurements[1]["integration_weights"][0],
                                I2,
                                self.measurements[1]["outputs"],
                            ),
                            demod.full(
                                self.measurements[1]["integration_weights"][1],
                                Q2,
                                self.measurements[1]["outputs"],
                            ),
                        )

                    elif (
                        self.measurements[0]["down_converter"] == "IQ"
                        and self.measurements[1]["down_converter"] == "IQ"
                    ):
                        measure(
                            self.operation,
                            self.element,
                            None,
                            dual_demod.full(
                                self.measurements[0]["integration_weights"][0][0],
                                self.measurements[0]["outputs"][0],
                                self.measurements[0]["integration_weights"][0][1],
                                self.measurements[0]["outputs"][1],
                                I,
                            ),
                            dual_demod.full(
                                self.measurements[0]["integration_weights"][1][0],
                                self.measurements[0]["outputs"][0],
                                self.measurements[0]["integration_weights"][1][1],
                                self.measurements[0]["outputs"][1],
                                Q,
                            ),
                            dual_demod.full(
                                self.measurements[1]["integration_weights"][0][0],
                                self.measurements[1]["outputs"][0],
                                self.measurements[1]["integration_weights"][0][1],
                                self.measurements[1]["outputs"][1],
                                I2,
                            ),
                            dual_demod.full(
                                self.measurements[1]["integration_weights"][1][0],
                                self.measurements[1]["outputs"][0],
                                self.measurements[1]["integration_weights"][1][1],
                                self.measurements[1]["outputs"][1],
                                Q2,
                            ),
                        )
                    else:
                        raise KeyError(
                            f"Dual measurement with '{self.measurements[0]['down_converter']}' and "
                            f"'{self.measurements[1]['down_converter']}' is not implemented yet."
                        )
                    save(I, I_st)
                    save(Q, Q_st)
                    save(I2, I2_st)
                    save(Q2, Q2_st)
                    save(f, f_st)

            with stream_processing():
                I_st.buffer(n_steps).average().save("I")
                Q_st.buffer(n_steps).average().save("Q")
                I2_st.buffer(n_steps).average().save("I2")
                Q2_st.buffer(n_steps).average().save("Q2")
                f_st.buffer(n_steps).save("f")
        return Prog_dual

    def _run_dual_measurement(self, qm, freq_sweep: dict, n_avg: int):
        """
        Execute the dual_measurement QUA program

        :param qm: opened quantum machine
        :param freq_sweep: dictionary containing the frequency sweep information (fmin, fmax, step)
        :param n_avg: number of averaged iterations
        :return: None
        """
        # Get defined program
        Prog = self._define_dual_measurement(freq_sweep, n_avg)
        print(
            f"Run dual measurements {self.measurements[0]['measurement']} and {self.measurements[1]['measurement']}..."
        )
        # Execute the measurement program
        job = qm.execute(Prog)

        # Fetch results
        print("Fetching data...")
        res_handles = job.result_handles
        res_handles.wait_for_all_values()

        f = res_handles.get("f").fetch_all()
        for i in range(2):
            if i == 1:
                I = res_handles.get("I").fetch_all()
                Q = res_handles.get("Q").fetch_all()
            else:
                I = res_handles.get("I2").fetch_all()
                Q = res_handles.get("Q2").fetch_all()
            self.results[self.measurements[i]["measurement"]]["f"] = f
            if self.measurements[i]["down_converter"] == "ED":
                self.results[self.measurements[i]["measurement"]]["S"] = np.abs(I)
                self.results[self.measurements[i]["measurement"]]["phase"] = 0 * np.abs(
                    I
                )
            else:
                self.results[self.measurements[i]["measurement"]]["S"] = np.sqrt(
                    I**2 + Q**2
                )
                self.results[self.measurements[i]["measurement"]]["phase"] = np.unwrap(
                    np.arctan2(I, Q)
                )

    def run_all(self, freq_sweep: dict = None, n_avg: int = 1, dual: bool = False):
        """
        Run all previously defined VNA measurements and store results in self.results.

        :param freq_sweep: dictionary containing the frequency sweep information. For instance freq_sweep = {"fmin": 10e6,"fmax": 150e6,"step": 0.01e6,}
        :param n_avg: number of averaged iterations
        :param dual: Boolean flag controlling the parallelism of the measurements. If two measurements were added, then dual=True
        will run them simultaneously, whereas if dual=False the measurements will be run sequentially.
        :return: None
        """
        print(self)
        # Open quantum machine manager
        self.qmm = QuantumMachinesManager()

        if "spectrum_analyzer" in self.meas_list:
            print("Spectrum analyzer...")
            # update measurement pulse duration to match bandwidth
            pulse = self.config["elements"][self.element]["operations"][self.operation]
            self.config["pulses"][pulse]["length"] = self.calibration["SA"][
                "pulse_length"
            ]
            qm = self.qmm.open_qm(self.config)
            self._run_spectrum_analyzer(qm, n_avg)

        # Run each measurement sequentially or in parallel if dual
        qm = self.qmm.open_qm(self.config)
        if not dual:
            for seq in self.measurements:
                self._run_single_measurement(qm, seq, freq_sweep, n_avg)
        else:
            if len(self.measurements) != 2:
                raise KeyError(
                    "Dual run only works for two previously defined measurements"
                )
            self._run_dual_measurement(qm, freq_sweep, n_avg)

    def plot_all(self):
        """
        Plot all the defined measurements.

        :return: None
        """

        for ss in self.results.keys():
            # Spectrum analyzer plot
            if ss == "SA":
                plt.figure(1001, figsize=(9, 8))
                for i in range(len(self.inputs)):
                    plt.subplot(211)
                    plt.plot(
                        np.arange(0, self.calibration["SA"]["pulse_length"], 1),
                        self.results["SA"]["raw"][i],
                        label=f"OPX input {self.inputs[i]}",
                    )
                    plt.subplot(212)
                    plt.plot(
                        self.results["SA"]["f"],
                        self.results["SA"]["fft"][i][
                            : int(np.ceil(len(self.results["SA"]["fft"][i]) / 2))
                        ],
                        label=f"OPX input {self.inputs[i]}",
                    )
                plt.subplot(211)
                plt.title("VNA spectrum analyzer")
                plt.xlabel("Time [ns]")
                plt.ylabel("Raw ADC trace [V]")
                plt.legend()
                plt.subplot(212)
                plt.xlabel("Frequency [Hz]")
                plt.ylabel("FFT [V]")
                plt.legend()
            # S-parameter measurement
            else:
                plt.figure(1002, figsize=(9, 8))
                plt.subplot(211)
                plt.title(f"Spectroscopy of '{self.element}'")
                plt.plot(self.results[ss]["f"] / 1e6, self.results[ss]["S"], label=ss)
                plt.ylabel(r"$\sqrt{I^2+Q^2}$ [V]")
                plt.legend()
                plt.subplot(212)
                plt.plot(
                    self.results[ss]["f"] / 1e6, self.results[ss]["phase"], label=ss
                )
                plt.ylabel("phase [rad]")
                plt.xlabel("Frequency [Hz]")
                plt.legend()
        plt.show()
