# Introduction
This package includes tools which are still a work-in-progress. 

## InteractivePlotLib
This package drastically extends the capabilities of matplotlib, enables easily editing various parts of the figure, 
copy-pasting data between figures and into spreadsheets, fitting the data and saving the figures.

It is currently experimental and only supports win32 with IPython.

## Example
```python
from qualang_tools.experimental.InteractivePlotLib import InteractivePlotLib 
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erf

# Make sure c:\data exists, you can specify any other empty directory.
# This is where the data will be stored.
Qplt = InteractivePlotLib("c:\data")

x = np.linspace(-10, 10, 2001)

y1 = 3 * np.exp(-((x - 4) ** 2) / (2 * 2 ** 2)) + 0.1 * np.random.rand(len(x))
y2 = -erf(x) + np.random.rand(len(x)) * 0.1
y3 = 1 * np.exp(-((x + 4) ** 2) / (2 * 4 ** 2)) + 0.1 * np.random.rand(len(x))

Qplt.figure(1)
plt.clf()
plt.plot(x, y1)
plt.plot(x, y2)

Qplt.figure(2)
plt.clf()
plt.plot(x, y3)
```

## Commands
- Click on title area - write the title
- Click on xlabel area - write xlabel
  - Write command using the ":" symbol
    - ":lin" for linear scale, ":log" for log scale
    - ":f(x)" (for example ":2*x", "x**2") to scale the data by a function.
    - ":u" - change units. For example, for the label x[V], click then write :u, then x[mV] to change the scale
- Click on ylabel area - write ylabel
  - Write command using the ":" symbol
    - Same commands as xlabel. use ":f(y)" for function scaling.
- Click near the edge of axes (near the numbers) to set a limit xlim or ylim
- Click outside the canvas on the right side to set a legend.
- Use up/down arrows to move between curves
- Click on a curve to select it
  - Copy - when selected, ctrl-c to copy it. you can paste it to another figure or excel/notepad
    - Can also copy-paste from excel to a figure, need x,y coordinates.
  - C - color, change color to r,g,b,m,k etc
  - Up/down - shift the order of curves in the figure
  - 1...9 - click on a number to change line width
  - Delete
- s - Save data.
  - Will save the open figures in the directory specified. Try it!
  - You can load the data later by: out = Qplt.load(n) where n is the "scan number"
    - This will load the data into the workspace, and out["code"] is the code you used.
- g - grid.
- m - Marker mode - Click any point on a curve or point.
  - Shift+m to add a new marker.
  - Alt+m to clear all markers
- f - fit (only on the visible range):
  - 0..9 - Polynomial fit.
  - g - Gaussian
  - l - Lorenzian
  - e - Exponent
  - r - Erg
  - s - Sine
  - f(x) - User defined - For example: "x**2 * a[0] + a[1], [1,1]" will fit to a parabola with initial gauss for a: [1,1]
  - The output is recorded in the "fit" variable in the main workspace.
  - For example, fit["x_shift"] after a gaussian fit will give the peak location
  - Each type of fit will have different fields. Special points are marked with red dots.
  - Alt+f to remove fit