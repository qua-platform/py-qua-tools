
# Commands:

# Click on title area - write title

# Click on xlabel area - write xlabel
#   write command using the ":" symbol
#       ":lin" for linear scale, ":log" for log scale
#       ":f(x)" (for example ":2*x", "x**2") to scale the data by a function.
#       ":u" - change units. for example, for the label x[V], click then write :u, then x[mV] to change the scale

# Click on ylabel area - write ylabel
#   same commands as xlabel. use ":f(y)" for function scaling

# Click near edge of axes (near the numbers) to set a limit xlim or ylim

# Click outside the canvas on the right side to set a legend.
#   Use up/down arrows to move between curves

# Click on a curve to select it
#   Copy - when selected, ctrl-c to copy it. you can paste it to another figure or excel/notepad
#       you can also copy paste from excel to a figure, need x,y coordinates.
#   C - color, change color to r,g,b,m,k etc
#   Up/down - shift order of curves in figure
#   1...9 - click on a number to change line width
#   Delete

# s - Save data.
#       Will save the open figures in the directory specify. Try it!
#       you can load the data later by: out = Qplt.load(n) where n is the "scan number"
#       This will load the data in workspace, and out["code"] is the code you used.

# g - grid.

# m - Marker mode - click any point on a curve, or point. shift+m to add new marker. alt+m to clear all markers

# f - fit (only on the visible range):
#   0..9 - polynom fit.
#   g - gaussian
#   l - lorenzian
#   e - exponent
#   r - erg
#   s - sine
#   f(x) - user defined - for example: "x**2 * a[0] + a[1], [1,1]" will fit to a parabola with initial gauss for a as [1,1]
#   the output is recorded in the "fit" variable in the main workspace.
#   for example, fit["x_shift"] after a gaussian fit will give the peak location
#   each type of fit will have different fields. special points are marked with red dots.
#   alt+f to remove fit

# %% practical example
from InteractivePlotLib import InteractivePlotLib
import numpy as np
import matplotlib.pyplot as plt
import scipy

# Make sure c:\data exists, you can specify any other empty directory.
# This is where the data will be stored.
Qplt = InteractivePlotLib("c:\\data")

x = np.linspace(-10, 10, 2001)

y1 = 3 * np.exp(-((x - 4) ** 2) / (2 * 2 ** 2)) + 0.1 * np.random.rand(len(x))
y2 = -scipy.special.erf(x) + np.random.rand(len(x)) * 0.1
y3 = 1 * np.exp(-((x + 4) ** 2) / (2 * 4 ** 2)) + 0.1 * np.random.rand(len(x))

fig = Qplt.figure(1)
plt.clf()
plt.plot(x, y1)
plt.plot(x, y2)

fig = Qplt.figure(2)
plt.clf()
plt.plot(x, y3)
