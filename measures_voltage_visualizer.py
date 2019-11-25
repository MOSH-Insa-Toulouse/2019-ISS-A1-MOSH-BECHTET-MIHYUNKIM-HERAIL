"""
Author: Philippe Hérail

GUI Program to measure current and energy used from CSV exported data from MCUXpresso power measurement tool.
Could also be used with a CSV with columns TIME(s) and CURRENT(A).
Based on PyQtGraph.

The GUI sport a crosshair that shows the X & Y values under the cursor.
It is also possible to click on point and place a vertical line (drag the line left and right tocreate a region) to measure power used, duration... (right panel) for a given period. Click to reset the region.
The compute button compute the values in the panel for the selected region.
The supply voltage use for calculation can be set in the UALIM box.
For an unknown reason, upon click, the vertical bar is placed slightly to the left (does not impact the performance)

Export to matplotlib (with right click), and then to pdf the best printable results.

Data is peak downsampled by default.

TODO: 
* Make the computation and GUI separate threads, for smoother zoom/resize
* The "Export to matplotlib" button in the top menu bar is currently not doing anything, need to add default matplotlib export settings.
* Add application icon

"""

import numpy as np
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import PyQt5.QtWidgets as qw
from pyqtgraph.Point import Point

# Setup the GUI
# Config pyqtgraph
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

# generate main layout
app = QtGui.QApplication([])
mw = qw.QMainWindow()
win = pg.GraphicsLayoutWidget()
win.useOpenGL(False) # OpenGL buggy on my computer
mLayout = qw.QHBoxLayout()

# Set central widget
cw = qw.QWidget()
cw.setLayout(mLayout)
mw.setCentralWidget(cw)
label = pg.LabelItem(justify='right')
win.addItem(label)
p1 = win.addPlot(row=1, col=0)
mLayout.addWidget(win)

# Add menu bar
menuFile = qw.QMenu("File")
actionFileOpen = qw.QAction("Open file")
menuFile.addAction(actionFileOpen)
actionExportMatplot = qw.QAction("Export to Matplotlib")
menuFile.addAction(actionExportMatplot)
mw.setMenuBar(qw.QMenuBar())
mw.menuBar().addMenu(menuFile)


# Add groupbox "Energy consumed"
groupEnergy = qw.QGroupBox()
groupEnergy.setTitle("Energy")
vGroupLayout = qw.QVBoxLayout()
groupEnergy.setLayout(vGroupLayout)

ualimLabel = qw.QLabel("Ualim (V):")
vGroupLayout.addWidget(ualimLabel)
ualimSpin = qw.QDoubleSpinBox()
ualimSpin.setValue(5.12)
vGroupLayout.addWidget(ualimSpin)
# set result box
computeResult = qw.QLineEdit()
computeResult.setReadOnly(True)
computeResult.setAlignment(QtCore.Qt.AlignCenter)
vGroupLayout.addWidget(computeResult)

# Add compute button
buttonCompute = qw.QPushButton("Compute")
vGroupLayout.addWidget(buttonCompute)

groupEnergy.setMaximumWidth(buttonCompute.minimumSizeHint().width()*3)
vGroupLayout.setAlignment(QtCore.Qt.AlignTop)

# Right info pane add to the layout
vInfoLayout = qw.QVBoxLayout()

# Add groupbox "Information"
groupInfo = qw.QGroupBox()
groupInfo.setTitle("Information")
groupInfo.setMaximumWidth(buttonCompute.minimumSizeHint().width()*3)
vGroupInfoLayout = qw.QVBoxLayout()
groupInfo.setLayout(vGroupInfoLayout)
labBoxDelta = qw.QLabel("\u0394t: ")
labAvgCurrent = qw.QLabel("Average current: ")
labAvgPower = qw.QLabel("Average power: ")
vGroupInfoLayout.addWidget(labBoxDelta)
vGroupInfoLayout.addWidget(labAvgCurrent)
vGroupInfoLayout.addWidget(labAvgPower)
vGroupInfoLayout.setAlignment(QtCore.Qt.AlignTop)

vInfoLayout.addWidget(groupInfo)
vInfoLayout.addWidget(groupEnergy)

# Add line width slider
# FIXME: Very slow when zoomed with bigger size, probably a rendering issue

widthLabel = qw.QLabel("Line Width: <br> <font color=\"red\">WARNING: Slow!</font>")
vInfoLayout.addWidget(widthLabel)
sliderPen = qw.QSlider()
sliderPen.setMaximum(10)
sliderPen.setMinimum(1)
sliderPen.setOrientation(QtCore.Qt.Horizontal)
sliderPen.setMaximumWidth(buttonCompute.minimumSizeHint().width()*3)
vInfoLayout.addWidget(sliderPen)

#Add panel layout to right size
mLayout.addLayout(vInfoLayout)
mLayout.setAlignment(QtCore.Qt.AlignTop)
vInfoLayout.setAlignment(QtCore.Qt.AlignTop)


region = pg.LinearRegionItem()
region.setZValue(10)

p1.setAutoVisible(y=True)


def openFileNameDialog(widget):
    """
        Opens a window to select the file to load
    """
    options = qw.QFileDialog.Options()
    options |= qw.QFileDialog.DontUseNativeDialog
    fileName, _ = qw.QFileDialog.getOpenFileName(
        widget, "qw.QFileDialog.getOpenFileName()", "", "All Files (*)", options=options)
    return fileName


# Config pyqtgraph
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

# quite ugly global varaibles, but way simpler
dataFrame = pd.DataFrame()
lastIndex = 0

# crosshair declare
vLine = pg.InfiniteLine(angle=90, movable=False)
hLine = pg.InfiniteLine(angle=0, movable=False)


def loadDataFile(openDialog=True):
    """
        Load a data file selected from a dialog windows.
        If openDialog=False, creates an empty data frame (used to start the program without data)
    """
    global dataFrame
    dataPath = openFileNameDialog(mw) if openDialog else ''
    if not dataPath:
        dataFrame = pd.DataFrame([[0, 0], [5, 0]], columns=["time", "current"])
    else:
        dataFrame = pd.read_csv(dataPath,
                                sep=",",
                                header=0, names=["time", "voltage", "current"])  # replaces column names

    # Uncomment line below if data has numbers with french formatting
    # dataFrame["current"] = dataFrame["current"].str.replace(
    #     ',', '.').astype(float)

    dataFrame.current *= 1000  # convert to mA
    # dataFrame.time *= 1e-6  # convert to s

    dataFrame.set_index("time", drop=False, inplace=True)

    global lastIndex
    lastIndex = dataFrame.last_valid_index()

    p1.setDownsampling(ds=1, auto=True, mode='peak')
    p1.setLabels(left="Current (mA)",
            bottom="Time (s)")

    p1.plot(dataFrame["time"].values,
            dataFrame["current"].values,
            pen="b",
            clear=True)
            
    mw.setWindowTitle(dataPath)

    p1.showGrid(x=True, y=True)

    region.setRegion([1e4, 2e4])

    # cross hair
    p1.addItem(vLine, ignoreBounds=True)
    p1.addItem(hLine, ignoreBounds=True)
    # Add the LinearRegionItem to the ViewBox, but tell the ViewBox to exclude this
    # item when doing auto-range calculations.
    p1.addItem(region, ignoreBounds=True)

def myround(x, base=5):
    return base * round(x/base)


def mouseMoved(evt):
    """
        Handle the event from the mouse.

        Mainly updates the crosshair and top right values.
    """
    if len(dataFrame.index):
        pos = evt[0]  # using signal proxy turns original arguments into a tuple
        mousePoint = vb.mapSceneToView(pos)
        # Needed to round the values to multiple of 5,
        # otherwise the index may not be defined for accessing values in the dataframe.
        # Change according to the sampling rate.
        index = int(mousePoint.x())
        if index < lastIndex:
            try:
                val = pg.siFormat(mousePoint.y()/1000, 3, 'A')
                time = pg.siFormat(mousePoint.x(), 3, 's')
                label.setText("<span style='font-size: 12pt'>time=%s,   <span style='color: red'>y1=%s</span>" %
                              (time, val))

            except KeyError:
                pass
            vLine.setPos(mousePoint.x())
            hLine.setPos(mousePoint.y())


def mouseClicked(evt):
    """
        Handles the mouse clicked events

        Mainly set the position of the vertical bar for creating the region
        for computation.

        FIXME: The bar is put on the left of the actual click location
    """
    if evt.button() == QtCore.Qt.LeftButton and len(dataFrame.index):
        pos = evt.pos()
        mousePoint = vb.mapSceneToView(pos)
        index = int(mousePoint.x())
        if index < lastIndex:
            region.setRegion([index, index])


def compute():
    """
        Function used to compute the info shown in the right side panel
        from tjhe selected region. 
    """
    if len(dataFrame.index):
        u = ualimSpin.value()
        bounds = region.getRegion()
        slicedDf = dataFrame.loc[bounds[0]:bounds[1]]
        computeResult.setText(pg.siFormat(
            np.trapz(slicedDf.current.values/1000*u, slicedDf.time.values), 3, 'J'))

        # Info computations
        delta = (region.getRegion()[1]-region.getRegion()[0])
        integ = np.trapz(slicedDf.current.values/1000,
                         slicedDf.time.values)/delta
        avgCurr = pg.siFormat(integ, 3, 'A')
        labAvgCurrent.setText(f"Average current: {avgCurr}")
        avgPow = pg.siFormat(integ*u, 3, 'W')
        labAvgPower.setText(f"Average power: {avgPow}")
        delta = pg.siFormat(delta, 3, 's')
        labBoxDelta.setText(f"\u0394t: {delta}")

def loadDataFileSlot():
    """
        Signal/slot compatible wrapper for loadDataFile function 
    """
    loadDataFile()

def setPenWidthSlot(val):
    """
        Signal handler for pen width slider    
    """
    p1.listDataItems()[0].setPen(color='b',width=val)

def exportMatplotSlot():
    """
        Signal handler for menu action "Export to matplotlib"

        TODO: Implement
    """
    msgBox = qw.QMessageBox();
    msgBox.setIcon(qw.QMessageBox.Information)
    msgBox.setText("Function not implemented yet");
    msgBox.exec();
    # exporter = pg.exporters.MatplotlibExporter(p1.listDataItems()[0])
    # exporter.parameters()


# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    # Initialize the window
    loadDataFile(False)

    vb = p1.vb
    # Set the mouse behavior (can be changed with a right click in the program)
    vb.setMouseMode(vb.RectMode)

    # Connects signal and slots

    # The signal proxy limits the rate of the mouse moved event to not overload the application
    proxy = pg.SignalProxy(p1.scene().sigMouseMoved, rateLimit=30, slot=mouseMoved)
    p1.scene().sigMouseClicked.connect(mouseClicked)
    buttonCompute.clicked.connect(compute)
    actionFileOpen.triggered.connect(loadDataFileSlot)
    actionExportMatplot.triggered.connect(exportMatplotSlot)
    sliderPen.valueChanged.connect(setPenWidthSlot)

    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        mw.show()
        QtGui.QApplication.instance().exec_()
