from scipy import optimize
import numpy as np


def fit_decay_sine(x, y):

    w = np.fft.fft(y)
    freqs = np.fft.fftfreq(len(x))
    new_w = w[1: len(freqs // 2)]
    new_f = freqs[1: len(freqs // 2)]

    ind = new_f > 0
    new_f = new_f[ind]
    new_w = new_w[ind]

    yy = np.abs(new_w)
    first_read_data_ind = np.where(yy[1:] - yy[:-1] > 0)[0][0]  # away from the DC peak

    new_f = new_f[first_read_data_ind:]
    new_w = new_w[first_read_data_ind:]

    out_freq = new_f[np.argmax(np.abs(new_w))]
    new_w_arg = new_w[np.argmax(np.abs(new_w))]

    omega = out_freq * 2 * np.pi / (x[1] - x[0])  # get guess for frequency #here

    cycle = int(np.ceil(1 / out_freq))
    peaks = np.array([np.std(y[i * cycle: (i + 1) * cycle]) for i in range(int(len(y) / cycle))]) * np.sqrt(2) * 2

    initial_offset = np.mean(y[:cycle])
    cycles_wait = np.where(peaks > peaks[0] * 0.37)[0][-1]

    post_decay_mean = np.mean(y[-cycle:])


    decay_guess = (np.log(peaks[0] / peaks[cycles_wait]) / (cycles_wait * cycle) / (x[1] - x[0]))  # get guess for decay #here

    fit_type = lambda x, a: post_decay_mean * a[4] * (1 - np.exp(-x * decay_guess * a[1])) + peaks[0] / 2 * a[2] * (
            np.exp(-x * decay_guess * a[1])
            * (a[5] * initial_offset / peaks[0] * 2 + np.cos(2 * np.pi * a[0] * omega / (2 * np.pi) * x + a[3]))
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

    m0 = (y[-1]-y[0])/(x[-1]-x[0])
    if np.where(y==0)[0].tolist() != []:
        ind = np.where(np.array(y) == 0)[0]
        n0 = y[ind]
    elif y[0] > 0:
        n0 = y[0]
    else:
        n0 = y[-1]


    fit_type = lambda x, a: a[0] * x + a[1]

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [m0, n0])

    print(
        f"a = {popt[0]}, b = {popt[1]}"
    )
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
    fit_type = lambda x, a: (((a[0] / 2) * (x - a[3])) / ((a[1] ** 2 / 4) + ((x - a[3]) ** 2))) + v0 * a[2]

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [1, 1, 1, 1])

    print(
        f"amp*kc = {popt[0]}, k = {popt[1]}, offset = {v0 * popt[2]}"
    )
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "amp*kc": popt[0],
        "k": popt[1],
        "w": popt[3],
        "offset": v0 * popt[2],
    }

    return out


def fit_reflection_resonator_spectroscopy(x, y):
    peak0 = min(y) #find guess to peak
    #find guess to width
    arg_min = y.argmin()
    width0_arg_right = (np.abs(peak0 / 2 - y[arg_min:len(y)])).argmin() + arg_min
    width0_arg_left = (np.abs(peak0 / 2 - y[0:arg_min])).argmin()
    width0 = x[width0_arg_right] - x[width0_arg_left]
    w0 = x[arg_min]
    # offset = min(y)
    # inc = (max(y)-min(y))/(x[y.argmax()]-x[y.argmin()])
    # find guess of offset
    v0 = y[0]
    fit_type = lambda x, a: (peak0/width0) * a[0] - ((((peak0/width0) * a[0] * a[2]) / (width0 * a[1])) / (1 + 4/((width0 * a[1]) ** 2) * ((x-(w0 * a[3])) ** 2)))

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [1, 1, 1, 1])

    print(
        f"offset = {(peak0/width0) * popt[0]}, k = {width0 * popt[1]}, kc = {popt[2]}, ki = {width0 * popt[1] - popt[2]}, w = {w0 * popt[3]}"
    )
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "offset": popt[0]*(peak0/width0),
        "k": popt[1]*width0,
        "kc": popt[2],
        "ki": width0 * popt[1] - popt[2],
        "w": w0 * popt[3],

    }

    return out


def fit_transmission_resonator_spectroscopy(x, y):
    # find guess to peak
    peak0 = max(y)
    # find guess to width
    arg_max = y.argmax()
    width0_arg_right = (np.abs(peak0 / 2 - y[arg_max:len(y)])).argmin() + arg_max
    width0_arg_left = (np.abs(peak0 / 2 - y[0:arg_max])).argmin()
    width0 = x[width0_arg_right] - x[width0_arg_left]
    # offset = min(y)
    # inc = (max(y)-min(y))/(x[y.argmax()]-x[y.argmin()])
    w0 = x[arg_max]
    # find guess of offset
    v0 = y[0]

    fit_type = lambda x, a: (((peak0/width0 * a[0])/2) * (width0 * a[1])/2) / (1 + 4/((width0 * a[1]) ** 2) * ((x-(w0 * a[2])) ** 2)) + v0 * a[3]
    # fit_type = lambda x, a: ((peak0/width0) * a[0] * a[2] / (width0 * a[1])) / (1 + 4/((width0 * a[1]) ** 2) * ((x-(w0 * a[3])) ** 2)) + v0 * a[4]

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [1, 1, 1, 1])

    print(
        f"kc = {peak0/width0 * popt[0]}, k = {width0 * popt[1]}, ki = {width0 * popt[1] - peak0/width0 * popt[0]}, w = {w0 * popt[2]}, offset =  {v0 * popt[3]}"
    )
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "kc": popt[0],
        "k": popt[1]*width0,
        "ki": width0 * popt[1] - peak0/width0 * popt[0],
        "w": w0 * popt[2],
        "offset": v0 * popt[3],
    }

    return out
