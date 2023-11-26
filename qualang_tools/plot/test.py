from fitting import Fitting
from fitting.fit_classes import TripleLorentzian
from fitting.fit_classes import DoubleLorentzian
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import numpy as np

def lorentz(x, x0, fwhm, scale):
    return scale/np.pi * (fwhm / 2) / ((x - x0)**2 + (fwhm/2)**2)

def multi_lorentz(x, x0s, lambdas, scales, offset, noise_scale=1):

    out = offset - np.sum(np.array([lorentz(x, x0, lam, scale) for x0, lam, scale in zip(x0s, lambdas, scales)]), axis=0)
    noise = np.random.rand(out.size) * noise_scale

    return out + noise


x = np.linspace(-5, 5, 100)

def abs(x, m, c, x0):
    return np.abs(m * (x - x0)) + c

m = 2
c = 3
x0 = 1

y = abs(x, m, c, x0)


plt.figure()
plt.plot(x, y)
plt.show()

# x = np.linspace(1825, 1835, 101)
# x0s = [1827.5, 1829.8, 1832]
# lambdas = [0.8, 0.8, 0.8]
# scales = [3, 3, 3]
# offset = 19.5
# noise_scale = 1

# y = multi_lorentz(x, x0s, lambdas, scales, offset, noise_scale)
#
# plt.figure()
# plt.plot(x, y)
# plt.show()


#
# # tl = triple_lorentzian(x, y, plot=True, verbose=True)
#
# file_a = '/Users/joseph/Downloads/1.dat'
# file_b = '/Users/joseph/Downloads/2.dat'
#
# def file_to_np(filename):
#     data = []
#     with open(filename, 'r') as file:
#         d = file.readlines()
#
#         for i in d[21:]:
#             k = i.rstrip('\n').split('\t')
#             data.append(list(map(float, k)))
#
#     return np.array(data)
#
#
# x1, y1 = file_to_np(file_a).T
# x2, y2 = file_to_np(file_b).T
#
# # fit_1 = triple_lorentzian(x1, y1, plot=True)
#
# plt.figure()
# plt.plot(x2, y2)
# plt.show()
#
#
# fit_1 = TripleLorentzian(x1, y1, plot=True)
# fit_2 = TripleLorentzian(x2, y2, plot=True)