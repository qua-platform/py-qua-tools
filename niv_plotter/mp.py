import pyqtgraph as pg
pg.mkQApp()

# Create remote process with a plot window
import pyqtgraph.multiprocess as mp
proc = mp.QtProcess()
rpg = proc._import('pyqtgraph')
plotwin = rpg.plot()
curve = plotwin.plot(pen='y')

# create an empty list in the remote process
data = proc.transfer([])

# Send new data to the remote process and plot it
# We use the special argument _callSync='off' because we do
# not want to wait for a return value.
data.extend([1,5,2,4,3], _callSync='off')
curve.setData(y=data, _callSync='off')
