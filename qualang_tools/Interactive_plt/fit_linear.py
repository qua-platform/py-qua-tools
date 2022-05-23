from scipy import optimize
import numpy as np


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
