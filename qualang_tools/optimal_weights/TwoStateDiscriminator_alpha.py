from pandas import DataFrame
from qm.qua import *
import os
import matplotlib.pyplot as plt
from sklearn import mixture
from scipy import signal
import numpy as np


class TwoStateDiscriminator:
    """
    TwoStateDiscriminator is a class that returns optimal weights for state discrimination
    of a two level system, namely, |g> and |e> of a qubit.
    The optimization starts with a training program (TwoStateDiscriminator.train()) that will perform the following steps:
        - Measure the raw adc traces and demodulated 'I' and 'Q' signals for the qubit in the ground and excited states.
        - Demodulate and derive the average time evolution of the complex vector Z(t)=I(t)+j*Q(t) within the readout window.
        - Derive the optimal weights as the difference between Z(t) for the qubit in the ground and excited state (Z_g(t)-Z_e(t)).
        - Update the configuration with these optimal integration weights.
    """

    def __init__(
        self,
        qmm,
        config: dict,
        readout_el: str,
        readout_pulse: str,
        path: str,
        meas_len: int,
        smearing: int,
        lsb: bool = False,
        iq_mixer: bool = True,
        update_tof: bool = True,
        iw_prefix: str = "opt_",
    ):
        """
        Constructor for the TwoStateDiscriminator class.

        :param qmm: QuantumMachinesManager object
        :param config: A quantum machine configuration dictionary with the readout resonator element (must be mixInputs and have 2 outputs, i.e., IQ mixers for up and down conversion).
        :param update_tof: A boolean variable to proceed or not to remove the smearing from the time_of_flight value
        :param readout_el: A string with the name of the readout resonator element (as specified in the config)
        :param readout_pulse: A string with the name of the readout pulse used to obtain the optimal weights
        :param path: A path to save optimized parameters, namely, integration weights and bias for each state. This file is generated during training, and it is used during the subsequent measure_state procedure.
        :param meas_len: Duration of the readout pulse extracted from the configuration.
        :param smearing: Smearing duration extracted from the configuration.
        :param lsb: Defines if the down-conversion mixers does a conversion to LO - IF, i.e., lower side band
        :param iw_prefix: Prefix to the name of the optimal integration weights. Default i 'opt_' leading to opt_cos_readout_element, opt_sin_readout_element...
        :param iq_mixer: Defines if an IQ mixer (True) or an image rejection mixer (False) is used for the down-conversion.
        """

        # Load the user inputs
        self.qmm = qmm
        self.config = config
        self.resonator_el = readout_el
        self.resonator_pulse = readout_pulse
        self.path = path
        self.update_tof = update_tof
        self.lsb = lsb
        self.iq_mixer = iq_mixer
        self.meas_len = meas_len
        self.smearing = smearing
        self.iw_prefix = iw_prefix
        # Initialize some variables
        self.num_of_states = 2
        self.saved_data = None
        self.time_diff = None
        self.Z = None
        self.ts = None
        self.plot = False
        self.simulation = None
        self.finish_train = 0
        self.mu = dict()
        self.sigma = dict()
        # Load the Optimal weights if path is provided and update the config
        self._load_file(path)

    def _load_file(self, path):
        """Load the saved integration weights and update the config"""
        if os.path.isfile(path):
            self.saved_data = np.load(path, allow_pickle=True)
            self._update_config()

    def _get_element_freq(self, element):
        """return the IF of a given element"""
        return self.config["elements"][element]["intermediate_frequency"]

    def _execute_and_fetch(self, qua_program, **execute_args):
        """Execute the program and fetch the data (I, Q, adc1, adc2)"""
        # Open QM
        qm = self.qmm.open_qm(self.config)
        # Execute the program
        if self.simulation is not None:
            job = self.qmm.simulate(self.config, qua_program, self.simulation)
        else:
            job = qm.execute(
                qua_program, duration_limit=0, data_limit=0, **execute_args
            )
        # Wait for all data and fetch
        res_handles = job.result_handles
        res_handles.wait_for_all_values()
        I_res = res_handles.get("I").fetch_all()["value"]
        Q_res = res_handles.get("Q").fetch_all()["value"]
        ts = res_handles.get("adc1").fetch_all()["value"]["timestamp"]
        in1 = res_handles.get("adc1").fetch_all()["value"]["value"]

        # Initial data format I = [g, e, g, e, g, e...] --> [g, g, g,..., e, e, e,...]
        I_res = np.concatenate([I_res[0::2], I_res[1::2]])
        Q_res = np.concatenate([Q_res[0::2], Q_res[1::2]])
        ts = np.concatenate([ts[0::2], ts[1::2]])
        in1 = np.concatenate([in1[0::2], in1[1::2]])

        if I_res.shape != Q_res.shape:
            raise RuntimeError(
                "Size of I and Q coming from stream processing are no the same"
            )

        if self.iq_mixer:
            in2 = res_handles.get("adc2").fetch_all()["value"]
            in2 = np.concatenate([in2[0::2], in2[1::2]])

            if not self.lsb:
                Z = in1 + 1j * in2
            else:
                Z = in1 - 1j * in2

        else:
            Z = in1
        return I_res, Q_res, ts, Z

    def _downconvert(self):
        """Down-convert the raw ADC traces"""
        if self.time_diff is None:
            self.time_diff = 36  # tested experimentally in 2.20
        rr_freq = self._get_element_freq(self.resonator_el)
        sig = self.Z * np.exp(
            -1j * 2 * np.pi * rr_freq * 1e-9 * (self.ts - self.time_diff)
        )
        return sig

    def _get_traces(self, qe, correction_method, I_res, Q_res, sig, use_hann_filter):
        """Derive the average traces for ground and excited states using different methods"""
        # Number of runs
        measures_per_state = len(I_res) // self.num_of_states
        # Array filled with 0 for ground and 1 for excited: [0, 0, 0..., 1, 1, 1...]
        self.seq0 = np.array(
            [[i] * measures_per_state for i in range(self.num_of_states)]
        ).flatten()
        # Use a gaussian mixture model to fit the IQ blobs from the results of the FPGA demodulation and exclude the points that don't belong to their label
        if correction_method == "gmm":
            data = {"x": I_res, "y": Q_res}
            x = DataFrame(data, columns=["x", "y"])
            gmm = mixture.GaussianMixture(
                n_components=self.num_of_states,
                covariance_type="spherical",
                tol=1e-12,
                reg_covar=1e-12,
            )
            pr_state = gmm.fit_predict(x)
            mapping = [
                np.argmax(np.bincount(pr_state[self.seq0 == i]))
                for i in range(self.num_of_states)
            ]
            traces = np.array(
                [
                    np.mean(sig[pr_state == mapping[i], :], axis=0)
                    for i in range(self.num_of_states)
                ]
            )
        # Compute the average traces using 'median' for the ground and excited states whose difference define the optimal weights.
        elif correction_method == "median":
            traces = np.array(
                [
                    np.median(sig[self.seq0 == i, :], axis=0)
                    for i in range(self.num_of_states)
                ]
            )
        # Compute the average traces using 'mean' for the ground and excited states whose difference define the optimal weights.
        elif correction_method == "mean":
            traces = np.array(
                [
                    np.mean(sig[self.seq0 == i, :], axis=0)
                    for i in range(self.num_of_states)
                ]
            )
        else:
            raise Exception(
                f"Correction method '{correction_method}' is not implemented."
            )
        # Filter the average traces using a Hann window
        if use_hann_filter:
            rr_freq = self._get_element_freq(qe)
            period_ns = int(1 / rr_freq * 1e9)
            hann = signal.windows.hann(period_ns * 2, sym=True)
            hann = hann / np.sum(hann)
            traces = np.array(
                [
                    np.convolve(traces[i, :], hann, "same")
                    for i in range(self.num_of_states)
                ]
            )
        return traces

    @staticmethod
    def _reshape_traces(traces):
        """Reshape the traces to have one point every clock cycle (4ns)"""
        weights = []
        for i in range(traces.shape[0]):
            weights.append(np.average(np.reshape(traces[i, :], (-1, 4)), axis=1))
        return np.array(weights)

    def _add_iw_to_pulses(self, iw):
        """Add optimal integration weights to readout pulses"""
        pulse = self.config["pulses"][self.resonator_pulse]
        if "integration_weights" not in pulse:
            pulse["integration_weights"] = {}
        pulse["integration_weights"][iw] = iw

    def _IQ_mu_sigma(self, b_vec):
        """Derive the IQ blobs with the optimal integration weights and get their centers and widths"""
        out1 = np.real(self.Z) * 2**-12
        rr_freq = self._get_element_freq(self.resonator_el)
        cos = np.cos(2 * np.pi * rr_freq * 1e-9 * (self.ts - self.time_diff))
        sin = np.sin(2 * np.pi * rr_freq * 1e-9 * (self.ts - self.time_diff))
        # Get iw with a 1ns timestep
        b_vec = np.repeat(b_vec, 4)
        if self.iq_mixer:
            if not self.lsb:
                out2 = np.imag(self.Z) * 2**-12
                sign = 1
            else:
                out2 = -np.imag(self.Z) * 2**-12
                sign = -1

            # Demodulate and integrate the measured data with the optimal weights
            I_res = np.sum(
                out1 * (cos * np.real(b_vec) + sin * np.imag(-b_vec)), axis=1
            ) + np.sum(
                out2 * (cos * np.imag(b_vec) + sin * np.real(b_vec)) * sign, axis=1
            )
            Q_res = np.sum(
                out2 * (cos * np.real(b_vec) + sin * np.imag(-b_vec)), axis=1
            ) - np.sum(
                out1 * (cos * np.imag(b_vec) + sin * np.real(b_vec)) * sign, axis=1
            )
        else:
            # Demodulate and integrate the measured data with the optimal weights
            I_res = np.sum(
                out1 * (cos * np.real(b_vec) + sin * np.imag(-b_vec)), axis=1
            )
            Q_res = np.sum(out1 * (cos * np.imag(b_vec) + sin * np.real(b_vec)), axis=1)
        # Demodulation units
        I_res *= 2**-12
        Q_res *= 2**-12
        # Derive the center and widths of the blobs
        for i in range(self.num_of_states):
            I_ = I_res[self.seq0 == i]
            Q_ = Q_res[self.seq0 == i]
            data = {"x": I_, "y": Q_}
            x = DataFrame(data, columns=["x", "y"])
            gmm = mixture.GaussianMixture(
                n_components=1, covariance_type="spherical", tol=1e-12, reg_covar=1e-12
            )
            gmm.fit(x)
            self.mu[i] = gmm.means_[0]
            self.sigma[i] = np.sqrt(gmm.covariances_[0])
        # Plot the IQ blobs obtained from the optimal weights
        if self.plot:
            plt.figure()
            for i in range(self.num_of_states):
                I_ = I_res[self.seq0 == i]
                Q_ = Q_res[self.seq0 == i]
                theta = np.linspace(0, 2 * np.pi, 100)
                a = self.sigma[i] * np.cos(theta) + self.mu[i][0]
                b = self.sigma[i] * np.sin(theta) + self.mu[i][1]
                plt.plot(I_, Q_, ".", label=f"state {i}")
                plt.plot([self.mu[i][0]], [self.mu[i][1]], "o")
                plt.plot(a, b)
                plt.axis("equal")
            plt.xlabel("I")
            plt.ylabel("Q")
            plt.legend()
            plt.show()
        # Add mu and sigma to the saved data
        data = dict(np.load(self.path))
        data["mu"] = self.mu
        data["sigma"] = self.sigma
        np.savez(self.path, **data)

    def _update_config(self):
        """Update the configuration with the optimal weights"""
        weights = self.saved_data["weights"]
        # Get mu and sigma from saved file if this does not follow the training
        if self.finish_train == 0:
            self.mu = self.saved_data["mu"].tolist()
            self.sigma = self.saved_data["sigma"].tolist()
        # Real weights
        b_vec = weights[0, :] - weights[1, :]
        # Assign the integration weights to list of tuples in steps of 4 ns
        w_plus_cos = [(np.real(b_vec)[i], 4) for i in range(len(np.real(b_vec)))]
        w_minus_sin = [(np.imag(-b_vec)[i], 4) for i in range(len(np.real(b_vec)))]
        w_plus_sin = [(np.imag(b_vec)[i], 4) for i in range(len(np.real(b_vec)))]
        w_minus_cos = [(np.real(-b_vec)[i], 4) for i in range(len(np.real(b_vec)))]
        # Derive the weights
        self.config["integration_weights"][
            self.iw_prefix + f"cos_{self.resonator_el}"
        ] = {
            "cosine": w_plus_cos,
            "sine": w_minus_sin,
        }
        self.config["integration_weights"][
            self.iw_prefix + f"sin_{self.resonator_el}"
        ] = {
            "cosine": w_plus_sin,
            "sine": w_plus_cos,
        }
        self.config["integration_weights"][
            self.iw_prefix + f"minus_sin_{self.resonator_el}"
        ] = {
            "cosine": w_minus_sin,
            "sine": w_minus_cos,
        }
        # Add the weights to the pulses
        self._add_iw_to_pulses(self.iw_prefix + f"cos_{self.resonator_el}")
        self._add_iw_to_pulses(self.iw_prefix + f"sin_{self.resonator_el}")
        self._add_iw_to_pulses(self.iw_prefix + f"minus_sin_{self.resonator_el}")
        # Update time of flight if smearing was added to increase the acquisition window
        if self.update_tof:
            self.config["elements"][self.resonator_el]["time_of_flight"] = (
                self.config["elements"][self.resonator_el]["time_of_flight"]
                - self.config["elements"][self.resonator_el]["smearing"]
            )
            self.config["elements"][self.resonator_el]["smearing"] = 0
        # If training is done, derive optimal IQ blobs mean and std
        if self.finish_train == 1:
            self._IQ_mu_sigma(b_vec)

    def _training_program(self, qubit_element, pi_pulse, cooldown_time, n_shots):
        if self.iq_mixer:
            with program() as qua_program:
                n = declare(int)
                I = declare(fixed)
                Q = declare(fixed)
                I_st = declare_stream()
                Q_st = declare_stream()
                adc = declare_stream(adc_trace=True)

                with for_(n, 0, n < n_shots, n + 1):
                    # Wait 100µs for the qubit to decay
                    wait(cooldown_time, self.resonator_el, qubit_element)
                    # Measure ground state
                    measure(
                        self.resonator_pulse,
                        self.resonator_el,
                        adc,
                        dual_demod.full("cos", "out1", "sin", "out2", I),
                        dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
                    )
                    save(I, I_st)
                    save(Q, Q_st)

                    # Wait 100µs for the qubit to decay
                    wait(cooldown_time, self.resonator_el, qubit_element)
                    # Measure excited state
                    align(qubit_element, self.resonator_el)
                    play(pi_pulse, qubit_element)
                    align(qubit_element, self.resonator_el)
                    measure(
                        self.resonator_pulse,
                        self.resonator_el,
                        adc,
                        dual_demod.full("cos", "out1", "sin", "out2", I),
                        dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
                    )
                    save(I, I_st)
                    save(Q, Q_st)
                with stream_processing():
                    I_st.save_all("I")
                    Q_st.save_all("Q")
                    adc.input1().with_timestamps().save_all("adc1")
                    adc.input2().save_all("adc2")
        else:
            with program() as qua_program:
                n = declare(int)
                I = declare(fixed)
                Q = declare(fixed)
                I_st = declare_stream()
                Q_st = declare_stream()
                adc = declare_stream(adc_trace=True)

                with for_(n, 0, n < n_shots, n + 1):
                    # Wait 100µs for the qubit to decay
                    wait(cooldown_time, self.resonator_el, qubit_element)
                    # Measure ground state
                    measure(
                        self.resonator_pulse,
                        self.resonator_el,
                        adc,
                        demod.full("cos", I, "out1"),
                        dual_demod.full("sin", Q, "out1"),
                    )
                    save(I, I_st)
                    save(Q, Q_st)

                    # Wait 100µs for the qubit to decay
                    wait(cooldown_time, self.resonator_el, qubit_element)
                    # Measure excited state
                    align(qubit_element, self.resonator_el)
                    play(pi_pulse, qubit_element)
                    align(qubit_element, self.resonator_el)
                    measure(
                        self.resonator_pulse,
                        self.resonator_el,
                        adc,
                        demod.full("cos", I, "out1"),
                        dual_demod.full("sin", Q, "out1"),
                    )
                    save(I, I_st)
                    save(Q, Q_st)
                with stream_processing():
                    I_st.save_all("I")
                    Q_st.save_all("Q")
                    adc.input1().with_timestamps().save_all("adc1")
        return qua_program

    def get_default_training_program(self):
        """Print the default training program"""
        if self.iq_mixer:
            prog = f"""
with program() as qua_program:
    n = declare(int)
    I = declare(fixed)
    Q = declare(fixed)
    I_st = declare_stream()
    Q_st = declare_stream()
    adc = declare_stream(adc_trace=True)

    with for_(n, 0, n < n_shots, n + 1):
        # Wait 100µs for the qubit to decay
        wait(cooldown_time, {self.resonator_el}, qubit_element)
        # Measure ground state
        measure(
            {self.resonator_pulse},
            {self.resonator_el},
            adc,
            dual_demod.full("cos", "out1", "sin", "out2", I),
            dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
        )
        save(I, I_st)
        save(Q, Q_st)

        # Wait 100µs for the qubit to decay
        wait(cooldown_time, {self.resonator_el}, qubit_element)
        # Measure excited state
        align(qubit_element, {self.resonator_el})
        play(pi_pulse, qubit_element)
        align(qubit_element, {self.resonator_el})
        measure(
            {self.resonator_pulse},
            {self.resonator_el},
            adc,
            dual_demod.full("cos", "out1", "sin", "out2", I),
            dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
        )
        save(I, I_st)
        save(Q, Q_st)
    with stream_processing():
        I_st.save_all("I")
        Q_st.save_all("Q")
        adc.input1().with_timestamps().save_all("adc1")
        adc.input2().save_all("adc2")"""
        else:
            prog = f"""
with program() as qua_program:
    n = declare(int)
    I = declare(fixed)
    Q = declare(fixed)
    I_st = declare_stream()
    Q_st = declare_stream()
    adc = declare_stream(adc_trace=True)

    with for_(n, 0, n < n_shots, n + 1):
        # Wait 100µs for the qubit to decay
        wait(cooldown_time, {self.resonator_el}, qubit_element)
        # Measure ground state
        measure(
            {self.resonator_pulse},
            {self.resonator_el},
            adc,
            demod.full("cos", I, "out1"),
            demod.full("sin", Q, "out1"),
        )
        save(I, I_st)
        save(Q, Q_st)

        # Wait 100µs for the qubit to decay
        wait(cooldown_time, {self.resonator_el}, qubit_element)
        # Measure excited state
        align(qubit_element, {self.resonator_el})
        play(pi_pulse, qubit_element)
        align(qubit_element, {self.resonator_el})
        measure(
            {self.resonator_pulse},
            {self.resonator_el},
            adc,
            demod.full("cos", I, "out1"),
            demod.full("sin", Q, "out1"),
        )
        save(I, I_st)
        save(Q, Q_st)
    with stream_processing():
        I_st.save_all("I")
        Q_st.save_all("Q")
        adc.input1().with_timestamps().save_all("adc1")"""
        default = """
By default:
    n_shots = 10_000
    cooldown_time = 25_000
    qubit_element = 'qubit' (make sure that it is defined in the config)
    pi_pulse = 'x_180' (make sure that it is defined in the config)
            """

        print(prog)
        print(default)
        return

    def train(
        self,
        qua_program,
        simulation=None,
        use_hann_filter: bool = True,
        plot: bool = False,
        correction_method: str = "median",
        **kwargs,
    ):
        """
        The train procedure is used to calibrate the optimal weights and bias for each state. A file with the optimal
        parameters is generated during training, and it is used during the subsequent measure_state procedure.
        A training program can be provided in the constructor otherwise the default program will be used.
        This default training program can be seen by calling self.get_default_training_program() and the 'pi_pulse' ('x_180'), 'qubit_element' ('qubit'), 'n_shots' (10_000) and 'cooldown_time' (25_000) can be specified as kwargs.

        :param qua_program: a training program that generates training sets. The program should generate equal number of training sets for each one of the states. Collection of training sets is achieved by first preparing the qubit in one of the states, and then measure the readout resonator element. The measure command must include streaming of the raw data (the tag must be called "adc") and the final complex demodulation results (which is constructed from 2 dual demodulation) must be saved under the tags "I" and "Q". E.g: measure("readout", "rr", "adc", dual_demod.full('cos', 'out1', 'sin', 'out2', I), dual_demod.full('minus_sin', 'out1', 'cos', 'out2', Q)). The stream processing section must be constructed as
        :param simulation: passes the SimulationConfig
        :param use_hann_filter: Whether to use a low-pass filter on the averaged sampled baseband waveforms.
        :param plot: Whether to plot some figures for debug purposes.
        :param correction_method: it is possible to use 'gmm', 'median', or 'mean'. The default mode is 'median'. 'mean' computes the mean trace for the ground and excited states whose difference define the optimal weights. 'median' computes the median trace for the ground and excited states whose difference define the optimal weights. 'gmm' uses a gaussian mixture model to fit the IQ blobs from the results of the FPGA demodulation and exclude the points that don't belong to their label (ground or excited) in the calculation of the weights.
        """
        self.plot = plot
        self.simulation = simulation
        qubit_element = kwargs.get("qubit_element", "qubit")
        pi_pulse = kwargs.get("pi_pulse", "x180")
        cooldown_time = kwargs.get("cooldown_time", 25_000)
        n_shots = kwargs.get("n_shots", 10_000)
        # Get qua_program
        if qua_program is None:
            qua_program = self._training_program(
                qubit_element, pi_pulse, cooldown_time, n_shots
            )
        # Open qm, execute and fetch data, format is [|g>, |g>, |g>,... |e>, |e>, |e>,...]
        I_res, Q_res, self.ts, self.Z = self._execute_and_fetch(qua_program)
        # Down convert the raw ADC traces
        sig = self._downconvert()
        # Get the averaged complex time trace of Z for ground and excited [Zg(t), Ze(t)]
        traces = self._get_traces(
            self.resonator_el,
            correction_method,
            I_res,
            Q_res,
            sig,
            use_hann_filter,
        )
        # Reshape the traces to steps of 4ns
        traces_4ns = self._reshape_traces(traces)

        norm = np.max(np.abs(traces_4ns))
        traces_4ns = traces_4ns / norm
        # Bias = norm of the ground and excited state vectors
        bias = (
            (np.linalg.norm(traces_4ns * norm, axis=1) ** 2) / norm / 2 * (2**-24) * 4
        )
        # Save the traces and norms
        np.savez(
            self.path,
            weights=traces_4ns,
            bias=bias,
            smearing=self.smearing,
            meas_len=self.meas_len,
        )
        self.saved_data = {
            "weights": traces_4ns,
            "bias": bias,
            "smearing": self.smearing,
            "meas_len": self.meas_len,
        }
        # The training is over
        self.finish_train = 1
        # Update the config with the optimal weights
        self._update_config()

        if self.plot:
            plt.figure()
            for i in range(self.num_of_states):
                I_ = I_res[self.seq0 == i]
                Q_ = Q_res[self.seq0 == i]
                plt.plot(I_, Q_, ".", label=f"state {i}")
                plt.axis("equal")
            plt.xlabel("I")
            plt.ylabel("Q")
            plt.title("IQ blobs from FPGA demod")
            plt.legend()

            plt.figure()
            for i in range(self.num_of_states):
                plt.subplot(self.num_of_states, 1, i + 1)
                plt.plot(np.real(traces_4ns[i, :]))
                plt.plot(np.imag(traces_4ns[i, :]))
                if i == 0:
                    plt.title("Time traces for |g> and |e>")
            plt.figure()
            for i in range(self.num_of_states):
                plt.plot(np.real(traces_4ns[i, :]), np.imag(traces_4ns[i, :]))
                plt.axis("equal")
            plt.title("Trajectories in phase space")

            plt.figure()
            plt.plot(np.real(traces_4ns[0, :] - traces_4ns[1, :]))
            plt.plot(np.imag(traces_4ns[0, :] - traces_4ns[1, :]))
            plt.title("Optimal weights")

    def get_threshold(self):
        bias = self.saved_data["bias"]
        return bias[0] - bias[1]

    def measure_state(
        self, pulse: str, out1: str, out2: str, adc=None, state=None, I=None, Q=None
    ):
        """
        This procedure generates a macro of QUA commands for measuring the readout resonator with the optimal
        integration weights and perform state discrimination.

        :param pulse: A string with the readout pulse name.
        :param out1: A string with the name first output of the readout resonator (corresponding to the real part of the
         complex IN(t_int) signal).
        :param out2: A string with the name second output of the readout resonator (corresponding to the imaginary part
        of the complex IN(t_int) signal).
        :param state: A QUA variable for the state information. Should be of type `bool`.
        If not given, a new variable will be created.
        :param adc: (optional) the stream variable which the raw ADC data will be saved and will appear in result
        analysis scope.
        :param I: A QUA variable for the information in the `I` quadrature. Should be of type `Fixed`. If not given, a new
        variable will be created.
        :param Q: A QUA variable for the information in the `Q` quadrature. Should be of type `Fixed`. If not given, a new
        variable will be created.
        :return: a boolean representing the qubit state (True for excited and False for ground) and the corresponding 'I'
        and 'Q' values if they were provided as input parameters.
        """
        # Declare I, Q and state if not provided
        if I is None:
            I = declare(fixed)
        if Q is None:
            Q = declare(fixed)
        if state is None:
            state = declare(bool)
        # Measure with optimal weights
        if self.iq_mixer:
            if not self.lsb:
                measure(
                    pulse,
                    self.resonator_el,
                    adc,
                    dual_demod.full(
                        self.iw_prefix + f"cos_{self.resonator_el}",
                        out1,
                        self.iw_prefix + f"sin_{self.resonator_el}",
                        out2,
                        I,
                    ),
                    dual_demod.full(
                        self.iw_prefix + f"minus_sin_{self.resonator_el}",
                        out1,
                        self.iw_prefix + f"cos_{self.resonator_el}",
                        out2,
                        Q,
                    ),
                )
            else:
                measure(
                    pulse,
                    self.resonator_el,
                    adc,
                    dual_demod.full(
                        self.iw_prefix + f"cos_{self.resonator_el}",
                        out1,
                        self.iw_prefix + f"minus_sin_{self.resonator_el}",
                        out2,
                        I,
                    ),
                    dual_demod.full(
                        self.iw_prefix + f"sin_{self.resonator_el}",
                        out1,
                        self.iw_prefix + f"cos_{self.resonator_el}",
                        out2,
                        Q,
                    ),
                )
        else:
            measure(
                pulse,
                self.resonator_el,
                adc,
                demod.full(self.iw_prefix + f"cos_{self.resonator_el}", I, out1),
                demod.full(self.iw_prefix + f"sin_{self.resonator_el}", Q, out1),
            )
        # State discrimination
        assign(state, I < self.get_threshold())
        # Return state, I and Q
        return state, I, Q

    def measure_state_old(self, pulse, out1, out2, res, adc=None, I=None, Q=None):
        """
        This procedure generates a macro of QUA commands for measuring the readout resonator and discriminating between
        the qubit states.

        :param pulse: A string with the readout pulse name.
        :param out1: A string with the name first output of the readout resonator (corresponding to the real part of the
         complex IN(t_int) signal).
        :param out2: A string with the name second output of the readout resonator (corresponding to the imaginary part
        of the complex IN(t_int) signal).
        :param res: A boolean QUA variable that will receive the discrimination result (0 or 1)
        :param adc: (optional) the stream variable which the raw ADC data will be saved and will appear in result
        analysis scope.
        :return: a boolean representing the qubit state (True for excited and False for ground) and the corresponding 'I' and 'Q' values if they were provided as input parameters.
        """
        II = declare(fixed)
        QQ = declare(fixed)

        if self.iq_mixer:
            if not self.lsb:
                Q1_weight, Q2_weight = (
                    self.iw_prefix + f"minus_sin_{self.resonator_el}",
                    self.iw_prefix + f"sin_{self.resonator_el}",
                )
            else:
                Q1_weight, Q2_weight = (
                    self.iw_prefix + f"sin_{self.resonator_el}",
                    self.iw_prefix + f"minus_sin_{self.resonator_el}",
                )
        else:
            Q1_weight, Q2_weight = (
                self.iw_prefix + f"sin_{self.resonator_el}",
                self.iw_prefix + f"minus_sin_{self.resonator_el}",
            )

        if Q is not None:
            if self.iq_mixer:
                measure(
                    pulse,
                    self.resonator_el,
                    adc,
                    dual_demod.full(
                        self.iw_prefix + f"cos_{self.resonator_el}",
                        out1,
                        Q2_weight,
                        out2,
                        II,
                    ),
                    dual_demod.full(
                        Q1_weight,
                        out1,
                        self.iw_prefix + f"cos_{self.resonator_el}",
                        out2,
                        QQ,
                    ),
                )
            else:
                measure(
                    pulse,
                    self.resonator_el,
                    adc,
                    demod.full(self.iw_prefix + f"cos_{self.resonator_el}", II, out1),
                    demod.full(Q1_weight, QQ, out1),
                )

        else:
            if self.iq_mixer:
                measure(
                    pulse,
                    self.resonator_el,
                    adc,
                    dual_demod.full(
                        self.iw_prefix + f"cos_{self.resonator_el}",
                        out1,
                        Q2_weight,
                        out2,
                        II,
                    ),
                )
            else:
                measure(
                    pulse,
                    self.resonator_el,
                    adc,
                    dual_demod.full(
                        self.iw_prefix + f"cos_{self.resonator_el}", II, out1
                    ),
                )

        assign(res, II < self.get_threshold())
        if I is not None:
            assign(I, II)
        if Q is not None:
            assign(Q, QQ)

        return res, I, Q
