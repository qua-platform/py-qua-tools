from scipy import optimize
import numpy as np


def fit_phase(x, y):
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
