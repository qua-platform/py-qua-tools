from scipy import optimize
import numpy as np


def fit_ramsey(x, y):
    """
    Create a fit to Ramsey experiment of the form

    .. math::
    f(x) = uncertainty_population * (1 - np.exp(-x * (1/tau))) + amp / 2 * (
        np.exp(-x * (1/tau))
        * (initial_offset * 2 + np.cos(2 * np.pi * f * x + phase))
        )

    for unknown parameters `f`, `phase`, `tau`, `amp`, `uncertainty_population` and `initial_offset`.

    :param x:  The data on the x axis
    :param y: The data on the y axis
    :return: A dictionary of (fit_func, f, phase, tau, amp, uncertainty_population, initial_offset)
        fit_func - The fitted function
        f -  The detuning frequency
        phase - The phase
        tau - The decay constant
        amp - The amplitude
        uncertainty_population -  The uncertainty in population
        initial_offset - The initial offset
    """
    w = np.fft.fft(y)
    freqs = np.fft.fftfreq(len(x))
    new_w = w[1 : len(freqs // 2)]
    new_f = freqs[1 : len(freqs // 2)]

    ind = new_f > 0
    new_f = new_f[ind]
    new_w = new_w[ind]

    yy = np.abs(new_w)
    first_read_data_ind = np.where(yy[1:] - yy[:-1] > 0)[0][0]  # away from the DC peak

    new_f = new_f[first_read_data_ind:]
    new_w = new_w[first_read_data_ind:]

    out_freq = new_f[np.argmax(np.abs(new_w))]
    new_w_arg = new_w[np.argmax(np.abs(new_w))]

    # Finding a guess for the frequency
    omega = out_freq * 2 * np.pi / (x[1] - x[0])

    cycle = int(np.ceil(1 / out_freq))
    peaks = (
        np.array(
            [np.std(y[i * cycle : (i + 1) * cycle]) for i in range(int(len(y) / cycle))]
        )
        * np.sqrt(2)
        * 2
    )

    # Finding a guess for the offset
    initial_offset = np.mean(y[:cycle])
    cycles_wait = np.where(peaks > peaks[0] * 0.37)[0][-1]

    post_decay_mean = np.mean(y[-cycle:])

    # Finding a guess for the decay
    decay_guess = (
        np.log(peaks[0] / peaks[cycles_wait]) / (cycles_wait * cycle) / (x[1] - x[0])
    )  # get guess for decay #here

    fit_type = lambda x, a: post_decay_mean * a[4] * (
        1 - np.exp(-x * decay_guess * a[1])
    ) + peaks[0] / 2 * a[2] * (
        np.exp(-x * decay_guess * a[1])
        * (
            a[5] * initial_offset / peaks[0] * 2
            + np.cos(2 * np.pi * a[0] * omega / (2 * np.pi) * x + a[3])
        )
    )

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    angle0 = np.angle(new_w_arg) - omega * x[0]

    popt = curve_fit(
        fit_type,
        x,
        y,
        [1, 1, 1, angle0, 1, 1, 1],
    )

    print(
        f"f = {popt[0] * omega / (2 * np.pi)}, phase = {popt[3] % (2 * np.pi)}, tau = {1 / (decay_guess * popt[1])}, amp = {peaks[0] * popt[2]}, uncertainty population = {post_decay_mean * popt[4]},initial offset = {popt[5] * initial_offset}"
    )
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "f": popt[0] * omega / (2 * np.pi),
        "phase": popt[3] % (2 * np.pi),
        "tau": 1 / (decay_guess * popt[1]),
        "amp": peaks[0] * popt[2],
        "uncertainty_population": post_decay_mean * popt[4],
        "initial_offset": popt[5] * initial_offset,
    }

    return out


def fit_linear(x, y):
    """
    Create a linear fit of the form

    .. math::
    f(x) = a * x + b

    for unknown parameters `a` and `b`.

    :param x: The data on the x axis
    :param y: The data on the y axis
    :return: A dictionary of (fit_func, a, b)
        fit_func - The fitted function
        a - The slope of the function
        b - The free parameter of the function

    """

    # Finding an initial guess to the slope
    m0 = (y[-1] - y[0]) / (x[-1] - x[0])

    # Finding an initial guess to the free parameter
    n0 = y[0]

    fit_type = lambda x, a: m0 * a[0] * x + n0 * a[1]

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [m0, n0])

    print(f"a = {popt[0]}, b = {popt[1]}")
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "a": popt[0],
        "b": popt[1],
    }

    return out


def fit_phase_resonator_spectroscopy(x, y):
    # find guess of offset
    v0 = y[0]

    # fit_type = lambda x, a: (((a[0] / 2) * (x - a[3])) / ((a[1] ** 2 / 4) + ((x-a[3]) ** 2))) * (4/a[1] ** 2) + v0 * a[2]
    fit_type = (
        lambda x, a: (((a[0] / 2) * (x - a[3])) / ((a[1] ** 2 / 4) + ((x - a[3]) ** 2)))
        + v0 * a[2]
    )

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [1, 1, 1, 1])

    print(f"amp*kc = {popt[0]}, k = {popt[1]}, offset = {v0 * popt[2]}")
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "amp*kc": popt[0],
        "k": popt[1],
        "w": popt[3],
        "offset": v0 * popt[2],
    }

    return out


def fit_reflection_resonator_spectroscopy(x, y):
    """
    Create a fit to reflection resonator spectroscopy of the form

    .. math::
    (a)-(b / (
        1 + (4 * ((x - f) ** 2) / (c ** 2)))) + d * x
    for unknown parameters `a`, `b`, `c`, `d`, `f`.

    :param x:  The data on the x axis
    :param y: The data on the y axis
    :return: A dictionary of (fit_func, f, kc, k, ki, offset
        fit_func - The fitted function
        f - The frequency at the peak
        kc - The strength with which the field of the resonator couples to the transmission line
        ki - A parameter that indicates the internal coherence properties of the resonator
        k - The FWHM of the fitted function.  k = ki + kc
        offset - The offset
        slope - The slope of the function. This is added after experimental considerations.

    """

    y = np.array(y)

    # Finding a guess for the min
    peak = min(y)
    arg_min = y.argmin()

    # Finding the frequency at the min
    f0 = x[arg_min]

    # Finding an initial guess for the FWHM
    if arg_min > len(y) / 2:
        y_FWHM = (peak + np.mean(y[0:10])) / 2
    else:
        y_FWHM = (peak + np.mean(y[-10:-1])) / 2

    # Finding a guess to the width
    width0_arg_right = (np.abs(y_FWHM - y[arg_min + 1 : len(y)])).argmin() + arg_min
    width0_arg_left = (np.abs(y_FWHM - y[0:arg_min])).argmin()
    width0 = x[width0_arg_right] - x[width0_arg_left]

    # Finding guess to offset
    v0 = (np.mean(y[-10:-1]) + np.mean(y[0:10])) / 2

    # Finding a guess to the slope
    m = (
        np.mean(y[int(width0_arg_right + width0) : -1])
        - np.mean(y[0 : int(width0_arg_left - width0)])
    ) / (
        np.mean(x[int(width0_arg_right + width0) : -1])
        - np.mean(x[0 : int(width0_arg_left - width0)])
    )

    fit_type = (
        lambda x, a: ((v0 - peak) * a[3])
        - (
            ((v0 - peak) * a[0])
            / (1 + (4 * ((x - (f0 * a[2])) ** 2) / ((width0 * a[1]) ** 2)))
        )
        + m * a[4] * x
    )

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [1, 1, 1, 1, 1])

    print(
        f"f = {f0 * popt[2]}, kc = {(v0 - peak) * popt[0] * (width0 * popt[1] / min(fit_type(x, popt)))}, ki = {width0 * popt[1] - (peak - v0) * popt[0] * (width0 * popt[1] / max(fit_type(x, popt)))}, k = {width0 * popt[1]},offset =  {(v0 - peak) * popt[3]}, slope = {m * popt[4]}"
    )
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "f": f0 * popt[2],
        "kc": (peak - v0) * popt[0] * (width0 * popt[1] / max(fit_type(x, popt))),
        "ki": width0 * popt[1]
        - (peak - v0) * popt[0] * (width0 * popt[1] / max(fit_type(x, popt))),
        "k": popt[1] * width0,
        "offset": (v0 - peak) * popt[3],
        "slope": m * popt[4],
    }

    return out


def fit_transmission_resonator_spectroscopy(x, y):
    """
    Create a fit to transmission resonator spectroscopy of the form

    .. math::
    (a / (
        1 + (4 * ((x - f) ** 2) / (b ** 2)))) + c

    for unknown parameters `a`, `b`, `c`, `f`.

    :param x:  The data on the x axis
    :param y: The data on the y axis
    :return: A dictionary of (fit_func, f, kc, k, ki, offset
        fit_func - The fitted function
        f - The frequency at the peak
        kc - The strength with which the field of the resonator couples to the transmission line
        ki - A parameter that indicates the internal coherence properties of the resonator
        k - The FWHM of the fitted function.  k = ki + kc
        offset - The offset

    """

    y = np.array(y)

    # Finding a guess for the max
    peak = max(y)
    arg_max = y.argmax()

    # Finding an initial guess for the FWHM
    if arg_max > len(y) / 2:
        y_FWHM = (peak + np.mean(y[0:10])) / 2
    else:
        y_FWHM = (peak + np.mean(y[-10:-1])) / 2

    # Finding a guess for the width
    width0_arg_right = (np.abs(y_FWHM - y[arg_max + 1 : len(y)])).argmin() + arg_max
    width0_arg_left = (np.abs(y_FWHM - y[0:arg_max])).argmin()
    width0 = x[width0_arg_right] - x[width0_arg_left]

    # Finding the frequency at the min
    f0 = x[arg_max]

    # Finding a guess to offset
    v0 = np.mean(y[0 : int(width0_arg_left - width0 / 2)])

    fit_type = lambda x, a: (
        ((peak - v0) * a[0])
        / (1 + (4 * ((x - (f0 * a[2])) ** 2) / ((width0 * a[1]) ** 2)))
    ) + (v0 * a[3])

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [1, 1, 1, 1, 1, 0.1])

    print(
        f"f = {f0 * popt[2]}, kc = {(peak - v0) * popt[0]*(width0 * popt[1]/max(fit_type(x, popt)))}, ki = {width0 * popt[1]-(peak - v0) * popt[0]*(width0 * popt[1]/max(fit_type(x, popt)))}, k = {width0 * popt[1]}, offset =  {v0 * popt[3]}"
    )
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "f": f0 * popt[2],
        "kc": (peak - v0) * popt[0] * (width0 * popt[1] / max(fit_type(x, popt))),
        "ki": width0 * popt[1]
        - (peak - v0) * popt[0] * (width0 * popt[1] / max(fit_type(x, popt))),
        "k": popt[1] * width0,
        "offset": v0 * popt[3],
    }

    return out
