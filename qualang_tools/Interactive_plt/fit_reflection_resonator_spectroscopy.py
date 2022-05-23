from scipy import optimize
import numpy as np


def fit_reflection(x, y):
    # find guess to peak
    peak0 = min(y)
    # find guess to width
    arg_min = y.argmin()
    width0_arg_right = (np.abs(peak0 / 2 - y[arg_min:len(y)])).argmin() + arg_min
    width0_arg_left = (np.abs(peak0 / 2 - y[0:arg_min])).argmin()
    width0 = x[width0_arg_right] - x[width0_arg_left]
    w0 = x[arg_min]
    # offset = min(y)
    # inc = (max(y)-min(y))/(x[y.argmax()]-x[y.argmin()])
    # find guess of offset
    v0 = y[0]
    fit_type = lambda x, a: (peak0 / width0) * a[0] - ((((peak0 / width0) * a[0] * a[2]) / (width0 * a[1])) / (
            1 + 4 / ((width0 * a[1]) ** 2) * ((x - (w0 * a[3])) ** 2)))

    def curve_fit(f, x, y, a0):
        def opt(x, y, a):
            return np.sum(np.abs(f(x, a) - y) ** 2)

        out = optimize.minimize(lambda a: opt(x, y, a), a0)
        return out["x"]

    popt = curve_fit(fit_type, x, y, [1, 1, 1, 1])

    print(
        f"offset = {(peak0 / width0) * popt[0]}, k = {width0 * popt[1]}, kc = {popt[2]}, ki = {width0 * popt[1] - popt[2]}, w = {w0 * popt[3]}"
    )
    out = {
        "fit_func": lambda x: fit_type(x, popt),
        "offset": popt[0] * (peak0 / width0),
        "k": popt[1] * width0,
        "kc": popt[2],
        "ki": width0 * popt[1] - popt[2],
        "w": w0 * popt[3],

    }

    return out
