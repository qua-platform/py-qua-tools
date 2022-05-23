from scipy import optimize
import numpy as np


def fit_transmission(x, y):
    # find guess to peak
    peak0 = max(y)
    # find guess to width
    arg_max = y.argmax()
    width0_arg_right = (np.abs(peak0 / 2 - y[arg_max : len(y)])).argmin() + arg_max
    width0_arg_left = (np.abs(peak0 / 2 - y[0:arg_max])).argmin()
    width0 = x[width0_arg_right] - x[width0_arg_left]
    # offset = min(y)
    # inc = (max(y)-min(y))/(x[y.argmax()]-x[y.argmin()])
    w0 = x[arg_max]
    # find guess of offset
    v0 = y[0]

    fit_type = (
        lambda x, a: (((peak0 / width0 * a[0]) / 2) * (width0 * a[1]) / 2)
        / (1 + 4 / ((width0 * a[1]) ** 2) * ((x - (w0 * a[2])) ** 2))
        + v0 * a[3]
    )
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
        "k": popt[1] * width0,
        "ki": width0 * popt[1] - peak0 / width0 * popt[0],
        "w": w0 * popt[2],
        "offset": v0 * popt[3],
    }

    return out
