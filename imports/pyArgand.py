#!/usr/bin/python
# -*- coding: utf-8 -*-

#    Copyright © 2010 Giuseppe Mercurio
#    Copyright © 2013-2018 Francois C. Bocquet
#    Copyright © 2014-2018 Markus Franke
#    This file is part of Torricelli.
#
#    Torricelli is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    Torricelli is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Torricelli.  If not, see <http://www.gnu.org/licenses/>.

# Use svn keyword to retrieve Revision number automatically on commit
# The String between the $ will automatically be changed by SVN
# Do not forget to activate the keyword for the file by for example
# svn propset svn:keywords 'Id Revision LastChangedDate LastChangedBy' pyArgand.py
# DO NOT CHANGE THE FOLLOWING LINES, unless you know what you are doing
__revision__  = filter(str.isdigit, "$Revision: 482 $")
__modDate__   = "$LastChangedDate: 2018-04-16 06:56:45 +0200 (Mo, 16. Apr 2018) $"
__modDate__   = __modDate__[49:61] + ' ' + __modDate__[28:38] + 'GMT' + __modDate__[38:43]
__changedBy__ = "$LastChangedBy: m.franke $".split(' ')[1]
__svnID__     = "$Id: pyArgand.py 482 2018-04-16 04:56:45Z m.franke $"

# insert version number here, if this is a full release
__version__ = '2.2.' + __revision__

import numpy as np
import sys
import os
import datetime
import colorsys
import pyqtgraph as pg
import numbers
from scipy.ndimage import gaussian_filter1d
from PyQt4 import QtCore, QtGui
from pyqtgraph.Qt import QtGui, QtCore, USE_PYSIDE
pg.setConfigOption('background', None)# means transparent background
pg.setConfigOption('foreground', 'k')
from PyQt4.QtCore import pyqtSignal, pyqtSlot


class QGraphicsArcItem(pg.QtGui.QGraphicsEllipseItem):
    #see: http://stackoverflow.com/questions/14279162/qt-qgraphicsscene-drawing-arc
    # pos should be a list [pc,fc]
    # color (r,g,b)
    def __init__(self, pos, pc_err, color):
        pg.QtGui.QGraphicsEllipseItem.__init__(self)
        self.pos = pos
        self.pc_err = pc_err
        self.color = QtGui.QColor(color[0], color[1], color[2])


    ## redefine the paint function to draw arcs.
    def paint(self, painter, option, widget=0):
        radius = self.pos[1]
        rect = QtCore.QRectF(-1*radius, -1*radius, 2*radius, 2*radius)
        startAngle = int( -360*16* (self.pos[0] + self.pc_err)) #360*16: full circle
        spanAngle  = int(  360*16* self.pc_err*2)
        painter.setPen(self.color)
        painter.drawArc(rect, startAngle, spanAngle)


## Redefining the standard pyqtgraph class to enable easy drawing of a polar plot.
class ArgandPlotWidget(pg.PlotWidget): # fig is ignored, just here for compatibility the other plot options
    def __init__(self):
        pg.PlotWidget.__init__(self)
        self.setAspectLocked()
        self.setAntialiasing(True) # looks prettier
        self.keysSelectedBefore = set()
        self.standardSizeOriginVector = 10
        self.standardSizeDataSet = 6
        self.setCursor(QtCore.Qt.CrossCursor)
        self.vectorList = []
        self.originVectorDict = {}
        self.dataSetDict = {}
        self.splitVectorList = []
        self.errorBarDictPc = {}
        self.errorBarDictFc = {}
        self.polarGridLines = []
        self.radialGridLines = []
        self.radialTickmarks = []
        self.radialTickLabels = []
        self.createAxisAndGrid()
        self.__version__   = __version__
        self.__revision__  = __revision__
        self.__modDate__   = __modDate__
        self.__changedBy__ = __changedBy__
        self.__svnID__     = __svnID__



    def createAxisAndGrid(self, polarGridNr = 10.0, radialGridNr = 20.0):
        # Add polar "Axis"
        self.polarAxis = pg.QtGui.QGraphicsEllipseItem(-1, -1, 2, 2)
        #self.polarAxis.setStartAngle(500) #Get part of the pie only shown
        #self.polarAxis.setSpanAngle(500)
        self.polarAxis.setPen(pg.mkPen(0.0)) # DotLine
        self.polarAxis.setBrush(pg.mkBrush(1.0)) # circle is filled white
        self.addItem(self.polarAxis)

        # Add polar grid lines
        for r in np.arange(0.1, 1.0, 1.0/polarGridNr):
            self.polarGridLine = pg.QtGui.QGraphicsEllipseItem(-r, -r, r*2, r*2)
            if r==0.2 or r==0.4 or r==0.6 or r==0.8: # draw these lines as solid
                self.polarGridLine.setPen(pg.mkPen(0.7,style=QtCore.Qt.SolidLine,color="r")) # SolidLine, DashLine or DotLine
            else: # the rest as dashed
                self.polarGridLine.setPen(pg.mkPen(0.8,style=QtCore.Qt.DashLine)) # DotLine
            self.polarGridLine.setBrush(pg.mkBrush(None))
            self.polarGridLines.append(self.polarGridLine)
            self.addItem(self.polarGridLine)
        # Add radial grid lines
        self.radialGridParam = [0 , 2.0*np.pi, 2.0*np.pi/radialGridNr] # angles in rad
        for a in np.arange(self.radialGridParam[0],self.radialGridParam[1],self.radialGridParam[2]):
            self.radialGridLine = pg.QtGui.QGraphicsLineItem(0, 0, np.cos(a), np.sin(a))
            self.radialGridLine.setPen(pg.mkPen(0.8,style=QtCore.Qt.DashLine))
            self.radialGridLines.append(self.radialGridLine)
            self.addItem(self.radialGridLine)
        # add radial tickmarks
        for a in np.arange(self.radialGridParam[0],self.radialGridParam[1],self.radialGridParam[2]):
            self.radialGridLine = pg.QtGui.QGraphicsLineItem(np.cos(a), np.sin(a),np.cos(a)*1.03, np.sin(a)*1.03)
            self.radialGridLine.setPen(pg.mkPen(0.0))
            self.radialTickmarks.append(self.radialGridLine)
            self.addItem(self.radialGridLine)
        # add radial tickmarks labels
        for a in np.arange(self.radialGridParam[0],self.radialGridParam[1],self.radialGridParam[2]):
            self.radialGridLineLabel = pg.TextItem(text=str("%.2f" % (a/(2*np.pi))), anchor=(0.5,0.5), color=0.0)
            self.radialGridLineLabel.setPos(np.cos(a)*1.15, np.sin(a)*1.15)
            self.radialTickLabels.append(self.radialGridLineLabel)
            self.addItem(self.radialGridLineLabel)
        # Add (0,0) cross (added last to be in the foreground)
        #self.addLine(x=0, pen=0.0) # Infinte lines
        #self.addLine(y=0, pen=0.0)
        self.plot([0,0],[-1,1], pen=(0,0,0)) # Finite, but sometimes displayed a pixel away, because of antialiasing
        self.plot([-1,1],[0,0], pen=(0,0,0))

        # hiding the "real" axis
        #self.hideAxis("left")


    def changeAxisAndGrid(self, polarGridNr = 10.0, radialGridNr = 20.0):
        # remove old layout
        for i in self.polarGridLines:
            self.removeItem(i)
        for i in self.radialGridLines:
            self.removeItem(i)
        for i in self.radialTickmarks:
            self.removeItem(i)
        for i in self.radialTickLabels:
            self.removeItem(i)
        # draw new layout
        self.createAxisAndGrid(polarGridNr, radialGridNr)


    ## return a [x, y] list
    def convertPcFc_to_cartesian(self, pc, fc):
        return fc*np.cos(2*np.pi*pc), fc*np.sin(2*np.pi*pc)

## template function
#    def addVector(self, p1, p2, fc_err=0, pc_err=0, name='', symb='+', color=(0,0,0)):
#        vec = GraphItemExtended()
#        if 'n' == symb:
#            symbSize=0
#            symb='o'
#        else:
#            symbSize=10
#        x1,y1 = p1[0],p1[1]
#        x2,y2 = p2[0],p2[1]
#        vec.setData(pos=np.array([[x1,y1],[x2,y2]]),size=[1,symbSize],adj=np.array([[0,1]]),symbol=['o',symb],text=['',''], dragable=[False,False], brush=color, pen=color, symbolPen=color, arrowHead=[False,False])
#        self.addItem(vec)
#        self.vectorList.append(vec)


    ## Add a vector (with 0,0 origin) to the polar diagram
    # return a pointer to the vectorItem, so it can be removed with removeItem()
    # the ident parameter allows the user to connect this item with an id to access the item later in the dict
    # the id has to be set
    def addOriginVector(self, pc, fc, fc_err=0, pc_err=0, drawOriginLine = True, drawArrowHead = False, drawError = True, name='', symb='+', size=-1, color=(0,0,0), ident=None):
        if ident==None:
            print("ERROR while adding OriginVector: You have not specified the ident-parameter.\n"\
            +"You have to give each item an unique identification!\n"\
            +"It does not matter if it is an integer number or a string.")
            return
        vec = GraphItemExtended()
        if 'n' == symb:
            symbSize=0
            symb='o'
        elif size==-1:
            symbSize=self.standardSizeOriginVector
        else:
            symbSize=size

        if np.isnan(pc) or np.isnan(fc) or np.isnan(pc_err) or np.isnan(fc_err)\
        or not(isinstance(pc, numbers.Real)) or not(isinstance(fc, numbers.Real)) or not(isinstance(pc_err, numbers.Real)) or not(isinstance(fc_err, numbers.Real)):
            print("\n-------------------------\n## Warning from pyArgand: OriginVector coordinates were not given in int or float or was NaN! ##\n## Set all coordinates to zero.##\n-------------------------\n")
            pc = 0.0
            fc = 0.0
            pc_err = 0.0
            fc_err = 0.0

        vec.setData(pos=np.array([[0,0], self.convertPcFc_to_cartesian(pc,fc)]), size=[1,symbSize], adj=np.array([[0,1]]), symbol=['o',symb], text=['',name], dragable=[False,False], pen=color, symbolBrush=color, symbolPen=color, arrowHead=[False,False])
        if ident == None:
            ident = id(vec)
        if drawOriginLine == True:
            self.addItem(vec)
            self.originVectorDict.update({ident:vec})
            # ErrorBars get the same id as the item they belong to
            if drawError:
                self.addErrorBars([pc, fc], [pc_err, fc_err], color, ident=ident)


    ## Add scattered points
    # return a pointer to the Item (to be removed with removeItem)
    # color can be given (R,G,B), default is black
    # data_argand = [pc, fc]
    # data_err    = [pc_err, fc_err]
    def addDataSet(self, data_argand, data_err, drawError=True, color=(0,0,0), symb='o', size=-1, ident=None):
        if ident==None:
            print("ERROR while adding DataSet: You have not specified the ident-parameter.\n"\
            +"You have to give each item an unique identification!\n"\
            +"It does not matter if it is an integer number or a string.")
            return

        if np.isnan(data_argand[0]) or np.isnan(data_argand[1]) or np.isnan(data_err[0]) or np.isnan(data_err[1])\
        or not(isinstance(data_argand[0], numbers.Real)) or not(isinstance(data_argand[1], numbers.Real)) or not(isinstance(data_err[0], numbers.Real)) or not(isinstance(data_err[1], numbers.Real)):
            print("\n-------------------------\n## Warning from pyArgand: DataSet coordinates were not given in int or float or was NaN! ##\n## Set all coordinates to zero.##\n-------------------------\n")

            data_argand = [0.0, 0.0]
            data_err    = [0.0, 0.0]

        data_cartesian = np.array([self.convertPcFc_to_cartesian(data_argand[0], data_argand[1])]) # needs a list although we treat the points one by one...

        if 'n' == symb:
            symbSize=0
            symb='o'
        elif size==-1:
            symbSize=self.standardSizeDataSet
        else:
            symbSize=size

        ptSet=GraphItemExtended()
        ptSet.setData(pos=data_cartesian, symbolPen=color, symbolBrush=color, size=symbSize, symbol=symb, text=[''], dragable=[False], arraowHead=[False])

        self.addItem(ptSet)
        self.dataSetDict.update({ident:ptSet})

        # ErrorBars get the same id as the item they belong to
        if drawError:
            self.addErrorBars(data_argand, data_err, color, ident=ident)


    ## Add error bars to the given point with the given color
    def addErrorBars(self, data_argand, data_err, color, ident=None):
        if data_err[0]<1e-4 or data_err[1]<1e-4:
            print "==>", data_argand, "<== has none or vanishing Error bars!"
        # Arc of a circle for pc
        errBar_pc = QGraphicsArcItem(data_argand, data_err[0], color)
        # Just a line for fc
        x1,y1 = self.convertPcFc_to_cartesian(data_argand[0], data_argand[1]-data_err[1])
        x2,y2 = self.convertPcFc_to_cartesian(data_argand[0], data_argand[1]+data_err[1])
        errBar_fc = pg.QtGui.QGraphicsLineItem(x1,y1, x2,y2)
        errBar_fc.setPen(pg.mkPen(color))
        self.addItem(errBar_fc)
        self.addItem(errBar_pc)
        if ident==None:
            print "ERROR while adding ErrorBars: errorBars need to be correlated to an object in the QTreeWidget. Set a proper ident parameter!"
            return
        self.errorBarDictPc.update({ident:errBar_pc})
        self.errorBarDictFc.update({ident:errBar_fc})


    ## Display a polygon passing though (0,0) (pc1,fc1) (pc2,fc2) (pc3,fc3) and closing to (0,)
    # Point number 2 is movable and indicated as a bigger dot
    # return a pointer to the vectorItem, so it can be removed with removeItem()
    def addSplitVector(self, pc1, fc1, pc_sum, fc_sum, pc3, fc3, nA, name=['','','','','',''], color=(255,0,0)):
        ### Be careful changing this! You may have to make adjustments in Torricelli.py, too!
        vec = GraphItemExtended()
        vec.setData(pos=np.array([[0,0],
                                  self.convertPcFc_to_cartesian(pc1,fc1),
                                  self.convertPcFc_to_cartesian(pc_sum,fc_sum),
                                  self.convertPcFc_to_cartesian(pc3,fc3),
                                  self.convertPcFc_to_cartesian(pc1,fc1*nA),
                                  self.convertPcFc_to_cartesian(pc3,fc3*(1-nA))]),
                    size=[0,10,0,0,0,0],
                    adj=np.array([[0,4], [4,2], [2,5], [5,0], [4,1], [5,3]]),
                    symbol=['o','o', 'o', 'o', 'o', 'o'],
                    text=name,
                    dragable=[False, True, False, False, False, False],
                    arrowHead=[False, False, False, True, True, True],
                    brush=color, symbolPen=color)
        vec.setPen(pg.mkPen(color=color, style=QtCore.Qt.DashLine))

        self.addItem(vec)
        self.splitVectorList.append(vec)


    ## mark a selected datapoint or origin vector
    def markSelected(self, keysSelectedNow=None):
        sizeDiff = 5
        if keysSelectedNow==None:
            print "ERROR: You have not specified the ident-parameter.\nI do not know what to mark!"
            return

        notSelectedAnymore = self.keysSelectedBefore - set(keysSelectedNow)
        newSelected        = set(keysSelectedNow) -self.keysSelectedBefore
        self.keysSelectedBefore = set(keysSelectedNow)
        # restore look of items that were deselected
        for ident in notSelectedAnymore:
            if ident in self.originVectorDict:
                self.originVectorDict[ident].setSymbolSize([1,self.standardSizeOriginVector])
                self.originVectorDict[ident].setSymbolPen(self.originVectorDict[ident].data['symbolBrush'])
            elif ident in self.dataSetDict:
                self.dataSetDict[ident].setSymbolSize(self.standardSizeDataSet)
                self.dataSetDict[ident].setSymbolPen(self.dataSetDict[ident].data['symbolBrush'])

        # change look of selected items
        for ident in newSelected:
            if ident in self.originVectorDict:
                self.originVectorDict[ident].setSymbolSize([1,self.standardSizeOriginVector+sizeDiff])
                self.originVectorDict[ident].setSymbolPen(pg.mkPen(color='k',width=2))
                self.originVectorDict[ident].setPen(color=self.originVectorDict[ident].data['pen'], width=3)
            elif ident in self.dataSetDict:
                self.dataSetDict[ident].setSymbolSize(self.standardSizeDataSet+sizeDiff)
                self.dataSetDict[ident].setSymbolPen(pg.mkPen(color='k',width=2))
            # else:
            #     print "ERROR in pyArgand: Item that is supposed to be marked is non existant"
            #     print "Key not found: ",ident


    ## Remove a single originVector together with its ErrorBars
    def remove_originVector(self, ident=None):
        if ident==None:
            print "ERROR: You have not specified the ident-parameter.\nI do not know what to delete!"
            return
        self.removeItem(self.originVectorDict[ident])
        self.remove_ErrorBars(ident)


    ## Remove a single dataSet together with its ErrorBars
    def remove_dataSet(self, ident=None):
        if ident==None:
            print "ERROR: You have not specified the ident-parameter.\nI do not know what to delete!"
            return
        self.removeItem(self.dataSetDict[ident])
        self.remove_ErrorBars(ident)


    ## removes a pair of errorBars if the exist
    # they do not exist if the user decides to plot without errorBars
    def remove_ErrorBars(self, ident):
        if ident==None:
            print "ERROR: You have not specified the ident-parameter.\nI do not know what to delete!"
            return
        if ident in self.errorBarDictPc:
            self.removeItem(self.errorBarDictPc[ident])
        if ident in self.errorBarDictFc:
            self.removeItem(self.errorBarDictFc[ident])


    ## clears the Argand diagram by removing all its content
    # it does not remove the diagram itself (polar and radial lines will stay)
    def clearArgand(self):
        self.removeAll_originVector()
        self.removeAll_dataSet()
        self.removeAll_SplitVector()
        # ErrorBars are removed together with originVector and dataSet


    ## Remove all Origin vector
    # Usually used to refresh the display
    def removeAll_originVector(self):
        for key,item in self.originVectorDict.iteritems():
            self.remove_ErrorBars(ident=key)
            self.removeItem(item)
        self.originVectorDict.clear()


    ## Remove all data points
    # Usually used to refresh the display
    def removeAll_dataSet(self):
        for key,item in self.dataSetDict.iteritems():
            self.remove_ErrorBars(ident=key)
            self.removeItem(item)
        self.dataSetDict.clear()


    ## Remove the split vector
    def removeAll_SplitVector(self):
        for d in self.splitVectorList:
            self.removeItem(d)
        self.splitVectorList = []


    ## Remove the error bars
    # should only be called if ONLY the errorbars should be removed
    # if a dataSet or originVector is removed it will remove its errorBars automatically
    def removeAll_ErrorBar(self):
        for i in self.errorBarDictPc.itervalues():
            self.removeItem(i)
        for i in self.errorBarDictFc.itervalues():
            self.removeItem(i)
        self.errorBarDictPc.clear()
        self.errorBarDictFc.clear()


#    def toggleCrosshair(self, draw=False):
#        if draw:
#            self.vLine = pg.InfiniteLine(angle=90, movable=False)
#            self.hLine = pg.InfiniteLine(angle=0, movable=False)
#            self.plotItem.addItem(self.vLine, ignoreBounds=True)
#            self.plotItem.addItem(self.hLine, ignoreBounds=True)
#        else:
#            self.plotItem.removeItem(self.vLine)
#            self.plotItem.removeItem(self.hLine)


    # moves the Crosshair to a new position
    # (you may want to connect this with a mouseMoved method
    # in your main GUI class)
#    def moveCrosshair(self,x=0,y=0):
#        self.vLine.setPos(x)
#        self.hLine.setPos(y)


    ## Move the node of index (idn) of the given vector (vec) to the fc,pc position
    def moveNode_i(self, vec, ind, pc, fc):
        vec.moveNode(ind, self.convertPcFc_to_cartesian(pc,fc))


# implement extended GraphItem class for additional features
# like * text labels on items
#      * mouseDragevent method for interactive use
class GraphItemExtended(pg.GraphItem):
    node_mouse_moved = pyqtSignal(list)
    SigDragFinished  = pyqtSignal(list)
    def __init__(self):
        self.dragPoint = None
        self.dragOffset = None
        self.textItems = []
        self.arrowHeadItems = []

        pg.GraphItem.__init__(self)


        #self.scatter.sigClicked.connect(self.clicked)


    # changes the parameters of the nodes
    # Example: node.setData(pos=np.array([[0,0],[-0.5,0.5]]),adj=np.array([[0,1]]),size=[10,10],symbol=['o','+'],text=['label1','label2'], dragable=[False, True], arrowHead=[False,True])
    def setData(self, **kwds):
        self.text = kwds.pop('text', [])
        self.data = kwds
        if 'pos' in self.data:
            npts = self.data['pos'].shape[0]
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)
            if 'dragable' in self.data:
                self.dragable = kwds.pop('dragable', [])
            else:
                self.dragable = [True] * npts
            if 'arrowHead' in self.data:
                for i, arrowHeadBool in enumerate(self.data['arrowHead']):
                    if arrowHeadBool:
                        self.addArrowhead(*self.data['pos'][i], angle=90)
                    else:
                        self.arrowHeadItems.append(False)

        self.setTexts(self.text, update=False)
        self.updateGraph()


    def setSymbolSize(self, size):
        self.data['size']=size
        self.updateGraph()


    def setSymbolPen(self, symbolPen):
        self.data['symbolPen']=symbolPen
        self.updateGraph()


    # adds an arrow head at a node
    def addArrowhead(self, posX, posY, angle, size=10, color='r'):
        arrowHead = pg.ArrowItem(pos=(posX, posY), angle=0, tipAngle=30, baseAngle=20, headLen=15, tailLen=0, tailWidth=0, pen=None, brush='r')
        # angle has to be zero here because it is defined in the updateGraph method.
        # otherwise the angle set in updateGraph would be added to the one in the definition of pg.ArrowItem
        self.arrowHeadItems.append(arrowHead) #np.arctan2(posX,posY)*180/np.pi+90
        arrowHead.setParentItem(self) #connects with the GraphItemExtended object so that it is
                                      #added to the scene if GraphItemExtended item is added


    # returns the array with the positions of all nodes
    def getPosArray(self):
        if 'pos' in self.data:
            return self.data['pos']
        else:
            print "ERROR: Cannot get Positions. Reason: No nodes set yet."


    # set the labels of the nodes (can be added directly with setDat(.a.., text='label'))
    def setTexts(self, text, update=True):
        for i in self.textItems:
            view = i.scene()
            if not view == None:
                view.removeItem(i)
        self.textItems = []
        for t in text:
            item = pg.TextItem(html=t, color=0.0)
            self.textItems.append(item)
            item.setParentItem(self)
        if update: # to prevent multiple updates
            self.updateGraph()


    # defines if a node is dragable by mouse
    def setDragable(self, dragable):
        self.dragable = list(dragable)


    # updates the graph
    def updateGraph(self):
        pg.GraphItem.setData(self, **self.data)
        for i,item in enumerate(self.textItems):
            item.setPos(*self.data['pos'][i])
        # adds an ArrowHead to the node if arrowHead option of this node is true
        if 'arrowHead' in self.data:
            for i, arrowHead in enumerate(self.arrowHeadItems):
                if arrowHead:
                    arrowHead.setPos(*self.data['pos'][i])
                    #arrowHead.setStyle(angle=np.arctan2(*self.data['pos'][i])*180/np.pi+90)
                    # There seems to be a bug in the ArrowItem class in pyqtgraph
                    # a workaround for this bug is to adress the QtGui.QGraphicsPathItem
                    # directly via the setRotation method.
                    # NOTE: This rotation is added to the rotation in the definition of the
                    # ArrowItem. So you have to initilize it like ArrowItem(angle=0,...)
                    arrowHead.setRotation(np.arctan2(*self.data['pos'][i])*180/np.pi+90)


    ## Change the position of a single node
    def moveNode(self, node_index, pos):
        # Only move the line, not the point.
        self.data['pos'][node_index] = pos
        self.updateGraph()


    # defines mouseDragEvent
    def mouseDragEvent(self, ev):
        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return

        diff = (ev.lastScreenPos()-ev.screenPos()).manhattanLength()
        if ev.isStart():
            # We are already one step into the drag.
            # Find the point(s) at the mouse cursor when the button was first
            # pressed:
            pos = ev.buttonDownPos()
            pts = self.scatter.pointsAt(pos)
            if len(pts) == 0:
                ev.ignore()
                return
            self.dragPoint = pts[0]
            ind = pts[0].data()[0]
            self.dragOffset = self.data['pos'][ind] - pos
        elif ev.isFinish():
            self.SigDragFinished.emit(list(ev.pos() + self.dragOffset))
            self.dragPoint = None
            return
        else:
            if self.dragPoint is None:
                ev.ignore()
                return
        ind = self.dragPoint.data()[0]

        # move Item to new curser position if declared as dragable
        if self.dragable[ind]:
            self.data['pos'][ind] = ev.pos() + self.dragOffset
            self.node_mouse_moved.emit(list(self.data['pos'][ind]))
            self.updateGraph()
        ev.accept()


    # for tests. Prints something if a GraphItem is clicked
#    def clicked(self, pts):
#        pass #print("clicked: %s" % pts)
