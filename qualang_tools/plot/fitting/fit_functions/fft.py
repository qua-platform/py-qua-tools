import numpy as np
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

def fft(t, data, plot=False):


    fft_data = np.fft.fft(data)

    N = len(fft_data)
    n = np.arange(N)

    sample_interval = np.abs(t[1] - t[0]) # just to make sure it's positive
    sample_rate = 1 / sample_interval

    T = N / sample_rate
    freqs = n / T

    frequencies = freqs[range(int(N/2))]
    y = fft_data / N # normalised
    y = y[range(int(N/2))]

    if plot:
        plt.figure()
        plt.plot(frequencies, np.abs(y))
        plt.show()

    return frequencies, np.abs(y)


def fit_peaks(frequencies, amplitudes, plot=False):

    peaks, properties = find_peaks(amplitudes, prominence=0.1)

    peak_frequencies = frequencies[peaks]
    peak_heights = amplitudes[peaks]

    if plot:
        plt.figure()
        plt.plot(frequencies, amplitudes)
        plt.scatter(peak_frequencies, peak_heights)
        plt.show()

    return peak_frequencies




def find_frequencies(t_data, y_data, plot=False):
    return fit_peaks(*fft(t_data, y_data), plot=plot)

# sampling rate
sr = 2000
# sampling interval
ts = 1.0/sr
t = np.arange(0,1,ts)

freq = 1.
x = 3*np.sin(2*np.pi*freq*t)

freq = 4
x += np.sin(2*np.pi*freq*t)

freq = 7
x += 0.5* np.sin(2*np.pi*freq*t)

plt.figure(figsize = (8, 6))
plt.plot(t, x, 'r')
plt.ylabel('Amplitude')

plt.show()

