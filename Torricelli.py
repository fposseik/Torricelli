#!/usr/bin/env python2
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
# svn propset svn:keywords 'Id Revision LastChangedDate LastChangedBy' Torricelli.py
# The following lines are edited automatically when a svn commit is done due to
# the property settings!
# DO NOT CHANGE THE FOLLOWING LINES, unless you know what you are doing
__revision__  = filter(str.isdigit, "$Revision: 483 $")
__modDate__   = "$LastChangedDate: 2018-04-25 16:38:24 +0200 (Mi, 25. Apr 2018) $"
__modDate__   = __modDate__[49:61] + ' ' + __modDate__[28:38] + 'GMT' + __modDate__[38:43]
__changedBy__ = "$LastChangedBy: m.franke $".split(' ')[1]
__svnID__     = "$Id: Torricelli.py 483 2018-04-25 14:38:24Z m.franke $"

# insert version number here, if this is a full release
__version__ = '3.9.' + __revision__

# scientific packages
import scipy as sp
import numpy as np
import cmath
import scipy.optimize
from scipy import interpolate
from scipy import constants
from scipy.interpolate import splrep, sproot
from scipy.stats import norm as scipy_norm
import lmfit

# GUI and plotting
import pyqtgraph as pg
import pyqtgraph.exporters # is not imported automatically with pyqtgraph in newer versions
from pyqtgraph.Qt import QtGui, QtCore
from PyQt4 import QtCore, QtGui

# file writing/reading
import ConfigParser
import csv

# operating system related packages
import sys, string
import os, shutil
import datetime
import glob # for fancy pathname handeling

# miscellaneous
from distutils.version import StrictVersion
import sip # includes C++ libaries
from operator import itemgetter
import ast
from ast import literal_eval
#from __future__ import print_function # adds some python 3 features

pg.setConfigOption('background', None)
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)

Torricelli_program_folder_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(Torricelli_program_folder_path+os.sep+'imports')
from GUI_MainWindow import Ui_MainWindow
from GUI_SymbolList import Ui_Dialog_SymbolList
from GUI_InsertManualValues import Ui_Dialog_InsertManualValues
from GUI_Regroup import Ui_Dialog_Regroup
from GUI_Rename import Ui_Dialog_Rename
from GUI_RemoveAll import Ui_Dialog_RemoveAll
from pyArgand import ArgandPlotWidget

# argument of the scipy.interpolate.interp1d interpolation function
interp1d_kind = 'linear'
#interp1d_kind = 'cubic' # probaly nicer, but very slow

## QDialog requesting the user to choose a group name suffix for regrouping
# used of for the Argand tab
class QDialog_rename(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dialog_Rename()
        self.ui.setupUi(self)

## QDialog requesting the user to choose a symbol
# used of for the Argand tab
class QDialog_symbol(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dialog_SymbolList()
        self.ui.setupUi(self)

## QDialog requesting the user to type-in values to be inserted as a new item in the Argand treeWidget
class QDialog_manualVal(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dialog_InsertManualValues()
        self.ui.setupUi(self)

## QDialog requesting the user to choose a group name suffix for regrouping
# used of for the Argand tab
class QDialog_regroup(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dialog_Regroup()
        self.ui.setupUi(self)

## QDialog requesting the user to choose a group name suffix for regrouping
# used of for the Argand tab
class QDialog_removeAll(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dialog_RemoveAll()
        self.ui.setupUi(self)

## Core of the program which defines the behavior of the GUI and well as the import/export and fitting methods
class Torricelli(QtGui.QMainWindow):
    ## Torricelli class constructor
    def __init__(self, parent=None):
        super(Torricelli, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.__version__   = __version__
        self.__revision__  = __revision__
        self.__modDate__   = __modDate__
        self.__changedBy__ = __changedBy__
        self.__svnID__     = __svnID__

        self.ui.setupUi(self)
        self.loadAll_csv_Files() # Basically reads in the whole crystal structure database once and for all
        self.PrepareGUI_InitVariables()
        # Installing an eventfilter for the TreeWidget to sniff which button is pressed
        # An event filter allows you to implement actions that are executed when a certain
        # event is happening without the need to reimplement the whole class.
        # This is very handy if you do not have the chance to reimplement the class
        # for example for  already existing objects that are defined external
        # For QTreeWidget: One has to access the viewport (the white area) to catch the mouse events
        self.ui.treeWidget_Argand_List.viewport().installEventFilter(self)
        # eventFilter for Torricelli itself. for example for manipulating the keyPress event
        self.installEventFilter(self)



    ################################################
    ######## Functions of general insterest ########
    ################################################

    # implement the event filter
    def eventFilter(self, source, event):
        # see http://doc.qt.io/qt-4.8/qevent.html
        # for a list of events in QEvent
        # eventfilter for enable editing
        if event.type() == QtCore.QEvent.MouseButtonRelease and source is self.ui.treeWidget_Argand_List.viewport():
            self.TreeWidgetMouseButtonReleasedEvent = event.button()

        elif event.type() == QtCore.QEvent.MouseButtonDblClick and source is self.ui.treeWidget_Argand_List.viewport():
            self.TreeWidgetMouseButtonReleasedEvent = event.type()

        # eventfilter for updating groups when an item is added/removed from a group via drag/drop
        if event.type() == QtCore.QEvent.DragEnter \
           and len(self.ui.treeWidget_Argand_List.selectedItems()) > 0 \
           and source is self.ui.treeWidget_Argand_List.viewport():
            # items can be moved from several different groups
            # saved in class variable because the groups should not be updated yet while dragging
            # but after the drop event (while dragging the item is still part of its old parent!)
            self.groupsChangedViaDrag.clear()
            for item in self.ui.treeWidget_Argand_List.selectedItems():
                self.groupsChangedViaDrag.add(item.parent())
        elif event.type() == QtCore.QEvent.Drop and source is self.ui.treeWidget_Argand_List.viewport():
            # first proceed with the original event handling, then adapt filter
            self.ui.treeWidget_Argand_List.dropEvent(event)
            itemThatReceivedIt = self.ui.treeWidget_Argand_List.itemAt(event.pos())
            if self.Argand_isGroup(itemThatReceivedIt):
                parentThatReceivedIt = itemThatReceivedIt
            else:
                parentThatReceivedIt = itemThatReceivedIt.parent()
            self.groupsChangedViaDrag.add(parentThatReceivedIt) # group that received the item changed too
            self.Argand_groupAverage(gp_items=list(self.groupsChangedViaDrag),refresh=False)
            # returning True interupts the handling of the event
            # event handling stopps here. This is neccessary if you want your filter to
            # be applied after the original event handling. In that case one should add something like
            # SourceOfEventObject.theEvent(event) before the filter code
            return True

        # returning False lets the event continue
        # all eventfilter events are handled before proceeding with the event
        return False

    ## returns a timestamp for file naming
    def timestamp(self):
        return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    ## returns True, if arg is a number, False otherwise
    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    ## Return the FWHM of any array, assuming it has a single peak
    def fwhm(self, x, y, k=10):
        """
        Determine full-with-half-maximum of a peaked set of points, x and y.

        Assumes that there is only one peak present in the datasset.  The function.
        uses a spline interpolation of order k.
        """
        class MultiplePeaks(Exception): pass
        class NoPeaksFound(Exception): pass
        half_max = (np.amax(y) - np.amin(y))/2.0
        s = splrep(x, y - half_max - np.amin(y))
        roots = sproot(s)

        if len(roots) > 2:
            raise MultiplePeaks("The dataset appears to have multiple peaks, and "
                    "thus the FWHM can't be determined.")
        elif len(roots) < 2:
            raise NoPeaksFound("No proper peaks were found in the data set; likely "
                    "the dataset is flat (e.g. all zeros).")
        else:
            return abs(roots[1] - roots[0])


    ### Define the gaussian function normalized to its area, and centered to the given array
    # The centering is very important to make sure the cross-correlation function will not end up shifted
    # Input: -- Sigma of the gaussian
    # -- An abscissa array
    def normalized_gauss_centered(self, sigma, array):
        g = scipy_norm.pdf(array, 0, sigma)
        return g/sum(g)

    ## Looks for the Reflectivity data file and the CasaXPS output file
    ## Expected folder hierarchy: "anything/fileNumber_comment/region_n"
    ## Refl file in "anything/fileNumber_comment" or "anything/fileNumber_comment/region_n"
    ## EY file in "anything/fileNumber_comment/region_n"
    def Find_refl_and_ey_file_forAGivenFolder(self):
        # look for reflectivity files in the "anything/fileNumber_comment" folder and pre-set them
        list_of_refl_files = []
        for files in glob.glob(str(self.ui.LineEdit_CurrentWorkingDirectory.text()) + os.sep+'..'+os.sep+'*.refl'):
            list_of_refl_files.append(files)
        if 1 == len(list_of_refl_files):
            self.ui.refl_name.setText(list_of_refl_files[0])
        elif 0 == len(list_of_refl_files): # Nothing found, then check folder "anything/fileNumber_comment/region_n"
            list_of_refl_files = []
            for files in glob.glob(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+'*.refl'):
                list_of_refl_files.append(files)
            if 1 == len(list_of_refl_files):
                self.ui.refl_name.setText(list_of_refl_files[0])
        else: # Really nothing then... or more than one
            self.ui.refl_name.setText('')

        # look for electron yield files in the folder "anything/fileNumber_comment/region_n" and pre-set them
        list_of_ey_files = []
        for files in glob.glob(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+'*.txt'):
            list_of_ey_files.append(files)

        if 1 == len(list_of_ey_files):
            self.ui.ey_name.setText(list_of_ey_files[0])
        else:
            self.ui.ey_name.setText('')

        # look for angle files in the folder "anything/fileNumber_comment/region_n" and pre-set them
        list_of_ang_files = []
        for files in glob.glob(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+'*.ang'):
            list_of_ang_files.append(files)

        if 1 == len(list_of_ang_files):
            self.ui.lineEdit_angles_path.setText(list_of_ang_files[0])
        else:
            self.ui.lineEdit_angles_path.setText('')


    # Sets the working directory
    # Folder == False comes by clicking the browse button in the GUI
    def choose_dataFolder(self, folder=''):
        if '' == folder or False == folder:
            dname = QtGui.QFileDialog.getExistingDirectory(self, 'Select current working directory')
        else:
            dname = folder

        if '' != dname:
            self.ui.LineEdit_CurrentWorkingDirectory.setText(dname)
            dirc=QtCore.QDir(dname)
            dirc.setCurrent(dname)
            self.ui.tab_Main.setCurrentIndex(1) # Activates the Import File tab

            if not os.path.exists(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+'results') and os.path.exists(dname):
                os.makedirs(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+'results')

            self.Find_refl_and_ey_file_forAGivenFolder()

        folder_list = os.path.normpath(str(self.ui.LineEdit_CurrentWorkingDirectory.text())).split(os.sep)
        self.data_file_name = folder_list[len(folder_list)-2] + os.sep + folder_list[len(folder_list)-1]

    ## Write any list of arrays to the specified file, and save a picture of the given plot
    # file_name: name without extension or folder
    # name_list: list of names of each saved array in array_list
    # data_list: array containing data of same lenth
    # the_plot:  pyqtgraph.PlotWidget name
    def Save_Data_and_PlotPicture(self, file_name, name_list, data_list, the_plot=None):
        nb_arrays_to_write = len(data_list)
        array_length = len(data_list[0])
        file_name = str(self.ui.LineEdit_CurrentWorkingDirectory.text()) + os.sep + 'results'+ os.sep + file_name
        #simple checks
        if len(name_list) != nb_arrays_to_write:
            print 'You forgot some array names or some arrays'
            return

        for index in range(nb_arrays_to_write):
            if len(data_list[index]) != len(data_list[0]):
                self.ui.statusbar.showMessage("Save_Data_and_PlotPicture() says \'Non-homogeneous lengths of arrays!\'")
                return
        try:
            with open(file_name+'.dat', 'w') as the_file:
                line = ''
                for name_i in range(nb_arrays_to_write):
                    line += str(name_list[name_i]) + '\t'
                the_file.write(line+'\n')

                for i in range(array_length):
                    line = ''
                    for array_i in range(nb_arrays_to_write):
                        line += str(data_list[array_i][i]) + '\t'
                    the_file.write(line+'\n')
        except IOError:
            QtGui.QMessageBox.warning(self, "Warning", 'Problem writing the data to file. \"results\" folder may be missing')

        if the_plot is not None:
            try:
                if StrictVersion(pg.__version__) < StrictVersion('0.9.9'):
                    exporter = pyqtgraph.exporters.ImageExporter.ImageExporter(the_plot.plotItem)
                else:
                    exporter = pyqtgraph.exporters.ImageExporter(the_plot.plotItem)
            except (ValueError, AttributeError, TypeError) as err:
                if type(err).__name__ == "ValueError":
                    print "\nCould not read the version of pyqtgraph!"
                    print("\n\nWARNING: There was an error exporting the fits as png images!\n"
                      "Image export will not work, but you can go on using torricelli.\n"
                      "This error can occur due an incompatible pyqtgraph version.")
                elif type(err).__name__ == "AttributeError":
                    print str(err)+'\n'
                    print("\nTry using a newer version of pyqtgraph or pyqtgraph 0.9.10\n"
                          "you are using version: " + pg.__version__ + "\n")
                elif type(err).__name__ == "TypeError":# and str(err) == "'float' object cannot be interpreted as an index":
                    errMsg = """<font face=courier><b>line 70, in export<br>"""+\
                    """bg = np.empty((self.params['width'], self.params['height'], 4), dtype=np.ubyte)<br>"""+\
                    """TypeError: 'float' object cannot be interpreted as an index</b></font>"""

                    QtGui.QMessageBox.warning(self, "Warning", "<b>There is a bug in the particular version of pyqtgraph you are using!</b> "+\
                    "If you get an error message after this warning similar to: <br><br>"+errMsg+"<br><br>Then there are two possiblities what you can do.<br>"+\
                    "Easiest way is to use just another version of pyqtgraph. v0.9.10 for example. However sometimes the error seems to occur there, too."+\
                    "Other possibility: You can implement a workaround and edit the file ImageExporter.py from the pyqtgraph module. To do so change the following in the file:<br><br>"+\
                    """Change the following line:<br><br>"""+\
                    """<font face=courier><b>bg = np.empty((self.params['width'], self.params['height'], 4), dtype=np.ubyte)</b></font><br>"""+\
                    """<br>to:<br><br>"""+\
                    """<font face=courier><b>bg = np.empty((int(self.params['width']), int(self.params['height']),4), dtype=np.ubyte)</b></font>"""+\
                    """<br><br><b>NOTE:</b> This is not a bug in Torricelli. You have to edit the ImageExporter.py file of the pyqtgraph package itsef!"""+\
                    """After upgrading or reinstalling pyqtgraph this modification can be overwritten and you can get the error again.""")
                    print "TypeError: "+str(err)

            else:
                exporter.parameters()['background'] = (0,0,0,0)
                exporter.export(file_name+'.png')


    ################################################
    ########     Section Import Files       ########
    ################################################
    ## Look for the reflectivity file
    def open_refl(self):
        text = QtGui.QFileDialog.getOpenFileName(self, "Open File", self.ui.LineEdit_CurrentWorkingDirectory.text(), "Reflectivity Files (*.refl);; All (*)")
        if '' != text:
            self.ui.refl_name.setText(text)
            self.display_refl()
            self.ui.statusbar.showMessage('Raw reflectivity and beam intensity data are imported!', 3000)

    ## Look for the electron yield file
    def open_ey(self):
        text = QtGui.QFileDialog.getOpenFileName(self, "Open File", self.ui.LineEdit_CurrentWorkingDirectory.text(), "Electron Yield Files (*.txt *.yield *.ey);; All (*)")
        if '' != text:
            self.ui.ey_name.setText(text)
            self.display_ey()
            self.ui.statusbar.showMessage('EY file has been imported!', 3000)

    def open_angles(self):
        text = QtGui.QFileDialog.getOpenFileName(self, "Open File", self.ui.LineEdit_CurrentWorkingDirectory.text(), "Angle Files (*.ang *.angle *.angles);; All (*)")
        if '' != text:
            self.ui.lineEdit_angles_path.setText(text)
            self.display_angles()
            self.load_angles()
            self.ui.statusbar.showMessage('Slice to angle conversion data is imported!', 3000)

    ## Displays the reflectivity file
    def display_refl(self):
        try:
            with open(self.ui.refl_name.text(), 'r') as refl_file:
                self.ui.display_window.setText(refl_file.read())
                self.ui.display_window.setLineWrapMode(QtGui.QTextEdit.NoWrap)
                self.ui.statusbar.showMessage('Raw reflectivity and beam intensity data are displayed!', 3000)
        except IOError:
            self.ui.statusbar.showMessage('*** Problem with the reflectivity file. ***')

    ## Displays the electron yield file
    def display_ey(self):
        try:
            with open(self.ui.ey_name.text(), 'r') as ey_file:
                self.ui.display_window.setText(ey_file.read())
                self.ui.display_window.setLineWrapMode(QtGui.QTextEdit.NoWrap)
                self.ui.statusbar.showMessage('EY file is displayed!', 3000)
        except IOError:
            self.ui.statusbar.showMessage('*** Problem with the EY file. ***')

    ## Displays the angles file
    def display_angles(self):
        try:
            with open(self.ui.lineEdit_angles_path.text(), 'r') as angles_file:
                self.ui.display_window.setText(angles_file.read())
                self.ui.display_window.setLineWrapMode(QtGui.QTextEdit.NoWrap)
                self.ui.statusbar.showMessage('Slice to angles file is displayed!', 3000)
        except IOError:
            self.ui.statusbar.showMessage('*** Problem with the slice to angles file. ***')

    def load_angles(self):
        try:
            with open(self.ui.lineEdit_angles_path.text(), 'r') as file_angles:
                info0 = file_angles.readline()
                info1 = file_angles.readline()
                info2 = file_angles.readline()
            with open(self.ui.lineEdit_angles_path.text(), 'r') as file_angles:
                self.slice_to_angle = dict(np.loadtxt(file_angles, dtype={'names': ('slice', 'angle'), 'formats':("int","float")}, skiprows=5))

            self.ui.label_angles_file_info.setText(info1+info2[:-2])
        except IOError:
            self.ui.statusbar.showMessage('*** Problem with the slice to angles file. ***')


    # Treats and plot the data as given by the user, and fill Torricelli arrays for later use
    # !! -> The Refl and EY are here normalized to I0
    # !! -> The reflectivity estimited error is sqrt(refl_normalised)
    def Transform_R_and_EY_userFile_to_TorricelliFriendly(self, slice_num=0, calledFromAngularCheckBox=False):
        if '' == self.ui.ey_name.text():
            QtGui.QMessageBox.warning(self, "Warning", "You forgot to give the experimental Electron yield file produced by CasaXPS!")
            return
        if '' == self.ui.refl_name.text():
            QtGui.QMessageBox.warning(self, "Warning", "You forgot to give the experimental Reflectivity file!")
            return

        self.ui.checkBox_AngularModeToggle.setEnabled(True)

        # Read in the reflectivity data from the experiments (consists of 3 columns: energy, reflectivity, beam_intensity)
        data_r = np.loadtxt(str(self.ui.refl_name.text()), dtype = "float", skiprows=1)

        # The following lines extract the names of the columns in the yield data file
        with open(str(self.ui.ey_name.text())) as data_ey_raw:
            data_ey_raw.readline(), data_ey_raw.readline()
            ey_column_name_line = data_ey_raw.readline()

        ey_column_names = ey_column_name_line.split("\t")
        # The user chooses the component(s) and the corresponding column name(s) is(are) displayed below
        columns = str(self.ui.signal_name.text())
        if ''==columns: columns='0'
        ey_column_indices = map(lambda x: x*2+1, np.fromstring(columns, dtype=int, sep=' '))
        # check if the indices match the number of components stored in the yield file
        if max(ey_column_indices) >= len(ey_column_names):
            QtGui.QMessageBox.warning(self, "Warning", "At least the index of one component you have given exceeds the number of components stored in your yield file.<br>Check the field <i>Components to sum</i>.")
            return
        self.ui.column_name_label.setText(", ".join(map(lambda x: ey_column_names[x], ey_column_indices)))

        data_ey = np.loadtxt (str(self.ui.ey_name.text()), dtype = "float", skiprows=3)

        # If the user do have several blocks into the CasaXPs output file, then it does not perform usual checks
        if self.ui.checkBox_AngularModeToggle.isChecked():
            np_photon_points = data_r.shape[0] # number of entries for each slice
            self.nb_slices = data_ey.shape[0]/np_photon_points # calculate number of slices

            self.load_angles()

            # adjustment of the slice spinbox
            if calledFromAngularCheckBox:
                self.ui.spinBox_SelectedSlice.setEnabled(True)
                self.ui.spinBox_SelectedSlice.setMinimum(0)
                self.ui.spinBox_SelectedSlice.setMaximum(self.nb_slices-1)
                self.ui.spinBox_SelectedSlice.setValue(self.nb_slices-1)

            if data_ey.shape[0] % np_photon_points != 0:
                print "\nERROR: Could not calculate the number of slices!\n"
                return

            # extract data corrensponding to chosen slice
            data_ey = data_ey[self.ui.spinBox_SelectedSlice.value()*np_photon_points:\
                              (self.ui.spinBox_SelectedSlice.value()+1)*np_photon_points]

        if data_r.shape[0] != data_ey.shape[0]:
            QtGui.QMessageBox.warning(self, "Warning", 'The reflectivity and electron yield files do not have the same length!\nMaybe you intended to use angular mode?')
            return

        i0 = data_r[:,2] # beam intensity
        i0average = sum(data_r[:,2])/len(data_r[:,2]) # average beam intensity

        xsw_energies = np.array([])
        xsw_reflectivity_normalised      = np.array([])
        xsw_reflectivity_estimated_error = np.array([])
        xsw_ey_normalised    = np.array([])
        xsw_ey_error_casaXPS = np.array([])
        for i in range (len (data_r[:,0])): # for each photon energy, normalized with I0
            xsw_energies = np.append(xsw_energies, data_r[i,0])
            xsw_reflectivity_normalised = np.append(xsw_reflectivity_normalised, data_r[i,1]/i0[i]*i0average)
            xsw_reflectivity_estimated_error = np.append(xsw_reflectivity_estimated_error, np.sqrt(data_r[i,1]/i0[i]*i0average))

            if abs(data_r[i,0] - data_ey[i, 0]) > 1e-1 and not self.ui.checkBox_AngularModeToggle.isChecked() and not self.ui.checkBox_ignore_hvCheck.isChecked():
                QtGui.QMessageBox.warning(self, "Warning", 'The photon energies of the reflectivity and electron yield files do not match!')
                return

            tmp_ey_norm = 0.0
            tmp_ey_err_squared  = 0.0
            for comp_index in range(len(self.Components_List_Used_in_EYfit)): # for each fit component desired by the user
                component_number = self.Components_List_Used_in_EYfit[comp_index]
                component_col_number = 1 + 2*component_number # component_col_number+1 is corresponding the error
                if component_col_number+1 >= data_ey.shape[1]:
                    QtGui.QMessageBox.warning(self, "Warning", 'The component number you asked for does not exist!')
                tmp_ey_norm += data_ey[i, component_col_number]
                tmp_ey_err_squared  += data_ey[i, component_col_number+1]**2 # sum up the squares of the errors

            xsw_ey_normalised =  np.append(xsw_ey_normalised, tmp_ey_norm/i0[i]*i0average)
            xsw_ey_error_casaXPS = np.append(xsw_ey_error_casaXPS, np.sqrt(tmp_ey_err_squared)/i0[i]*i0average)

        self.Exp_photonEnergy = xsw_energies
        self.Exp_Refl_Normalised = xsw_reflectivity_normalised
        self.Exp_Refl_Estimated_Error = xsw_reflectivity_estimated_error
        self.Exp_EY_Normalised = xsw_ey_normalised
        self.Exp_EY_casaXPS_Error = xsw_ey_error_casaXPS

        ## Move the experimental photon energy axis relative to the theoretical Bragg energy
        self.Exp_photonEnergy_BraggCentered = self.Exp_photonEnergy - self.ui.doubleSpinBox_ndp_EBragg.value()

        # Now save when fitting the reflectivity, because of normalisation.
        ## self.Save_Data_and_PlotPicture('Exp_refl_norm_centred', [self.Exp_photonEnergy_BraggCentered, self.Exp_Refl_Normalised, self.Exp_Refl_Estimated_Error])
        ## self.Save_Data_and_PlotPicture('Exp_ey_norm_centred'+str(self.Components_List_Used_in_EYfit), [self.Exp_photonEnergy_BraggCentered, self.Exp_EY_Normalised, self.Exp_EY_casaXPS_Error])
        self.Pyqt_View_raw_refl.clear()
        self.Pyqt_View_raw_ey.clear()
        self.Pyqt_View_raw_refl.plot(self.Exp_photonEnergy, self.Exp_Refl_Normalised, pen=(0,0,220), symbol='o')
        self.Pyqt_View_raw_ey.plot(  self.Exp_photonEnergy, self.Exp_EY_Normalised,   pen=(0,0,220), symbol='o')
        ey_err = pg.ErrorBarItem(  x=self.Exp_photonEnergy, y=self.Exp_EY_Normalised, top=self.Exp_EY_casaXPS_Error, bottom=self.Exp_EY_casaXPS_Error, beam=0.05, pen=(200,200,200))
        self.Pyqt_View_raw_ey.addItem(ey_err)

        self.reset_ey_par() # Set initials parameters for the electron yield fit
        self.set_refl_par() # same for reflectivity
        # self.Pyqt_View_refl_fit.plot(self.Exp_photonEnergy_BraggCentered + self.ui.doubleSpinBox_ReflFit_InitVal_DeltaE.value(), (self.Exp_Refl_Normalised - self.ui.doubleSpinBox_ReflFit_InitVal_Bgd.value()) / self.ui.doubleSpinBox_ReflFit_InitVal_Norm.value(), pen=None, symbol='o', symbolBrush=(0,150,255))
        # plot_center = self.Theory_photonEnergy[np.argmax(self.Theory_ReflSample_cc_ReflMono2)]
        # plot_width  = (self.Exp_photonEnergy_BraggCentered[-1]-self.Exp_photonEnergy_BraggCentered[0])*1.2
        # self.Pyqt_View_refl_fit.setXRange(plot_center-plot_width/2., plot_center+plot_width/2.)
        # self.Pyqt_View_refl_fit.setYRange(0, 1)

        # update the angle corresponding to slice if given and do a consistency check
        if not self.ui.lineEdit_angles_path.text()=='' and self.ui.checkBox_AngularModeToggle.isChecked():
            if len(self.slice_to_angle) != self.nb_slices:
                QtGui.QMessageBox.warning(self, "INCONSISTENCY DETECTED", "<b>The number of angles and slices do not match the number of slices determined by your loaded yield file!</b><br><br>Please check your angles file or your yield file and make sure that they match!")
            self.ui.label_AngleOfSlice.setText(str(self.slice_to_angle[self.ui.spinBox_SelectedSlice.value()])+'&deg;<b></b>') #<b></b> is to auto enable rich text
            self.ui.doubleSpinBox_ndp_phi.setValue(self.slice_to_angle[self.ui.spinBox_SelectedSlice.value()])


    #######################################################################
    #######      Section Structure factor and Ideal Reflectivity     ######
    #######################################################################
    ## Simple protection against abusive modification of the DCM parameters.
    def allow_DCM_parameter_modification(self):
        answer = QtGui.QMessageBox.warning(self, 'Editing DCM parameters', 'Are you sure you want to continue?', QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        if answer == QtGui.QMessageBox.Yes:
            self.ui.comboBox_DCM_Element.setEnabled(True)
            self.ui.spinBox_DCM_h.setEnabled(True)
            self.ui.spinBox_DCM_k.setEnabled(True)
            self.ui.spinBox_DCM_l.setEnabled(True)
            self.ui.label_DCM_i.setEnabled(True)
            self.ui.doubleSpinBox_DCM_Temperature.setEnabled(True)
            self.ui.doubleSpinBox_b_mo.setEnabled(True)
        elif answer == QtGui.QMessageBox.No:
            self.ui.comboBox_DCM_Element.setEnabled(False)
            self.ui.spinBox_DCM_h.setEnabled(False)
            self.ui.spinBox_DCM_k.setEnabled(False)
            self.ui.spinBox_DCM_l.setEnabled(False)
            self.ui.label_DCM_i.setEnabled(False)
            self.ui.doubleSpinBox_DCM_Temperature.setEnabled(False)
            self.ui.doubleSpinBox_b_mo.setEnabled(False)

    # Updates the asymmetry parameter b
    def refresh_sample_b_and_theta_value(self):
        self.ui.doubleSpinBox_b_cr.setValue(-1*np.sin(   (90.0-self.ui.doubleSpinBox_sample_miscut.value()-self.ui.doubleSpinBox_sample_deviation_NI.value())*np.pi/180. )\
                                                /np.sin( (90.0+self.ui.doubleSpinBox_sample_miscut.value()-self.ui.doubleSpinBox_sample_deviation_NI.value())*np.pi/180. ))
        self.ui.doubleSpinBox_theta.setValue(90.-self.ui.doubleSpinBox_sample_deviation_NI.value())

    # Updates the polarization factor P for x-ray and electrons
    def refresh_sample_P_value(self):
        if self.ui.radioButton_sigma_pol_light.isChecked():
            self.ui.doubleSpinBox_sample_P_Refl.setValue(1.0)
            self.ui.label_pol.setText(u"\u03C3"+'-polarization')
            self.ui.doubleSpinBox_EYinit_Pe.setEnabled(False)
            P_electrons = 0.0 #actually not defined
        else:
            self.ui.doubleSpinBox_sample_P_Refl.setValue(-1*np.cos( (2*self.ui.doubleSpinBox_sample_deviation_NI.value())*np.pi/180. )) # same as P= cos (2 theta.)
            self.ui.label_pol.setText(u"\u03C0"+'-polarization')
            self.ui.doubleSpinBox_EYinit_Pe.setEnabled(True)
            P_electrons = np.sin( self.ui.doubleSpinBox_ndp_phi.value()*np.pi/180 - 2*self.ui.doubleSpinBox_sample_deviation_NI.value()*np.pi/180 )\
              / np.sin( self.ui.doubleSpinBox_ndp_phi.value()*np.pi/180 )
        self.ui.doubleSpinBox_EYinit_Pe.setValue(P_electrons)

    ## return the crystal system given the lattice distances and angles
    def determine_crystal_system(self, element, isCompound=False):
        if not isCompound:
            a = self.lattice_a[element]
            b = self.lattice_b[element]
            c = self.lattice_c[element]
            alpha = self.lattice_alpha[element]*180/np.pi
            beta  = self.lattice_beta[ element]*180/np.pi
            gamma = self.lattice_gamma[element]*180/np.pi
        else:
            a = self.compound_lattice_a[element]
            b = self.compound_lattice_b[element]
            c = self.compound_lattice_c[element]
            alpha = self.compound_lattice_alpha[element]*180/np.pi
            beta  = self.compound_lattice_beta[ element]*180/np.pi
            gamma = self.compound_lattice_gamma[element]*180/np.pi

        if   abs(a-b)<1e-5 and abs(b-c)<1e-5 and abs(alpha-90)<1e-5   and abs(beta-90)<1e-5    and abs(gamma-90)<1e-5:   return 'Cubic'
        elif abs(a-b)<1e-5 and abs(b-c)>1e-5 and abs(alpha-90)<1e-5   and abs(beta-90)<1e-5    and abs(gamma-120.)<1e-5: return 'Hexagonal'
        elif abs(a-b)<1e-5 and abs(b-c)>1e-5 and abs(alpha-90)<1e-5   and abs(beta-90)<1e-5    and abs(gamma-90)<1e-5:   return 'Tetragonal'
        elif abs(a-b)<1e-5 and abs(b-c)<1e-5 and abs(alpha-beta)<1e-5 and abs(beta-gamma)<1e-5 and abs(beta-90)>1e-5:    return 'Trigonal'# or 'Rhombohedral'
        elif abs(a-b)>1e-5 and abs(b-c)>1e-5 and abs(a-c)>1e-5 and abs(alpha-90)<1e-5    and abs(beta-90)<1e-5    and abs(gamma-90)<1e-5:  return 'Orthorhombic'
        elif abs(a-b)>1e-5 and abs(b-c)>1e-5 and abs(a-c)>1e-5 and abs(alpha-gamma)<1e-5 and abs(beta-90)>1e-5    and abs(gamma-90)<1e-5:  return 'Monoclinic'
        elif abs(a-b)>1e-5 and abs(b-c)>1e-5 and abs(a-c)>1e-5 and abs(alpha-gamma)>1e-5 and abs(alpha-beta)>1e-5 and abs(beta-gamma)>1e-5:return 'Triclinic'
        else: print '--> Unknown crystal system for', element


    ## return structure name that fits the DW Databases
    def convertSystemCell_to_Abbreviations(self, element):
        if self.cell_type[element]   == 'faceCentered' and self.determine_crystal_system(element) == 'Cubic':     return 'FCC'
        elif self.cell_type[element] == 'bodyCentered' and self.determine_crystal_system(element) == 'Cubic':     return 'BCC'
        elif self.cell_type[element] == 'HCP'          and self.determine_crystal_system(element) == 'Hexagonal': return 'HCP'
        elif self.cell_type[element] == 'diamond'      and self.determine_crystal_system(element) == 'Cubic':     return 'DIAMOND'
        else: return 'Unknnown'


    ## Upon changing the DCM element, the structure is displayed,
    # Also the possible DW methods are listed
    def update_structure_DCM(self):
        currentIndex = self.ui.comboBox_DCM_Element.currentIndex()
        element = str(self.ui.comboBox_DCM_Element.itemText(currentIndex))
        self.ui.label_DCM_Structure.setText(self.determine_crystal_system(element))
        self.ui.label_DCM_Type.setText(str(self.cell_type[element]))
        self.ui.label_DCM_a.setText(str(self.lattice_a[element]))
        self.ui.label_DCM_b.setText(str(self.lattice_b[element]))
        self.ui.label_DCM_c.setText(str(self.lattice_c[element]))
        self.ui.label_DCM_alpha.setText(str(self.lattice_alpha[element]*180/np.pi))
        self.ui.label_DCM_beta.setText(str(self.lattice_beta[element]*180/np.pi))
        self.ui.label_DCM_gamma.setText(str(self.lattice_gamma[element]*180/np.pi))
        if self.checked_values[element]=='yes':
            self.ui.label_DCM_CheckedValue.setText('Yes')
            self.ui.label_DCM_CheckedValue.setStyleSheet('QLabel {color:green}')
        elif self.checked_values[element]=='no':
            self.ui.label_DCM_CheckedValue.setText('No')
            self.ui.label_DCM_CheckedValue.setStyleSheet('QLabel {color:red}')

        # check which DW is available, with the adequate lattice structure:
        self.ui.comboBox_DCM_DWMethod.clear()
        if self.ui.doubleSpinBox_DCM_Temperature.value() > 80:
            if str(element) in self.gao_HT_Z:
                if self.gao_HT_lattice_type[element] == self.convertSystemCell_to_Abbreviations(element):
                    self.ui.comboBox_DCM_DWMethod.addItem('Gao')
        else:
            if str(element) in self.gao_LT_Z:
                if self.gao_LT_lattice_type[element] == self.convertSystemCell_to_Abbreviations(element):
                    self.ui.comboBox_DCM_DWMethod.addItem('Gao')

        if str(element) in self.sears_Z:
            if self.sears_lattice_type[element] == self.convertSystemCell_to_Abbreviations(element):
                self.ui.comboBox_DCM_DWMethod.addItem('Sears')
                if self.determine_crystal_system(element) == 'Cubic':
                    self.ui.comboBox_DCM_DWMethod.addItem('Warren') # All necessary data are in Sears' paper and additionally, it must be cubic.
        self.ui.comboBox_DCM_DWMethod.addItem('None')
        self.ui.label_DCM_i.setVisible(str(self.ui.label_DCM_Structure.text())[0] == 'H')

    ## Upon changing the Elemental element, the structure is displayed,
    # Also the possible DW methods are listed
    def update_structure_Sample_Elemental(self):
        currentIndex = self.ui.comboBox_Sample_Elemental_Element.currentIndex()
        element = str(self.ui.comboBox_Sample_Elemental_Element.itemText(currentIndex))
        self.ui.label_Sample_Elemental_Structure.setText(self.determine_crystal_system(element))
        self.ui.label_Sample_Elemental_Type.setText(str(self.cell_type[element]))
        self.ui.label_Elemental_a.setText(str(self.lattice_a[element]))
        self.ui.label_Elemental_b.setText(str(self.lattice_b[element]))
        self.ui.label_Elemental_c.setText(str(self.lattice_c[element]))
        self.ui.label_Elemental_alpha.setText(str(self.lattice_alpha[element]*180/np.pi))
        self.ui.label_Elemental_beta.setText(str(self.lattice_beta[element]*180/np.pi))
        self.ui.label_Elemental_gamma.setText(str(self.lattice_gamma[element]*180/np.pi))
        if self.checked_values[element]=='yes':
            self.ui.label_Elemental_CheckedValue.setText('Yes')
            self.ui.label_Elemental_CheckedValue.setStyleSheet('QLabel {color:green}')
        elif self.checked_values[element]=='no':
            self.ui.label_Elemental_CheckedValue.setText('No')
            self.ui.label_Elemental_CheckedValue.setStyleSheet('QLabel {color:red}')

        # check which DW is available, with the adequate lattice structure:
        self.ui.comboBox_Sample_Elemental_DWMethod.clear()
        if self.ui.doubleSpinBox_Sample_Elemental_Temperature.value() > 80:
            if str(element) in self.gao_HT_Z:
                if self.gao_HT_lattice_type[element] == self.convertSystemCell_to_Abbreviations(element):
                    self.ui.comboBox_Sample_Elemental_DWMethod.addItem('Gao')
        else:
            if str(element) in self.gao_LT_Z:
                if self.gao_LT_lattice_type[element] == self.convertSystemCell_to_Abbreviations(element):
                    self.ui.comboBox_Sample_Elemental_DWMethod.addItem('Gao')
        if str(element) in self.sears_Z:
            if self.sears_lattice_type[element] == self.convertSystemCell_to_Abbreviations(element):
                self.ui.comboBox_Sample_Elemental_DWMethod.addItem('Sears')
                if  self.determine_crystal_system(element) == 'Cubic':
                    self.ui.comboBox_Sample_Elemental_DWMethod.addItem('Warren') # All necessary data are in Sears' paper, but it must be cubic
        self.ui.comboBox_Sample_Elemental_DWMethod.addItem('None')
        self.ui.label_Sample_Elemental_i.setVisible(str(self.ui.label_Sample_Elemental_Structure.text())[0] == 'H')


    ## Upon changing the Compound element, the structure is displayed,
    # Also the possible DW methods are listed (to be implemented)
    def update_structure_Sample_Compound(self, currentIndex):
        element = str(self.ui.comboBox_Sample_Compound_Element.itemText(currentIndex))
        self.ui.label_Sample_Compound_Structure.setText(self.determine_crystal_system(element, True))
        self.ui.label_Sample_Compound_Type.setText(str(self.compound_cell_type[element]))
        self.ui.label_Compound_a.setText(str(self.compound_lattice_a[element]))
        self.ui.label_Compound_b.setText(str(self.compound_lattice_b[element]))
        self.ui.label_Compound_c.setText(str(self.compound_lattice_c[element]))
        self.ui.label_Compound_alpha.setText(str(self.compound_lattice_alpha[element]*180/np.pi))
        self.ui.label_Compound_beta.setText( str(self.compound_lattice_beta[element]*180/np.pi))
        self.ui.label_Compound_gamma.setText(str(self.compound_lattice_gamma[element]*180/np.pi))
        self.ui.label_Sample_Compound_i.setVisible(str(self.ui.label_Sample_Compound_Structure.text())[0] == 'H')
        if self.compound_checked_values[element]=='yes':
            self.ui.label_Compound_CheckedValue.setText('Yes')
            self.ui.label_Compound_CheckedValue.setStyleSheet('QLabel {color:green}')
        elif self.compound_checked_values[element]=='no':
            self.ui.label_Compound_CheckedValue.setText('No')
            self.ui.label_Compound_CheckedValue.setStyleSheet('QLabel {color:red}')

        self.ui.comboBox_Sample_Compound_DWMethod.clear()
        if element == '6H-SiC':
            self.ui.comboBox_Sample_Compound_DWMethod.addItem('Zywietz')
        self.ui.comboBox_Sample_Compound_DWMethod.addItem('None')

    ## returns the interpolated value of the variable 'name_y', for a given 'value_x'
    # reads the data from the csv file 'fname'
    def interpolate_value_from_csv_file(self, fname, name_x, value_x, name_y, delim=','):
        with open(fname, 'rb') as csvFile:
            spamreader = csv.DictReader(csvFile, delimiter=delim)
            X = []
            Y = []
            for row in spamreader:
                X.append(float(row[name_x]))
                Y.append(float(row[name_y]))
            f = sp.interpolate.interp1d(X, Y) # linear interpolation
            return f(value_x)

    # Clear all structure factor values and theoretical curves as soon as some parameter is changed.
    def clear_structFact_display(self):
        self.Pyqt_View_idealRefl.clear()
        self.ui.label_DW_DCM_A.setText('')
        self.ui.label_F0_DCM.setText('')
        self.ui.label_FH_DCM.setText('')
        self.ui.label_FHbar_DCM.setText('')
        self.ui.label_dhkl_DCM.setText('')
        self.ui.label_DW_sample.setText('')
        self.ui.label_DW_sample_A.setText('')
        self.ui.label_DW_sample_B.setText('')
        self.ui.label_F0_sample.setText('')
        self.ui.label_FH_sample.setText('')
        self.ui.label_FHbar_sample.setText('')
        self.ui.label_dhkl_sample.setText('')
        self.ui.label_EB_sample.setText('')


    ## General function that calculates first the structure factor of the sample, and then, knowing the wanted Bragg energy, it calculate the corresponding structure factor for the double monochomator.
    # Finally, it will all be displayed in the GUI
    def calculate_structure_factors(self):
        self.Pyqt_View_refl_fit.clear()

        if self.ui.radioButton_Sample_Elemental.isChecked(): # Elemental sample :
            SampleName = str(self.ui.comboBox_Sample_Elemental_Element.currentText())\
              +'('+str(self.ui.spinBox_Sample_Elemental_h.value())\
              +    str(self.ui.spinBox_Sample_Elemental_k.value())\
              +    str(self.ui.spinBox_Sample_Elemental_l.value())+')'
            d_hkl, E_bragg, F_0, F_H, F_Hbar, DW_A, DW_B, vol_unit_cell, lambda_bragg = self.calculate_structure_factor(str(self.ui.comboBox_Sample_Elemental_Element.currentText()),\
                 self.cell_type[str(self.ui.comboBox_Sample_Elemental_Element.currentText())],\
                 self.ui.spinBox_Sample_Elemental_h.value(),\
                 self.ui.spinBox_Sample_Elemental_k.value(),\
                 self.ui.spinBox_Sample_Elemental_l.value(),\
                 self.ui.comboBox_Sample_Elemental_DWMethod.currentText(),\
                 self.ui.doubleSpinBox_Sample_Elemental_Temperature.value(),\
                 False, 0.0,\
                 self.Z_inverted[self.elemental_Z[str(self.ui.comboBox_Sample_Elemental_Element.currentText())]])
        else: # Compound sample
            SampleName = str(self.ui.comboBox_Sample_Compound_Element.currentText())\
              +'('+str(self.ui.spinBox_Sample_Compound_h.value())\
              +    str(self.ui.spinBox_Sample_Compound_k.value())\
              +    str(self.ui.spinBox_Sample_Compound_l.value())+')'
            d_hkl, E_bragg, F_0, F_H, F_Hbar, DW_A, DW_B, vol_unit_cell, lambda_bragg = self.calculate_structure_factor(str(self.ui.comboBox_Sample_Compound_Element.currentText()),\
                 self.compound_cell_type[str(self.ui.comboBox_Sample_Compound_Element.currentText())],\
                 self.ui.spinBox_Sample_Compound_h.value(),\
                 self.ui.spinBox_Sample_Compound_k.value(),\
                 self.ui.spinBox_Sample_Compound_l.value(),\
                 self.ui.comboBox_Sample_Compound_DWMethod.currentText(),\
                 self.ui.doubleSpinBox_Sample_Compound_Temperature.value(),\
                 False, 0.0,\
                 self.compound_elementA[str(self.ui.comboBox_Sample_Compound_Element.currentText())],\
                 self.compound_elementB[str(self.ui.comboBox_Sample_Compound_Element.currentText())])
        if d_hkl is None: # forbidden hkl combination
            self.clear_structFact_display()
            return

        # DCM with adapted parameters
        DCMName = str(self.ui.comboBox_DCM_Element.currentText())\
          +'('+str(self.ui.spinBox_DCM_h.value())\
          +    str(self.ui.spinBox_DCM_k.value())\
          +    str(self.ui.spinBox_DCM_l.value())+')'

        d_hkl_DCM, E_bragg_DCM, F_0_DCM, F_H_DCM, F_Hbar_DCM, DW_A_DCM, DW_B_DCM, vol_unit_cell_DCM, lambda_bragg_DCM = self.calculate_structure_factor(str(self.ui.comboBox_DCM_Element.currentText()),\
                 self.cell_type[str(self.ui.comboBox_DCM_Element.currentText())],\
                 self.ui.spinBox_DCM_h.value(),\
                 self.ui.spinBox_DCM_k.value(),\
                 self.ui.spinBox_DCM_l.value(),\
                 self.ui.comboBox_DCM_DWMethod.currentText(),\
                 self.ui.doubleSpinBox_DCM_Temperature.value(),\
                 True, E_bragg,\
                 str(self.ui.comboBox_DCM_Element.currentText()))

        self.ui.label_DW_DCM_A.setText(str('%1.4f' % DW_A_DCM))
        self.ui.label_F0_DCM.setText('{:.4f}'.format(F_0_DCM))
        self.ui.label_FH_DCM.setText('{:.4f}'.format(F_H_DCM))
        self.ui.label_FHbar_DCM.setText('{:.4f}'.format(F_Hbar_DCM))
        self.ui.label_dhkl_DCM.setText(str('%1.3f' % d_hkl_DCM + ' Ang'))
        self.ui.label_DW_sample.setText(str('%1.4f' % DW_A))
        self.ui.label_DW_sample_A.setText(str('%1.4f' % DW_A + ' (A)'))
        self.ui.label_DW_sample_B.setText(str('%1.4f' % DW_B + ' (B)'))
        self.ui.label_F0_sample.setText('{:.4f}'.format(F_0))
        self.ui.label_FH_sample.setText('{:.4f}'.format(F_H))
        self.ui.label_FHbar_sample.setText('{:.4f}'.format(F_Hbar))
        self.ui.label_dhkl_sample.setText(str('%1.3f' %d_hkl + ' Ang'))
        self.ui.label_EB_sample.setText(str('%1.2f' %E_bragg + ' eV'))
        self.ui.doubleSpinBox_ndp_EBragg.setValue(E_bragg)

        # Light polarisation
        P = self.ui.doubleSpinBox_sample_P_Refl.value()
        P_DCM = 1.0

        b_mo = self.ui.doubleSpinBox_b_mo.value() # Usual double monochromators have two Si(111) crystals and use the (111) reflection: symmetric case, ignoring the miscut.
        self.b_cr = self.ui.doubleSpinBox_b_cr.value() # useful when the user measures off-normal reflections
        # A practical equation for B is in Eq. 13.19 of the book: The XSW Technique (2013)
        # b = sin(Theta_B - Alpha) / sin(Theta_B + Alpha) where Alpha is the angle between the surface of the crystal and the atomic planes.

        try:  # Store data in file
            with open(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+"results"+os.sep+"Structure Factor.dat", 'w') as SFfile:
                SFfile.write('--- '+SampleName+' Sample parameters ---\n')
                SFfile.write('F0\t=\t'+ str(F_0) +'\n')
                SFfile.write('FH\t=\t'+ str(F_H) +'\n')
                SFfile.write('FHbar\t=\t'+ str(F_Hbar) +'\n')
                SFfile.write('DW for element A\t=\t'+ str(DW_A) +' (for elemental and compounds) \n')
                SFfile.write('DW for element B\t=\t'+ str(DW_B) +' (for compounds only)\n')
                SFfile.write('d hkl\t=\t'+ str(d_hkl) +'\n')
                SFfile.write('Bragg energy\t=\t'+ str(E_bragg) +'\n')
                SFfile.write('b\t=\t'+ str(self.b_cr) +'\n')
                SFfile.write('P\t=\t'+ str(P) +'\n')
                SFfile.write('--- '+DCMName+' DCM  ---\n')
                SFfile.write('DW\t=\t'+ str(DW_A_DCM) +'\n')
                SFfile.write('F0\t=\t'+ str(F_0_DCM) +'\n')
                SFfile.write('FH\t=\t'+ str(F_H_DCM) +'\n')
                SFfile.write('FHbar\t=\t'+ str(F_Hbar_DCM) +'\n')
                SFfile.write('d hkl\t=\t'+ str(d_hkl_DCM) +'\n')
                SFfile.write('b\t=\t'+ str(b_mo) +'\n')
                SFfile.write('P\t=\t'+ str(P_DCM) +'\n')
        except IOError:
            QtGui.QMessageBox.warning(self, "Warning", 'Problem with the structure factor file.\nThe \"results\" folder may have been deleted during the analysis.')
            raise IOError('Problem with the structure factor file')

        gamma_cr = (sp.constants.value('classical electron radius')*1e10 * lambda_bragg**2)/( sp.pi * vol_unit_cell )
        theta_bragg_mo = sp.arcsin( lambda_bragg/(2 * d_hkl_DCM) )
        gamma_mo = (sp.constants.value('classical electron radius')*1e10 * lambda_bragg**2)/( sp.pi * vol_unit_cell_DCM )

        # the minimum and the maximum values of this energy interval could be reduced in order to speed up the calculation, provided that it´s always bigger than the experimental energy range
        x_min = -self.ui.doubleSpinBox_theoReflRange.value()
        x_max = self.ui.doubleSpinBox_theoReflRange.value()
        dx = 0.02 # energy step of this theoretical array of energies

        self.Theory_photonEnergy = np.arange (x_min, x_max + dx, dx) # array of energies relative to the theoretical Bragg energy
        self.Theory_Refl_sample         = np.zeros( len(self.Theory_photonEnergy) )
        self.Theory_Phase_Sample        = np.zeros( len(self.Theory_photonEnergy) )
        self.Theory_Refl_Monochromator  = np.zeros( len(self.Theory_photonEnergy) )
        self.Theory_Phase_Monochromator = np.zeros( len(self.Theory_photonEnergy) )

        #print("===============================================================")
        # calculate eta, refl and phase for each photon energy.
        for i in range (int((x_max-x_min)/dx) +1):
                eta_cr = ( 2*self.b_cr*( self.Theory_photonEnergy[i]/E_bragg )*(np.sin(self.ui.doubleSpinBox_theta.value()*np.pi/180))**2 + gamma_cr*F_0*(1-self.b_cr)/2 )\
                  / ( np.absolute(P)*gamma_cr*np.sqrt(np.absolute(self.b_cr)*F_H*F_Hbar) )
                eta_mo = ( 2*b_mo*( self.Theory_photonEnergy[i]/E_bragg )*(np.sin(theta_bragg_mo))**2 + gamma_mo*F_0_DCM*(1-b_mo)/2 )\
                  / ( np.absolute(P_DCM)*gamma_mo*np.sqrt(np.absolute(b_mo)*F_H_DCM*F_Hbar_DCM) )

                ## Sample crystal:
                EH_over_EO_plus_cr  = -1*(P/np.abs(P))*(eta_cr+np.sqrt(eta_cr**2-1))*np.sqrt(np.absolute(self.b_cr)*F_H/F_Hbar)
                EH_over_EO_minus_cr = -1*(P/np.abs(P))*(eta_cr-np.sqrt(eta_cr**2-1))*np.sqrt(np.absolute(self.b_cr)*F_H/F_Hbar)
                phi_plus_cr   = np.arctan(np.imag(EH_over_EO_plus_cr )/ np.real(EH_over_EO_plus_cr ))
                phi_minus_cr  = np.arctan(np.imag(EH_over_EO_minus_cr)/ np.real(EH_over_EO_minus_cr))
                refl_plus_cr  = np.abs(EH_over_EO_plus_cr )**2
                refl_minus_cr = np.abs(EH_over_EO_minus_cr)**2

                #print np.real(EH_over_EO_minus_cr)
                if refl_plus_cr>0 and refl_plus_cr<1: # choose the branch that has a physically meaningful reflectivity.
                    self.Theory_Refl_sample[i]  = refl_plus_cr
                    self.Theory_Phase_Sample[i] = phi_plus_cr
                    #print("ph.E: {:6.2f} | *refl_plus_cr: {:8.2f} | refl_minus_cr: {:8.2f} | *phi_plus_cr: {:8.2f} | phi_minus_cr: {:8.2f} ".format(self.Theory_photonEnergy[i], refl_plus_cr,refl_minus_cr,phi_plus_cr,phi_minus_cr))
                else:
                    self.Theory_Refl_sample[i]  = refl_minus_cr
                    self.Theory_Phase_Sample[i] = phi_minus_cr

                    if np.real(EH_over_EO_minus_cr) < 0 and self.ui.radioButton_sigma_pol_light.isChecked(): # from Zegenhagen 1993 Eq. 2.10, 2.11
                        self.Theory_Phase_Sample[i] += np.pi
                    # Taking change of sign in real(EH/E0) into account due to the change of sign in the polarization factor when using pi-polarization
                    elif np.real(EH_over_EO_minus_cr) > 0 and self.ui.radioButton_pi_pol_light.isChecked():
                       self.Theory_Phase_Sample[i] += np.pi
                       #print("ph.E: {:6.2f} | refl_plus_cr: {:8.2f} | *refl_minus_cr: {:8.2f} | phi_plus_cr: {:8.2f} | *phi_minus_cr: {:8.2f} ".format(self.Theory_photonEnergy[i], refl_plus_cr, refl_minus_cr, phi_plus_cr + np.pi, phi_minus_cr + np.pi))
                    else:
                       pass
                       #print("ph.E: {:6.2f} | refl_plus_cr: {:8.2f} | *refl_minus_cr: {:8.2f} | phi_plus_cr: {:8.2f} | *phi_minus_cr: {:8.2f} ".format(self.Theory_photonEnergy[i], refl_plus_cr, refl_minus_cr, phi_plus_cr, phi_minus_cr))


                # if np.real(EH_over_EO_minus_cr) < 0 and self.ui.radioButton_sigma_pol_light.isChecked(): # from Zegenhagen 1993 Eq. 2.10, 2.11
                #     phi_plus_cr += np.pi
                #     phi_minus_cr += np.pi
                # # Taking change of sign in real(EH/E0) into account due to the change of sign in the polarization factor when using pi-polarization
                # elif np.real(EH_over_EO_minus_cr) > 0 and self.ui.radioButton_pi_pol_light.isChecked():
                #     phi_plus_cr += np.pi
                #     phi_minus_cr += np.pi
                #
                #
                # if phi_plus_cr>0 and phi_plus_cr<np.pi/2: # choose the branch that has a physically meaningful reflectivity.
                #     self.Theory_Refl_sample[i]  = refl_plus_cr
                #     self.Theory_Phase_Sample[i] = phi_plus_cr
                #     print("ph.E: {:6.2f} | *refl_plus_cr: {:8.2f} | refl_minus_cr: {:8.2f} | *phi_plus_cr: {:8.2f} | phi_minus_cr: {:8.2f} ".format(self.Theory_photonEnergy[i], refl_plus_cr,refl_minus_cr,phi_plus_cr,phi_minus_cr))
                # else:
                #     self.Theory_Refl_sample[i]  = refl_minus_cr
                #     self.Theory_Phase_Sample[i] = phi_minus_cr
                #     print("ph.E: {:6.2f} | refl_plus_cr: {:8.2f} | *refl_minus_cr: {:8.2f} | phi_plus_cr: {:8.2f} | *phi_minus_cr: {:8.2f} ".format(self.Theory_photonEnergy[i], refl_plus_cr, refl_minus_cr, phi_plus_cr, phi_minus_cr))


                # ORIGINAL
                # if refl_plus_cr>0 and refl_plus_cr<1: # choose the branch that has a physically meaningful reflectivity.
                #     self.Theory_Refl_sample[i]  = refl_plus_cr
                #     self.Theory_Phase_Sample[i] = phi_plus_cr
                #     print("ph.E: {:6.2f} | *refl_plus_cr: {:8.2f} | refl_minus_cr: {:8.2f} | *phi_plus_cr: {:8.2f} | phi_minus_cr: {:8.2f} ".format(self.Theory_photonEnergy[i], refl_plus_cr,refl_minus_cr,phi_plus_cr,phi_minus_cr))
                # else:
                #     self.Theory_Refl_sample[i]  = refl_minus_cr
                #     self.Theory_Phase_Sample[i] = phi_minus_cr
                #
                #     if np.real(EH_over_EO_minus_cr) < 0 and self.ui.radioButton_sigma_pol_light.isChecked(): # from Zegenhagen 1993 Eq. 2.10, 2.11
                #         self.Theory_Phase_Sample[i] += np.pi
                #     # Taking change of sign in real(EH/E0) into account due to the change of sign in the polarization factor when using pi-polarization
                #     elif np.real(EH_over_EO_minus_cr) > 0 and self.ui.radioButton_pi_pol_light.isChecked():
                #        self.Theory_Phase_Sample[i] += np.pi
                #        print("ph.E: {:6.2f} | refl_plus_cr: {:8.2f} | *refl_minus_cr: {:8.2f} | phi_plus_cr: {:8.2f} | *phi_minus_cr: {:8.2f} ".format(self.Theory_photonEnergy[i], refl_plus_cr, refl_minus_cr, phi_plus_cr + np.pi, phi_minus_cr + np.pi))
                #     else:
                #        pass
                #        print("ph.E: {:6.2f} | refl_plus_cr: {:8.2f} | *refl_minus_cr: {:8.2f} | phi_plus_cr: {:8.2f} | *phi_minus_cr: {:8.2f} ".format(self.Theory_photonEnergy[i], refl_plus_cr, refl_minus_cr, phi_plus_cr, phi_minus_cr))


                ## monochromator:
                EH_over_EO_plus_mo  = -1*(P_DCM/np.absolute(P_DCM))*(eta_mo+np.sqrt(eta_mo**2-1))*np.sqrt(np.absolute(b_mo)*F_H_DCM/F_Hbar_DCM)
                EH_over_EO_minus_mo = -1*(P_DCM/np.absolute(P_DCM))*(eta_mo-np.sqrt(eta_mo**2-1))*np.sqrt(np.absolute(b_mo)*F_H_DCM/F_Hbar_DCM)
                phi_plus_mo   = np.arctan(np.imag(EH_over_EO_plus_mo )/np.real(EH_over_EO_plus_mo ))
                phi_minus_mo  = np.arctan(np.imag(EH_over_EO_minus_mo)/np.real(EH_over_EO_minus_mo))
                refl_plus_mo  = np.absolute(EH_over_EO_plus_mo )**2
                refl_minus_mo = np.absolute(EH_over_EO_minus_mo)**2
                if refl_minus_mo>0 and refl_minus_mo<1: # choose the branch that has a physically meaningful reflectivity.
                    self.Theory_Refl_Monochromator[i]  = refl_minus_mo
                    self.Theory_Phase_Monochromator[i] = phi_minus_mo
                    if np.real(EH_over_EO_plus_mo) < 0:
                        self.Theory_Phase_Monochromator[i] += np.pi
                else:
                    self.Theory_Refl_Monochromator[i]  = refl_plus_mo
                    self.Theory_Phase_Monochromator[i] = phi_plus_mo

        ## Normalization so that it won't affect the area of the the crystal reflectivity when cross-correlated.
        self.Theory_Squared_Refl_Monochromator_norm = self.Theory_Refl_Monochromator**2/sum(self.Theory_Refl_Monochromator**2)
        if len(self.Theory_Refl_sample) == len(self.Theory_Squared_Refl_Monochromator_norm):
            delta_photon = self.Theory_photonEnergy[1] - self.Theory_photonEnergy[0]

            # Make sure the axises are correct: first do a 'full' correlation, and then interpolate in the original range
            # This assumes that both arrays have the SAME LENGTH and the SAME X AXIS !!! This is very important!
            # In that case, the x_axis=0 of the array after correlation occurs for the element len(one the array), when both arrays are perfectely superimposed
            # Therefore the first element of the array after correlation is -1*len(one the array)*step_size
            full = np.correlate( self.Theory_Refl_sample, self.Theory_Squared_Refl_Monochromator_norm, mode = 'full')

            full_x = np.linspace(-1*len(self.Theory_photonEnergy)*delta_photon, (len(self.Theory_photonEnergy)-1)*delta_photon, 2*len(self.Theory_photonEnergy)-1)
            # Now interpolate the result back in the photon energy range we want: that simplifies later use.
            interp_full = interpolate.interp1d(full_x, full, kind=interp1d_kind)
            self.Theory_ReflSample_cc_ReflMono2 = interp_full(self.Theory_photonEnergy)

            self.Pyqt_View_idealRefl.clear()
            self.Pyqt_View_idealRefl.setXRange(-1,2)
            self.Pyqt_View_idealRefl.setYRange(-0.1,1.1)
            self.Pyqt_View_idealRefl.addLegend()
            self.Pyqt_View_idealRefl.plot(self.Theory_photonEnergy, self.Theory_Phase_Sample/np.pi, pen=(0,0,0), name='Phase Sample/Pi')
            self.Pyqt_View_idealRefl.plot(self.Theory_photonEnergy, self.Theory_Refl_sample, pen=(50,255,0), name='Refl Sample')
            self.Pyqt_View_idealRefl.plot(self.Theory_photonEnergy, self.Theory_Refl_Monochromator, pen=(255,144,0), name='Refl Mono')
            self.Pyqt_View_idealRefl.plot(self.Theory_photonEnergy, self.Theory_Squared_Refl_Monochromator_norm, pen=(0,0,255), name='Refl Mono^2 norm')
            self.Pyqt_View_idealRefl.plot(self.Theory_photonEnergy, self.Theory_ReflSample_cc_ReflMono2, pen=(255,0,0), name='Refl Sample Cross-correl Mono^2')
            self.Pyqt_View_refl_fit.plot(self.Theory_photonEnergy, self.Theory_ReflSample_cc_ReflMono2, pen=(255,0,0))

            self.Save_Data_and_PlotPicture('Theoretical values',\
                                           ['photonEnergy',\
                                            'Refl_sample',\
                                            'Phase_Sample',\
                                            'Refl_Monochromator',\
                                            'Phase_Monochromator',\
                                            'ReflSample_cc_ReflMono2'],\
                                           [self.Theory_photonEnergy,\
                                            self.Theory_Refl_sample,\
                                            self.Theory_Phase_Sample,\
                                            self.Theory_Refl_Monochromator,\
                                            self.Theory_Phase_Monochromator,\
                                            self.Theory_ReflSample_cc_ReflMono2],\
                                           self.Pyqt_View_idealRefl)
            self.ui.button_fit_refl.setEnabled(True)
            self.ui.button_set_refl.setEnabled(True)
            self.ui.statusbar.showMessage('Ideal Reflectivity and Phase have been successfully calculated!', 5000)
        else:
            print 'You cannot make a correlation/convolution in such conditions!!!', len(self.Theory_Refl_sample), len(self.Theory_Squared_Refl_Monochromator_norm)
            return
        self.ui.button_import.setEnabled(True)

    ## Compute any required structural factor
    # if isMono == False: Theta is taken from the GUI, and the Bragg energy calculated
    # if isMono == True:  The Bragg energy is given as argument
    # Returns d_hkl, E_bragg, F_0, F_H, F_Hbar, Debye-Waller exponent (B) (with Debye-Waller corrections)
    def calculate_structure_factor(self, Crystal, Cell_type, h, k, l, DW_method, Crystal_temp, isMono=False, E_bragg=0.0, Element_A=None, Element_B=None):
        if Element_B is None:
            a     = self.lattice_a[Crystal]
            b     = self.lattice_b[Crystal]
            c     = self.lattice_c[Crystal]
            alpha = self.lattice_alpha[Crystal]
            beta  = self.lattice_beta[Crystal]
            gamma = self.lattice_gamma[Crystal]
        else: # Compound
            a     = self.compound_lattice_a[Crystal]
            b     = self.compound_lattice_b[Crystal]
            c     = self.compound_lattice_c[Crystal]
            alpha = self.compound_lattice_alpha[Crystal]
            beta  = self.compound_lattice_beta[Crystal]
            gamma = self.compound_lattice_gamma[Crystal]

        # see https://en.wikipedia.org/wiki/Crystal_structure#Reciprocal_spacing
        # see also: https://en.wikipedia.org/wiki/Crystal_system
        #if Lattice_type=='Cubic' or Lattice_type=='Tetragonal' or Lattice_type=='Orthorhombic':
        #    d_hkl = np.sqrt(1/( (h/a)**2 + (k/b)**2 + (l/c)**2 )) # in Ang
        #elif Lattice_type=='Monoclinic':
        #    d_hkl = np.sqrt( (np.sin(beta)**2)/( (h/a)**2 + (k*np.sin(beta)/b)**2 + (l/c)**2 - 2*h*l*np.cos(beta)/(a*c) ))
        #elif Lattice_type=='Triclinic':
        #    d_hkl = np.sqrt( (1 - np.cos(alpha)**2 - np.cos(beta)**2 - np.cos(gamma)**2 + 2*np.cos(alpha)*np.cos(beta)*np.cos(gamma))\
        #                        / ( (h*np.sin(alpha)/a)**2 + (k*np.sin(beta)/b)**2 + (l*np.sin(gamma)/c)**2 ) )
        #elif Lattice_type=='Trigonal': # synonym of rhombohedral
        #    d_hkl = np.sqrt( ( (1 - 3*np.cos(alpha)**2 + 2*np.cos(alpha)**3)*a**2 )\
        #                        / ( (h**2 + k**2 + l**2)*np.sin(alpha)**2 + 2*(h*k + k*l + h*l)*(np.cos(alpha)**2 -np.cos(alpha))))
        #elif Lattice_type=='Hexagonal': # Any hexagonal
        #    d_hkl = np.sqrt( 1/( (l/c)**2 +4*( h**2 + k**2 + h*k)/(3*a**2)  ))
        #else:
        #    print Crystal, 'has an unknown lattice structure:', Lattice_type
        #    return

        #### MORE GENERAL FORMULI LEADING TO d_hkl #####
        # Unit cell volume. See International Tables for Crystallography (ITC)
        # ITC (2016) vol A, Chap. 1.3.2, p.24 (http://it.iucr.org/Ac/contents/)
        #V = a*b*c*np.sqrt( 1 - (np.cos(alpha))**2 - (np.cos(beta))**2 - (np.cos(gamma))**2 + 2*np.cos(alpha)*np.cos(beta)*np.cos(gamma))
        # or in ITC (2004) vol C., Chap. 1.1, p2 Eq. (1.1.1.1)
        V = 2*a*b*c*np.sqrt( np.sin((alpha+beta+gamma)/2)*np.sin((-alpha+beta+gamma)/2)*np.sin((alpha-beta+gamma)/2)*np.sin((alpha+beta-gamma)/2))
        ### Both V are identical !!

        # and with ITC (2004) vol C., Chap. 1.1, p2 Eq. (1.1.1.3)
        astar = b*c*np.sin(alpha)/V
        bstar = a*c*np.sin(beta)/V
        cstar = a*b*np.sin(gamma)/V
        cosAlphastar = (np.cos(beta)*np.cos(gamma)  - np.cos(alpha))/( np.sin(beta)*np.sin(gamma) )
        cosBetastar  = (np.cos(alpha)*np.cos(gamma) - np.cos(beta)) /( np.sin(alpha)*np.sin(gamma))
        cosGammastar = (np.cos(alpha)*np.cos(beta)  - np.cos(gamma))/( np.sin(alpha)*np.sin(beta) )
        # and Eq. (1.1.2.2) and (1.1.2.3)
        d_hkl = 1/ np.sqrt( (h*astar)**2 + (k*bstar)**2 + (l*cstar)**2 + 2*h*k*astar*bstar*cosGammastar + 2*h*l*astar*cstar*cosBetastar + 2*k*l*bstar*cstar*cosAlphastar )

        if isMono:
            if E_bragg==0.0: print 'calculate_structure_factor wants a reasonable Bragg value!'
            Lambda_hkl = 0. # not used
        else:
            Lambda_hkl = 2.0*d_hkl*np.sin(self.ui.doubleSpinBox_theta.value()*np.pi/180) # in Ang
            E_bragg = sp.constants.value('Planck constant in eV s')*sp.constants.value('speed of light in vacuum')/(Lambda_hkl*1e-10) # eV

        # According to Peng et al. Acta Cryst. (1996). A52, 456-470 the Debye-Waller correction to F_H is exp(-B*s**2)
        # with s = sin(theta)/lamba: in our case s=1/(2*d_hkl) in Ang-1,and B = 8 * pi**2 * <u**2_n> (Eq. 3)
        DW_A=DW_B= 0.0
        if DW_method == 'None':
            pass
        elif DW_method == 'Gao': # Gao and Peng, Acta Cryst. (1999). A55, 926
            if Crystal_temp > 80: # Eq. 2, in Ang**2
                B = self.gao_HT_a0[Element_A]\
                  + self.gao_HT_a1[Element_A]*Crystal_temp\
                  + self.gao_HT_a2[Element_A]*Crystal_temp**2\
                  + self.gao_HT_a3[Element_A]*Crystal_temp**3\
                  + self.gao_HT_a4[Element_A]*Crystal_temp**4
                DW_A=DW_B = B/(4*d_hkl**2) # OK for Si. See Flensburg et al. PRB 60 (1999) 284 (B=0.4691 at 293K)
            else: #T <80 Key
                B = self.gao_LT_a0[Element_A]\
                  + self.gao_LT_a1[Element_A]*Crystal_temp\
                  + self.gao_LT_a2[Element_A]*Crystal_temp**2\
                  + self.gao_LT_a3[Element_A]*Crystal_temp**3\
                  + self.gao_LT_a4[Element_A]*Crystal_temp**4
                DW_A=DW_B = B/(4*d_hkl**2)

        elif DW_method == 'Sears': # Sears and Shelley Acta Cryst. (1991). A47, 441-446
            reduced_temp = Crystal_temp/self.sears_Tm[Element_A]
            if reduced_temp < 0.2 : # Eq. 14
                J = self.sears_fMin1[str(Element_A)] + ((np.pi**2)/3)*self.sears_alpha[str(Element_A)]*(reduced_temp**2)
            else :
                J = 2*self.sears_fMin2[Element_A]*reduced_temp + 1/(6*reduced_temp) - self.sears_f2[Element_A]/(360*(reduced_temp**3))
            B  = 39.904*J/(self.sears_M[Element_A]*self.sears_vm[Element_A]) # Eq. 15, in Ang**2
            DW_A=DW_B = B/(4*d_hkl**2)

        elif DW_method == 'Warren': # Warren, X-ray diffraction, (1969) (only for cubic elements!)
            reduced_temp = Crystal_temp/self.sears_Tm[Element_A]
            M = 12*Crystal_temp*(sp.constants.value('Planck constant')**2)*(1/(2*d_hkl*1e-10)**2)\
              * (1 + (reduced_temp**2)/36 - (reduced_temp**4)/3600)\
              / (1e-3*self.sears_M[Element_A]*sp.constants.value('Boltzmann constant')*(self.sears_Tm[Element_A]**2)/sp.constants.value('Avogadro constant')) # Eq. 11.77, 11.75,
            DW_A=DW_B = M # p.151

        elif DW_method == 'Zywietz': # Zywietz et al., Phys. Rev. B vol54 (1996)
            # Note that Debye temperatures are also given SiC (Tab. II). Could then be used in the Warren formula, but not implemented yet.
            # We use the Mean-square displacement of each atom species, from Fig. 7:
            B_A = 8 * (np.pi)**2 * self.interpolate_value_from_csv_file(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'DW'+os.sep+'DW_Zywietz_Si.csv', 'T', Crystal_temp, '<u^2_Si>') * 1e-2 # in Ang**2
            B_B = 8 * (np.pi)**2 * self.interpolate_value_from_csv_file(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'DW'+os.sep+'DW_Zywietz_C.csv',  'T', Crystal_temp, '<u^2_C>')  * 1e-2
            DW_A = B_A/(4*d_hkl**2)
            DW_B = B_B/(4*d_hkl**2)
        else:
            QtGui.QMessageBox.warning(self, "Warning", 'Unknown Debye-Waller method: '+DW_method+'.\nProceeds without Debye-Waller correction.')


        # The structure factors:
        f0_A = self.interpolate_value_from_csv_file(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'f0.csv', '1/2dhkl', 1/(2*d_hkl), Element_A)
        f1_A = self.interpolate_value_from_csv_file(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'f1 and f2'+os.sep+string.lower(str(Element_A))+'.nff', 'E(eV)', E_bragg, 'f1', '\t')
        f2_A = self.interpolate_value_from_csv_file(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'f1 and f2'+os.sep+string.lower(str(Element_A))+'.nff', 'E(eV)', E_bragg, 'f2', '\t')
        if Element_B is not None:
            f0_B = self.interpolate_value_from_csv_file(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'f0.csv', '1/2dhkl', 1/(2*d_hkl), Element_B)
            f1_B = self.interpolate_value_from_csv_file(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'f1 and f2'+os.sep+string.lower(str(Element_B))+'.nff', 'E(eV)', E_bragg, 'f1', '\t')
            f2_B = self.interpolate_value_from_csv_file(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'f1 and f2'+os.sep+string.lower(str(Element_B))+'.nff', 'E(eV)', E_bragg, 'f2', '\t')

        structure_factor_0    = 0.0
        structure_factor_H    = 0.0
        structure_factor_Hbar = 0.0
        with open(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'Lattices'+os.sep+'AtomCoordinates_'+Cell_type+'.csv', 'rb') as atomPos:
            spamreader = csv.DictReader(atomPos, delimiter=',')
            for row in spamreader: # sum on all atomic positions
                a = float(eval(row['x (a)']))
                b = float(eval(row['y (b)']))
                c = float(eval(row['z (c)']))
                if str(row['Element']) == 'A':
                    structure_factor_0 = structure_factor_0 + (f1_A + 1j*f2_A) # for the (000), the corresponding d_khl is infinity, and the DW is then 0.
                    structure_factor_H = structure_factor_H\
                      + (f0_A - self.Z[Element_A] + f1_A + 1j*f2_A)*np.exp(2j*np.pi*(h*a + k*b + l*c) - DW_A)
                    structure_factor_Hbar = structure_factor_Hbar\
                      + (f0_A - self.Z[Element_A] + f1_A + 1j*f2_A)*np.exp(2j*np.pi*(-h*a - k*b - l*c) - DW_A)
                elif str(row['Element']) == 'B':
                    structure_factor_0 = structure_factor_0 + (f1_B + 1j*f2_B)
                    structure_factor_H = structure_factor_H\
                      + (f0_B - self.Z[Element_B] + f1_B + 1j*f2_B)*np.exp(2j*np.pi*(h*a + k*b + l*c) - DW_B)
                    structure_factor_Hbar = structure_factor_Hbar\
                      + (f0_B - self.Z[Element_B] + f1_B + 1j*f2_B)*np.exp(2j*np.pi*(-h*a - k*b - l*c) - DW_B)

            if abs(structure_factor_H) < 1e-10:
                QtGui.QMessageBox.warning(self, "Warning", 'The '+str(h)+str(k)+str(l)+' reflection of '+Crystal+' is forbidden!')
                return None, None, None, None, None, None, None, None, None
            else:
                return d_hkl, E_bragg, structure_factor_0, structure_factor_H, structure_factor_Hbar, DW_A*(4*d_hkl**2), DW_B*(4*d_hkl**2), V, Lambda_hkl


    ## Load once all possible csv files that could be necessary later on
    def loadAll_csv_Files(self):
        # Z values for most elements in the periodic table: (call for instance: self.Z['Ir'])
        self.Z = {'Ru': 44, 'Re': 75, 'Ra': 88, 'Rb': 37, 'Rh': 45, 'Be': 4, 'Ba': 56, 'Bi': 83, 'Bk': 97, 'Br': 35, 'H': 1, 'P': 15, 'Os': 76, 'Hg': 80, 'Ge': 32, 'Gd': 64, 'Ga': 31, 'Pr': 59, 'Pt': 78, 'Pu': 94, 'C': 6, 'Pb': 82, 'Pa': 91, 'Pd': 46, 'Cd': 48, 'Po': 84, 'Ho': 67, 'Hf': 72, 'K': 19, 'He': 2, 'Mg': 12, 'Mo': 42, 'Mn': 25, 'O': 8, 'S': 16, 'W': 74, 'Zn': 30, 'Eu': 63, 'Zr': 40, 'Er': 68, 'Ni': 28, 'Na': 11, 'Nb': 41, 'Nd': 60, 'Ne': 10, 'Np': 93, 'Fe': 26, 'B': 5, 'F': 9, 'Sr': 38, 'N': 7, 'Kr': 36, 'Si': 14, 'Sn': 50, 'Sm': 62, 'V': 23, 'Sc': 21, 'Sb': 51, 'Se': 34, 'Co': 27, 'Cm': 96, 'Cl': 17, 'Ca': 20, 'Cf': 98, 'Ce': 58, 'Xe': 54, 'Lu': 71, 'Cs': 55, 'Cr': 24, 'Cu': 29, 'La': 57, 'Li': 3, 'Tl': 81, 'Tm': 69, 'Th': 90, 'Ti': 22, 'Te': 52, 'Tb': 65, 'Tc': 43, 'Ta': 73, 'Yb': 70, 'Dy': 66, 'I': 53, 'U': 92, 'Y': 39, 'Ac': 89, 'Ag': 47, 'Ir': 77, 'Am': 95, 'Al': 13, 'As': 33, 'Ar': 18, 'Au': 79, 'In': 49}
        self.Z_inverted = {v: k for k, v in self.Z.iteritems()} #call: self.Z_inverted[77]

        # load the lattice data for elemental samples
        with open(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'Lattices'+os.sep+'CrystallographicData_Elemental.csv', 'rb') as lattices:
            spamreader = csv.DictReader(lattices, delimiter=',', quotechar='\'')
            self.elemental_Z = {}
            self.cell_type = {}
            self.lattice_a = {}
            self.lattice_b = {}
            self.lattice_c = {}
            self.lattice_alpha = {}
            self.lattice_beta = {}
            self.lattice_gamma = {}
            self.checked_values = {}
            for row in spamreader:
                self.ui.comboBox_DCM_Element.addItem(row['Name'])
                self.ui.comboBox_Sample_Elemental_Element.addItem(row['Name'])
                self.elemental_Z[row['Name']]   = int(row['Z'])
                self.cell_type[row['Name']]     = row['cell_type']
                self.lattice_a[row['Name']]     = float(row['a'])/100.
                self.lattice_b[row['Name']]     = float(row['b'])/100.
                self.lattice_c[row['Name']]     = float(row['c'])/100.
                self.lattice_alpha[row['Name']] = float(row['alpha'])*np.pi/180
                self.lattice_beta[row['Name']]  = float(row['beta'] )*np.pi/180
                self.lattice_gamma[row['Name']] = float(row['gamma'])*np.pi/180
                self.checked_values[row['Name']]= str(row['checked_values'])

        # load the lattice data for compounds samples
        with open(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'Lattices'+os.sep+'CrystallographicData_Compound.csv', 'rb') as lattices_comp:
            spamreader = csv.DictReader(lattices_comp, delimiter=',', quotechar='\'')
            self.compound_elementA = {}
            self.compound_elementB = {}
            self.compound_cell_type = {}
            self.compound_lattice_a = {}
            self.compound_lattice_b = {}
            self.compound_lattice_c = {}
            self.compound_lattice_alpha = {}
            self.compound_lattice_beta = {}
            self.compound_lattice_gamma = {}
            self.compound_checked_values = {}
            for row in spamreader:
                self.ui.comboBox_Sample_Compound_Element.addItem(row['Name'])
                self.compound_elementA[row['Name']]  = self.Z_inverted[int(row['Z_A'])]
                self.compound_elementB[row['Name']]  = self.Z_inverted[int(row['Z_B'])]
                self.compound_cell_type[row['Name']] = row['cell_type']
                self.compound_lattice_a[row['Name']]     = float(row['a'])/100.
                self.compound_lattice_b[row['Name']]     = float(row['b'])/100.
                self.compound_lattice_c[row['Name']]     = float(row['c'])/100.
                self.compound_lattice_alpha[row['Name']] = float(row['alpha'])*np.pi/180
                self.compound_lattice_beta[row['Name']]  = float(row['beta'] )*np.pi/180
                self.compound_lattice_gamma[row['Name']] = float(row['gamma'])*np.pi/180
                self.compound_checked_values[row['Name']]= str(row['checked_values'])

        # load the Debye-Waller according to Gao
        with open(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'DW'+os.sep+'DW_Gao_Elemental_highT.csv', 'rb') as gao:
            spamreader = csv.DictReader(gao, delimiter=',')
            self.gao_HT_Z = {}
            self.gao_HT_lattice_type = {}
            self.gao_HT_a0 = {}
            self.gao_HT_a1 = {}
            self.gao_HT_a2 = {}
            self.gao_HT_a3 = {}
            self.gao_HT_a4 = {}
            for row in spamreader:
                self.gao_HT_Z[row['symbol']]            = int(row['Z'])
                self.gao_HT_lattice_type[row['symbol']] = row['lattice_type']
                self.gao_HT_a0[row['symbol']]           = float(row['a0'])
                self.gao_HT_a1[row['symbol']]           = float(row['a1'])
                self.gao_HT_a2[row['symbol']]           = float(row['a2'])
                self.gao_HT_a3[row['symbol']]           = float(row['a3'])
                self.gao_HT_a4[row['symbol']]           = float(row['a4'])
        with open(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'DW'+os.sep+'DW_Gao_Elemental_lowT.csv', 'rb') as gao:
            spamreader = csv.DictReader(gao, delimiter=',')
            self.gao_LT_Z = {}
            self.gao_LT_lattice_type = {}
            self.gao_LT_a0 = {}
            self.gao_LT_a1 = {}
            self.gao_LT_a2 = {}
            self.gao_LT_a3 = {}
            self.gao_LT_a4 = {}
            for row in spamreader:
                self.gao_LT_Z[row['symbol']]            = int(row['Z'])
                self.gao_LT_lattice_type[row['symbol']] = row['lattice_type']
                self.gao_LT_a0[row['symbol']]           = float(row['a0'])
                self.gao_LT_a1[row['symbol']]           = float(row['a1'])
                self.gao_LT_a2[row['symbol']]           = float(row['a2'])
                self.gao_LT_a3[row['symbol']]           = float(row['a3'])
                self.gao_LT_a4[row['symbol']]           = float(row['a4'])

        # load the Debye-Waller according to Sears
        # Tm will also be used in the Warren method
        with open(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Databases'+os.sep+'DW'+os.sep+'DW_Sears.csv', 'rb') as sears:
            spamreader = csv.DictReader(sears, delimiter=',')
            self.sears_Z = {}
            self.sears_M = {}
            self.sears_lattice_type = {}
            self.sears_vm = {}
            self.sears_Tm = {}
            self.sears_alpha = {}
            self.sears_fMin2 = {}
            self.sears_fMin1 = {}
            self.sears_f2 = {}
            for row in spamreader:
                self.sears_Z[row['symbol']]            = int(row['Z'])
                self.sears_M[row['symbol']]            = float(row['M'])
                self.sears_lattice_type[row['symbol']] = row['lattice_type']
                self.sears_vm[row['symbol']]           = float(row['vm'])
                self.sears_Tm[row['symbol']]           = float(row['Tm'])
                self.sears_alpha[row['symbol']]        = float(row['alpha'])
                self.sears_fMin2[row['symbol']]        = float(row['f-2'])
                self.sears_fMin1[row['symbol']]        = float(row['f-1'])
                self.sears_f2[row['symbol']]           = float(row['f2'])

    ## GUI function: dis/enable object depending on which type of sample is selected
    def Sample_ElementalCompound_choice_changed(self):
        activate = self.ui.radioButton_Sample_Compound.isChecked()
        self.ui.comboBox_Sample_Compound_Element.setEnabled(activate)
        self.ui.label_Sample_Compound_Structure.setEnabled(activate)
        self.ui.label_Sample_Compound_Type.setEnabled(activate)
        self.ui.label_Compound_a.setEnabled(activate)
        self.ui.label_Compound_b.setEnabled(activate)
        self.ui.label_Compound_c.setEnabled(activate)
        self.ui.label_Compound_alpha.setEnabled(activate)
        self.ui.label_Compound_beta.setEnabled(activate)
        self.ui.label_Compound_gamma.setEnabled(activate)
        self.ui.label_Compound_CheckedValue.setVisible(activate)
        self.ui.comboBox_Sample_Compound_DWMethod.setEnabled(activate)
        self.ui.doubleSpinBox_Sample_Compound_Temperature.setEnabled(activate)
        self.ui.spinBox_Sample_Compound_h.setEnabled(activate)
        self.ui.spinBox_Sample_Compound_k.setEnabled(activate)
        self.ui.spinBox_Sample_Compound_l.setEnabled(activate)
        self.ui.label_Sample_Compound_i.setEnabled(activate)
        self.ui.label_DW_sample_A.setVisible(activate)
        self.ui.label_DW_sample_B.setVisible(activate)

        self.ui.label_DW_sample.setVisible(not activate)
        self.ui.comboBox_Sample_Elemental_Element.setEnabled(not activate)
        self.ui.label_Sample_Elemental_Structure.setEnabled(not activate)
        self.ui.label_Sample_Elemental_Type.setEnabled(not activate)
        self.ui.label_Elemental_a.setEnabled(not activate)
        self.ui.label_Elemental_b.setEnabled(not activate)
        self.ui.label_Elemental_c.setEnabled(not activate)
        self.ui.label_Elemental_alpha.setEnabled(not activate)
        self.ui.label_Elemental_beta.setEnabled(not activate)
        self.ui.label_Elemental_gamma.setEnabled(not activate)
        self.ui.label_Elemental_CheckedValue.setVisible(not activate)
        self.ui.comboBox_Sample_Elemental_DWMethod.setEnabled(not activate)
        self.ui.doubleSpinBox_Sample_Elemental_Temperature.setEnabled(not activate)
        self.ui.spinBox_Sample_Elemental_h.setEnabled(not activate)
        self.ui.spinBox_Sample_Elemental_k.setEnabled(not activate)
        self.ui.spinBox_Sample_Elemental_l.setEnabled(not activate)
        self.ui.label_Sample_Elemental_i.setEnabled(not activate)


    ## GUI function: refreshes the miller-Bravais (i) incides in the case of hexagonal lattices
    def refresh_forth_Miller_Bravais_indice(self):
        self.ui.label_DCM_i.setText(str(-self.ui.spinBox_DCM_h.value()-self.ui.spinBox_DCM_k.value()))
        self.ui.label_Sample_Elemental_i.setText(str(-self.ui.spinBox_Sample_Elemental_h.value()-self.ui.spinBox_Sample_Elemental_k.value()))
        self.ui.label_Sample_Compound_i.setText(str(-self.ui.spinBox_Sample_Compound_h.value()-self.ui.spinBox_Sample_Compound_k.value()))


    #####################################################
    #########    Section Fit Reflectivity    ############
    #####################################################

    ## Sets the initial parameters used for refl fit
    def set_refl_par(self):
        self.ui.doubleSpinBox_ReflFit_InitVal_Sigma.setValue(0.1)
        self.ui.doubleSpinBox_ReflFit_InitVal_Norm.setValue(np.amax(self.Exp_Refl_Normalised)/np.max(self.Theory_ReflSample_cc_ReflMono2))
        self.ui.doubleSpinBox_ReflFit_InitVal_Bgd.setValue(self.Exp_Refl_Normalised[0])
        if len(self.Theory_ReflSample_cc_ReflMono2) == 0:
            self.ui.doubleSpinBox_ReflFit_InitVal_DeltaE.setValue(0.0)
        else:
            self.ui.doubleSpinBox_ReflFit_InitVal_DeltaE.setValue(self.Theory_photonEnergy[np.argmax(self.Theory_ReflSample_cc_ReflMono2)]\
                                                                      - self.Exp_photonEnergy_BraggCentered[np.argmax(self.Exp_Refl_Normalised)])


    ## Reports the evolution of the fitting procedure in a log file
    def write_to_refl_log_file(self, text):
        try:
            with open(self.log_file_name, 'a') as Refl_log_file:
                Refl_log_file.write(text + '\n')
        except IOError:
            QtGui.QMessageBox.warning(self, "Warning", 'Problem with the log file.\nThe \"results\" folder may have been deleted during the analysis.')
            raise IOError('Problem with the reflectivity log file')
        self.ui.QTextEdit_FitResult_Refl.append(text)
        self.ui.QTextEdit_FitResult_Refl.moveCursor(QtGui.QTextCursor.End)

    # Computes the difference between the experimental values and the calculated ones
    def residuals_Refl(self, params):
        sigma = params[0]
        Norm  = params[1]
        DR = params[2]
        DE = params[3]
        Theory_refl = np.correlate (self.Theory_ReflSample_cc_ReflMono2,\
                                    self.normalized_gauss_centered(sigma, self.Theory_photonEnergy),\
                                    mode = "same") # with a centered gaussian, the axis does not change

        # Interpolates the fit functions on the precise experimental photon energies
        theo = interpolate.interp1d(self.Theory_photonEnergy, Theory_refl, kind=interp1d_kind)
        try:
            self.Theory_refl_on_Exp_points = Norm*theo(self.Exp_photonEnergy_BraggCentered+DE)
        except ValueError as err:
            QtGui.QMessageBox.warning(self, "ERROR", "ERROR: Failed to interpolate the experimental data."+\
            "ValueError in scipy.interp1d()"+\
            "\n\nThis error can occur if your experimental refl data"+\
            "\nexceeds the limits of the previous calculated theoretical data."
            "\nLimits of theoretical data:  "+str(self.Theory_photonEnergy[0])+", "+str(self.Theory_photonEnergy[-1]) + \
            "\nLimits of experimental data: "+str(self.Exp_photonEnergy_BraggCentered[0]+DE)+", "+str(self.Exp_photonEnergy_BraggCentered[-1]+DE) +\
            "\n\nYou can change the range in the theoretical reflectivity tab.")
            raise

        self.write_to_refl_log_file('Sigma='+str(sigma) + '\tNorm='+str(Norm) + '\tBgd='+str(DR) + '\tDeltaEn='+str(DE))
        # The estimated error (for a while SQRT) does not make sense as it is unit-dependant. Unless the user has a proper way of calculating the error for the reflectivity, we prefer not to weight each point at all.
        # The /np.amax(self.Exp_Refl_Normalised) only serves to somehow yield a normalized/readable value of the chi2
        return (self.Exp_Refl_Normalised-DR) - self.Theory_refl_on_Exp_points#/ np.amax(self.Exp_Refl_Normalised)


    # Fits the reflectivity
    def fit_Refl(self):
        if len(self.Exp_Refl_Normalised) == 0:
            QtGui.QMessageBox.warning(self, "Warning", 'You forgot to import data !')
            return
        if len(self.Theory_photonEnergy)==0:
            QtGui.QMessageBox.warning(self, "Warning", 'You forgot to compute the ideal reflectivity !')
            return

        self.ui.QTextEdit_FitResult_Refl.clear()
        try:
            self.log_file_name = str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+"results"+os.sep+"Fit_refl.log"
            with open(self.log_file_name, 'w') as Refl_log_file:
                Refl_log_file.write('')
        except IOError:
            QtGui.QMessageBox.warning(self, "Warning", 'Problem with the log file.\nThe \"results\" folder may have been deleted during the analysis.')
            raise IOError('Problem with the reflectivity log file')

        self.write_to_refl_log_file('All the fit parameters combinations tested are reported in the following:')
        self.ui.QTextEdit_FitResult_Refl.setLineWrapMode(QtGui.QTextEdit.NoWrap)

        self.Pyqt_View_refl_fit.clear()
        initial_parameter_list = [self.ui.doubleSpinBox_ReflFit_InitVal_Sigma.value(),\
                                  self.ui.doubleSpinBox_ReflFit_InitVal_Norm.value(),\
                                  self.ui.doubleSpinBox_ReflFit_InitVal_Bgd.value(),\
                                  self.ui.doubleSpinBox_ReflFit_InitVal_DeltaE.value()]

        # Fit !
        bestFit_param, cov_x, info, msg, ierr = scipy.optimize.leastsq (self.residuals_Refl, initial_parameter_list, args = (), ftol = 1e-24, full_output = 1)
        if cov_x is None:
            self.write_to_refl_log_file('Singular matrix encountered while optimizing')
            QtGui.QMessageBox.warning(self, "Warning", 'Singular matrix encountered while fitting.\n\nConsider changing the initial value of sigma and trying to fit again.')
            raise NameError('Fit_reflectivity: Singular matrix encountered while optimizing')

        # Chi Squared according to Pearsons definition:
        ChiSq_refl = sum(np.divide(info['fvec']**2,self.Theory_refl_on_Exp_points))/(len(self.Exp_photonEnergy_BraggCentered) - len(bestFit_param))
        # keep in mind: info['fvec'] contains the residuals used of the leastsq method. There is no need to calculate them again

        # experimental and theoretical data as defined in the residual function
        expData = self.Exp_Refl_Normalised-self.ui.doubleSpinBox_ReflFit_InitVal_Bgd.value()
        theoData = self.Theory_refl_on_Exp_points
        self.R_squared_refl = self.calculate_the_R_squared_parameter(expData,theoData)

        if self.R_squared_refl < 0 or self.R_squared_refl > 1:
            QtGui.QMessageBox.warning(self, "WARNING in section fit reflectivity",  "Unable to calculate reasonable R_squared value\nto determine the goodness of the fit.\nMaybe you have a problem with your initial fitting parameters \nor you have a very noisy signal.")
            self.ui.doubleSpinBox_ReflFit_RSquared.setValue(-1)
        else:
            self.ui.doubleSpinBox_ReflFit_RSquared.setValue(self.R_squared_refl)
        self.write_to_refl_log_file("*** R_squared = " + str(self.R_squared_refl))

        ## covariance matrix: obtained by multiplying the matrix cov_x times the residual standard deviation.
        cov = ChiSq_refl * np.diag(cov_x)
        bestFit_dev = []
        for i in range(len(bestFit_param)):
          bestFit_dev.append(np.sqrt(cov[i]))
        self.ui.doubleSpinBox_ReflFit_RedChiSquare.setValue(ChiSq_refl)
        self.ui.doubleSpinBox_ReflFit_sigma.setValue(bestFit_param[0])
        self.ui.doubleSpinBox_ReflFit_N.setValue(bestFit_param[1])
        self.ui.doubleSpinBox_ReflFit_dr.setValue(bestFit_param[2])
        self.ui.doubleSpinBox_ReflFit_de.setValue(bestFit_param[3])
        self.ui.doubleSpinBox_ReflDeviation_sigma.setValue(bestFit_dev[0])
        self.ui.doubleSpinBox_ReflDeviation_N.setValue(bestFit_dev[1])
        self.ui.doubleSpinBox_ReflDeviation_dr.setValue(bestFit_dev[2])
        self.ui.doubleSpinBox_ReflDeviation_de.setValue(bestFit_dev[3])

        bestFit_theo_refl = np.correlate (self.Theory_ReflSample_cc_ReflMono2,\
                                    self.normalized_gauss_centered(bestFit_param[0], self.Theory_photonEnergy),\
                                    mode = "same") # with a centered gaussian, the axis does not change

        fit_results_plot_note = self.data_file_name\
                                + '<br>b<span style=" vertical-align:sub;">substrate</span>='+str(self.b_cr)\
                                + '<br>Exp. rough FWHM='  + str(round(self.fwhm(self.Exp_photonEnergy_BraggCentered, self.Exp_Refl_Normalised),3))\
                                + ' eV<br>'+u"\u03C3"+'=' + str(round(bestFit_param[0]*1000., 3)) + ' meV +- (' + str(round(bestFit_dev[0]*1000., 3))\
                                + ')<br>N<span style=" vertical-align:sub;">R</span>=' + str(round(bestFit_param[1], 0)) + ' +- (' + str(round(bestFit_dev[1], 0))\
                                + ')<br>R<span style=" vertical-align:sub;">0</span>='   + str(round(bestFit_param[2], 0)) + ' +- (' + str(round(bestFit_dev[2], 0))\
                                + ')<br>'+u"\u03B4"+' h'+u"\u03BD"+'='   + str(round(bestFit_param[3], 3)) + ' eV +- (' + str(round(bestFit_dev[3], 3))\
                                + ')<br>'+u"\u03C7"+'<span style=" vertical-align:super;">2</span><span style=" vertical-align:sub;">Pearson</span>=' + str(round(ChiSq_refl, 3))
        text = pg.TextItem(html='<font size=\"5\">'+fit_results_plot_note+'</font>', color=(0,0,0), anchor=(0,0))
        text.setPos(np.amin(self.Exp_photonEnergy_BraggCentered) + bestFit_param[3], 1)
        self.Pyqt_View_refl_fit.addItem(text)
        self.Save_Data_and_PlotPicture('Exp_refl_norm_centred',\
                                       ['Exp_photonEnergy_BraggCentered',\
                                        'Exp_Refl_Normalised',\
                                        'Exp_Refl_Estimated_Error'],\
                                       [self.Exp_photonEnergy_BraggCentered + bestFit_param[3],\
                                        (self.Exp_Refl_Normalised - bestFit_param[2]) / bestFit_param[1],\
                                        self.Exp_Refl_Estimated_Error / bestFit_param[1]])
        self.Pyqt_View_refl_fit.plot(self.Exp_photonEnergy_BraggCentered + bestFit_param[3], (self.Exp_Refl_Normalised - bestFit_param[2]) / bestFit_param[1], pen=None, symbol='o', symbolBrush=(0,150,255))
        self.Pyqt_View_refl_fit.plot(self.Theory_photonEnergy, self.Theory_ReflSample_cc_ReflMono2, pen=(255,0,0))
        self.Pyqt_View_refl_fit.plot(self.Theory_photonEnergy, bestFit_theo_refl, pen=(0,0,255))
        plot_center = self.Theory_photonEnergy[np.argmax(self.Theory_ReflSample_cc_ReflMono2)]
        plot_width  = (self.Exp_photonEnergy_BraggCentered[-1]-self.Exp_photonEnergy_BraggCentered[0])*1.2
        self.Pyqt_View_refl_fit.setXRange(plot_center-plot_width/2., plot_center+plot_width/2.)
        self.Pyqt_View_refl_fit.setYRange(0, 1)

        # Error bars:
        #for photon_index in range(len(self.Exp_photonEnergy_BraggCentered)):
        #    posX = self.Exp_photonEnergy_BraggCentered[photon_index] + bestFit_param[3]
        #    posY = (self.Exp_Refl_Normalised[photon_index] - bestFit_param[2]) / bestFit_param[1]
        #    half_error = self.Exp_Refl_Estimated_Error[photon_index] / (2 * bestFit_param[1])
        #    self.Pyqt_View_refl_fit.plot([posX , posX],\
        #                                 [posY + half_error, posY - half_error],\
        #                                 pen=[255,0,0])

        self.Save_Data_and_PlotPicture('Fit_result_refl',\
                                       ['Theory_photonEnergy',\
                                        'Fit_result_Refl'],\
                                       [self.Theory_photonEnergy,\
                                        bestFit_theo_refl],\
                                       self.Pyqt_View_refl_fit)

        self.ui.button_fit_ey.setEnabled(True)
        self.ui.statusbar.showMessage('Experimental Reflectivity has been successfully fitted!', 5000)


    #######################################################
    #########    Section Fit EY: CF and CP   ##############
    #######################################################

    def EY_initSlider_valueChanged(self, who): # val not used because of actionTriggered
        if 'fc' == who:
            val = self.ui.horizontalSlider_manual_fc.value()
            self.ui.doubleSpinBox_fc.setValue(val/1000.)
        elif 'pc' == who:
            val = self.ui.horizontalSlider_manual_pc.value()
            self.ui.doubleSpinBox_pc.setValue(val/1000.)
        else:
            print "what??: ", val
        self.update_EY_manual_plot()


    # if ignore Monte Carlo analysis is checked there are no errors for the
    # experimental values. Therefore the chi squared makes no sense at all
    # and should not be displayed.
    def update_chiSquared(self):
        if self.ui.checkBox_ignore_MonteCarlo.isChecked():
            self.ui.doubleSpinBox_FitEY_RedChiSquare.setEnabled(False)
            self.ui.label_16.setEnabled(False)
            self.ui.label_fit_ey_chi.setEnabled(False)
        else:
            self.ui.doubleSpinBox_FitEY_RedChiSquare.setEnabled(True)
            self.ui.label_16.setEnabled(True)
            self.ui.label_fit_ey_chi.setEnabled(True)


    ## One of the slider has been moved by the user, then display is then updated
    def EY_initSpin_valueChanged(self, who):
        if who is 'fc':
            self.ui.horizontalSlider_manual_fc.setValue(self.ui.doubleSpinBox_fc.value()*1000.)
        elif who is 'pc':
            self.ui.horizontalSlider_manual_pc.setValue(self.ui.doubleSpinBox_pc.value()*1000.)
        else:
            print "What!?: ", val
        self.update_EY_manual_plot()


    ## Set the last fit results as initial parameters for the next fit
    def set_fitEYparam_forManualUse(self):
        self.ui.doubleSpinBox_fc.setValue(self.ui.doubleSpinBox_EYFit_fc.value())
        self.ui.doubleSpinBox_pc.setValue(self.ui.doubleSpinBox_EYFit_pc.value())
        self.ui.doubleSpinBox_n.setValue(self.ui.doubleSpinBox_EYFit_n.value())
        if self.ui.checkBox_eyfit_fitgamma.isChecked():
            self.ui.radioButton_EYinit_man_gamma.setChecked(True)
            self.ui.doubleSpinBox_EYinit_man_gamma.setValue(self.ui.doubleSpinBox_EYFit_gamma.value())
        if self.ui.checkBox_eyfit_fitSr.isChecked():
            self.ui.radioButton_EYinit_man_SR.setChecked(True)
            self.ui.doubleSpinBox_EYinit_man_SR.setValue(self.ui.doubleSpinBox_EYFit_Sr.value())

    ## Fills the log file.
    def write_line_EY_log_file(self, line):
        try:
            with open(self.path_fit_ey_log, 'a') as EY_log_file:
                EY_log_file.write(line + '\n')
        except IOError:
            QtGui.QMessageBox.warning(self, "Warning", 'Problem with the log file.\nThe \"results\" folder may have been deleted during the analysis.')
            raise IOError('Problem with the EY fit log file')
        self.ui.QTextEdit_FitResult_EY.append(line)
        self.ui.QTextEdit_FitResult_EY.moveCursor(QtGui.QTextCursor.End)


    ## Sets the suggested fitting parameters for the electron yield
    def reset_ey_par(self,):
        if 0 == len(self.Exp_EY_Normalised):
            QtGui.QMessageBox.warning(self, "Warning", 'You forgot to import data !')
            return
        self.ui.doubleSpinBox_n.setValue(self.Exp_EY_Normalised[0])
        self.ui.doubleSpinBox_n.setRange(0, 2*self.Exp_EY_Normalised[0])


    ## Plots the fit function, for the given parameters
    # This is thought to help the user find meaningful initial parameters
    def update_EY_manual_plot(self):
        if self.ui.button_fit_ey.isEnabled() and 0 != self.ui.doubleSpinBox_EYFit_n.value():
            params = lmfit.Parameters()
            params.add('Fc', value=self.ui.doubleSpinBox_fc.value())
            params.add('Pc', value=self.ui.doubleSpinBox_pc.value())
            params.add('N',  value=self.ui.doubleSpinBox_n.value())
            params.add('Delta', value=self.ui.doubleSpinBox_EYinit_Delta.value())
            params.add('gamma', value=self.get_init_value_gamma())
            params.add('Sr',  value=self.ui.doubleSpinBox_EYinit_man_SR.value())

            residuals, theoretical_EY_curve = self.residual_ey(params, True)
            red_chi_sq = sum(residuals**2)/(len(self.Exp_EY_Normalised) - (len(params)-1)) # does not fit exactely to the value what 'minimize()' computes, but it's close enough...
            self.ui.doubleSpinBox_manual_chisq.setValue(red_chi_sq)
            if self.ui.checkBox_display_manual_EY.isChecked():
                self.the_plot_EY_manual.setData(self.Theory_photonEnergy, theoretical_EY_curve)


    ## One has to clear everything and replot everything again because it is not possible to re-fresh the textItem only...
    # Called by fit_ElYield() and by checkBox_display_manual_EY.clicked
    def update_EY_plot(self, with_manual_spectrum=True):
        self.Pyqt_View_ey_fit.clear()
        fitted_N = self.ui.doubleSpinBox_EYFit_n.value()

        text = pg.TextItem(html='<font size=\"5\">'+self.fit_results_plot_note+'</font>', color=(0,0,0), anchor=(0,0))
        text.setPos(np.amin(self.Exp_photonEnergy_BraggCentered-0.5)+self.ui.doubleSpinBox_ReflFit_de.value(), 4)
        self.Pyqt_View_ey_fit.addItem(text)
        if self.ui.checkBox_display_manual_EY.isChecked() and with_manual_spectrum:
            self.the_plot_EY_manual = self.Pyqt_View_ey_fit.plot([0,1], [1,2], pen=(255,0,0))#self.Exp_photonEnergy, self.Exp_EY_Normalised/fitted_N, pen=(255,0,0))
            self.update_EY_manual_plot()
        self.the_plot_EY_fit = self.Pyqt_View_ey_fit.plot(self.Theory_photonEnergy, self.Fit_Result_EY, pen=(0,0,255))
        self.the_plot_EY_exp = self.Pyqt_View_ey_fit.plot(self.Exp_photonEnergy_BraggCentered+self.ui.doubleSpinBox_ReflFit_de.value(), self.Exp_EY_Normalised/fitted_N, pen=None, symbol='o', symbolBrush=(0,150,255))
        ey_err = pg.ErrorBarItem(x=(self.Exp_photonEnergy_BraggCentered+self.ui.doubleSpinBox_ReflFit_de.value()), y=self.Exp_EY_Normalised/fitted_N,\
                                     top=self.Exp_EY_casaXPS_Error/fitted_N, bottom=self.Exp_EY_casaXPS_Error/fitted_N, beam=0.05, pen=(200,200,200))
        self.Pyqt_View_ey_fit.addItem(ey_err)
        self.Pyqt_View_ey_fit.setXRange(np.amin(self.Exp_photonEnergy_BraggCentered)-0.5+self.ui.doubleSpinBox_ReflFit_de.value(), np.amax(self.Exp_photonEnergy_BraggCentered)+0.5+self.ui.doubleSpinBox_ReflFit_de.value())
        self.Pyqt_View_ey_fit.setYRange(0,4)

    ## Returns the gamma initial value, either theo or man
    def get_init_value_gamma(self):
        if self.ui.radioButton_EYinit_theo_gamma.isChecked():
            return self.ui.doubleSpinBox_EYinit_theo_gamma.value()
        elif self.ui.radioButton_EYinit_man_gamma.isChecked():
            return self.ui.doubleSpinBox_EYinit_man_gamma.value()

    ## Computes the array of difference between the fit funtion and the experiemental points
    def residual_ey(self, parameters, manual=False):
        Fc = parameters['Fc'].value
        Pc = parameters['Pc'].value
        N  = parameters['N'].value
        Delta = parameters['Delta'].value
        Sr  = parameters['Sr'].value
        gamma  = parameters['gamma'].value
        Psi = self.ui.doubleSpinBox_EYinit_Psi.value()
        Si  = self.ui.doubleSpinBox_EYinit_abs_si.value()

        if parameters['Sr'].vary:
            pass
        elif parameters['gamma'].vary:
            Sr, Si, Psi, Q_0, Q_h = self.compute_ndp_from_gamma(gamma, Delta)

        Theo_Sample_EY = ( 1 + Sr*self.Theory_Refl_sample + 2*Fc*Si*np.sqrt(self.Theory_Refl_sample)*np.cos( self.Theory_Phase_Sample - 2*np.pi*Pc + Psi ) )
        Theo_Sample_EY_cc_Gauss = np.correlate(Theo_Sample_EY,\
                                               self.normalized_gauss_centered(self.ui.doubleSpinBox_ReflFit_sigma.value(), self.Theory_photonEnergy),\
                                               mode = 'same') # with a centered gaussian, the axis does not change
        Theo_Sample_EY_cc_Gauss_cc_RMono2_full = np.correlate (Theo_Sample_EY_cc_Gauss, self.Theory_Squared_Refl_Monochromator_norm, mode = 'full')



        delta_photon = self.Theory_photonEnergy[1] - self.Theory_photonEnergy[0]
        full_x = np.linspace(-1*len(self.Theory_photonEnergy)*delta_photon, (len(self.Theory_photonEnergy)-1)*delta_photon, 2*len(self.Theory_photonEnergy)-1)
        interp_full = interpolate.interp1d(full_x, Theo_Sample_EY_cc_Gauss_cc_RMono2_full, kind=interp1d_kind)
        self.Theo_Sample_EY_cc_Gauss_cc_RMono2 = interp_full(self.Exp_photonEnergy_BraggCentered+self.ui.doubleSpinBox_ReflFit_de.value())

        if parameters['Sr'].vary:
            self.write_line_EY_log_file('Fc='+str(Fc) + '\tPc='+str(Pc) + '\tN='+str(N) + '\tSr='+str(Sr))
        elif parameters['gamma'].vary:
            self.write_line_EY_log_file('Fc='+str(Fc) + '\tPc='+str(Pc) + '\tN='+str(N) + '\tgamma='+str(gamma))
        else:
            self.write_line_EY_log_file('Fc='+str(Fc) + '\tPc='+str(Pc) + '\tN='+str(N))

        if manual: #return both the difference and the theoretical curve
            if self.ui.checkBox_ignore_MonteCarlo.isChecked():
                return (self.Exp_EY_Normalised/N - self.Theo_Sample_EY_cc_Gauss_cc_RMono2), interp_full(self.Theory_photonEnergy)
            else:
                return (self.Exp_EY_Normalised/N - self.Theo_Sample_EY_cc_Gauss_cc_RMono2) / (self.Exp_EY_casaXPS_Error/N), interp_full(self.Theory_photonEnergy)
        else:
            if self.ui.checkBox_ignore_MonteCarlo.isChecked():
                return (self.Exp_EY_Normalised/N - self.Theo_Sample_EY_cc_Gauss_cc_RMono2)
            else:
                return (self.Exp_EY_Normalised/N - self.Theo_Sample_EY_cc_Gauss_cc_RMono2) / (self.Exp_EY_casaXPS_Error/N)

    ### Fitting procedure for the Electron yield.
    # Check Mercurio et al. Phys. Rev. B vol88, p 045421 (2013) for more details
    def fit_ElYield(self):
        if self.ui.doubleSpinBox_ReflFit_de.value() is 0 or self.ui.doubleSpinBox_ReflFit_sigma.value() is 0:
            QtGui.QMessageBox.warning(self, "Information", "You forgot to fit the reflectivity!")
            return

        if self.ui.checkBox_AngularModeToggle.isChecked() :
            self.path_fit_ey_log = str(self.ui.LineEdit_CurrentWorkingDirectory.text()) + os.sep + 'results'+os.sep+'Fit_ey_comp'+str(self.Components_List_Used_in_EYfit)+'_slice%02i'% self.ui.spinBox_SelectedSlice.value() +'.log'
        else:
            self.path_fit_ey_log = str(self.ui.LineEdit_CurrentWorkingDirectory.text()) + os.sep + 'results'+os.sep+"Fit_ey_comp"+str(self.Components_List_Used_in_EYfit)+'.log'
        self.ui.QTextEdit_FitResult_EY.clear()
        try:
            with open(self.path_fit_ey_log, 'w') as EY_log_file:
                EY_log_file.write('')
        except IOError:
            QtGui.QMessageBox.warning(self, "Warning", 'Problem with the log file.\nThe \"results\" folder may have been deleted during the analysis.')
            raise IOError('Problem with the EY fit log file')

        # Check lmfit version (should be v0.9.0 or newer)
        # -----------------------------------------------------------------------------
        # since lmfit v0.9.0 the input parameter object is not updated during fitting.
        # This is to contain the initial parameters.
        # To get the fit result one HAS TO adress the MinimizerResult object,
        # which is the return value of lmfit.minimize()
        try:
            if StrictVersion(lmfit.__version__) < StrictVersion('0.8.3'):
                print "\nERROR: Your lmfit version is deprecated! You have lmfit v"+lmfit.__version__+"\nPlease install at least lmfit v0.9.0\nUse the command \'pip install lmfit --upgrade\' in your console."
                QtGui.QMessageBox.warning(self, "ERROR", "Your lmfit version is deprecated! You have lmfit v"+lmfit.__version__+
                                        "\nPlease install at least lmfit v0.9.0\nUse the command \'pip install lmfit --upgrade\' in your console.")
                return
            elif StrictVersion(lmfit.__version__) < StrictVersion('0.9.0'):
                print("\nWARNING: Your lmfit version is deprecated! You have lmfit v"+lmfit.__version__+
                "\nTorricelli will work, but consider to update lmfit at least to v0.9.0\nto ensure compatibility with newer Torricelli versions."+
                "\nUse the command \'pip install lmfit --upgrade\' in your console.\n")
        except (ValueError, AttributeError) as err:
            print "Version error: ",err
            print("\nERROR: There was an error regarding the lmfit package that is used to fit the yield curves!")
            if type(err).__name__ == "ValueError":
                print "\nCould not read the version of lmfit!"
            if not type(err).__name__ == "ValueError":
                print("\nTry using lmfit v0.9.2"+
                      "\nYou are using version: " + lmfit.__version__ + "\nTo uninstall and install a specific version type:"+
                      "\n\'pip uninstall lmfit\'\n\'pip install lmfit==0.9.2\'")
            return

        self.write_line_EY_log_file("All the fit parameters combinations tested are reported in the following:")
        fit_params = lmfit.Parameters()
        fit_params.add('Fc',    value=self.ui.doubleSpinBox_fc.value(), vary=self.ui.checkBox_eyfit_fitFc.isChecked())
        fit_params.add('Pc',    value=self.ui.doubleSpinBox_pc.value(), vary=self.ui.checkBox_eyfit_fitPc.isChecked())
        fit_params.add('N',     value=self.ui.doubleSpinBox_n.value(),  vary=self.ui.checkBox_eyfit_fitN.isChecked())
        fit_params.add('Delta', value=self.ui.doubleSpinBox_EYinit_Delta.value(),  vary=False)
        fit_params.add('Sr',    value=self.ui.doubleSpinBox_EYinit_man_SR.value(), vary=self.ui.checkBox_eyfit_fitSr.isChecked()    and      self.ui.radioButton_EYinit_man_SR.isChecked())
        fit_params.add('gamma', value=self.get_init_value_gamma(),                 vary=self.ui.checkBox_eyfit_fitgamma.isChecked() and (not self.ui.radioButton_EYinit_man_SR.isChecked()))
        fit_result_output = lmfit.minimize(self.residual_ey, fit_params, args=())

        if fit_result_output.success is not True:
            self.write_line_EY_log_file('Fit did not converge:'+fit_result_output.message)
            QtGui.QMessageBox.warning(self, "Fit does not converge", 'Try to change the parameter start values.\n\"'+fit_result_output.message+'\"')
            return
        else:
            self.write_line_EY_log_file('Successful fit: \"'+fit_result_output.message+'\"')
            self.ui.statusbar.showMessage('Successful fit: \"'+fit_result_output.message+'\"', 5000)

        # Calculation of R^2, goodness of fit
        self.R_squared_ey = self.calculate_the_R_squared_parameter(self.Exp_EY_Normalised/fit_result_output.params['N'].value,self.Theo_Sample_EY_cc_Gauss_cc_RMono2)

        if self.R_squared_ey < 0 or self.R_squared_ey > 1:
            QtGui.QMessageBox.warning(self, "WARNING in section fit reflectivity",  "Unable to calculate reasonable R_squared value\nto determine the goodness of the fit.\nMaybe you have a problem with your initial fitting parameters \nor you have a very noisy signal.")
            self.ui.doubleSpinBox_eyFit_RSquared.setValue(-1)
        else:
            self.ui.doubleSpinBox_eyFit_RSquared.setValue(self.R_squared_ey)

        # if ignore Monte Carlo analysis is checked there are no errors for the
        # experimental values. Therefore the chi squared makes no sense at all
        # and should not be displayed.
        if self.ui.checkBox_ignore_MonteCarlo.isChecked():
            self.ui.doubleSpinBox_FitEY_RedChiSquare.setValue(0)
        else:
            self.ui.doubleSpinBox_FitEY_RedChiSquare.setValue(fit_result_output.redchi)

        self.ui.doubleSpinBox_EYFit_fc.setValue(fit_result_output.params['Fc'].value)
        self.ui.doubleSpinBox_EYFit_pc.setValue(fit_result_output.params['Pc'].value)
        self.ui.doubleSpinBox_EYFit_n.setValue(fit_result_output.params['N'].value)
        self.ui.doubleSpinBox_stddev_ey_fc.setValue(fit_result_output.params['Fc'].stderr)
        self.ui.doubleSpinBox_stddev_ey_pc.setValue(fit_result_output.params['Pc'].stderr)
        self.ui.doubleSpinBox_stddev_n.setValue(fit_result_output.params['N'].stderr)

        self.ui.doubleSpinBox_EYFit_Sr.setValue(0)
        self.ui.doubleSpinBox_stddev_Sr.setValue(0)
        self.ui.doubleSpinBox_EYFit_Sr.setEnabled(False)
        self.ui.doubleSpinBox_stddev_Sr.setEnabled(False)
        self.ui.doubleSpinBox_EYFit_gamma.setValue(0)
        self.ui.doubleSpinBox_stddev_gamma.setValue(0)
        self.ui.doubleSpinBox_EYFit_gamma.setEnabled(False)
        self.ui.doubleSpinBox_stddev_gamma.setEnabled(False)

        if self.ui.checkBox_eyfit_fitgamma.isChecked():
            self.ui.doubleSpinBox_EYFit_gamma.setEnabled(True)
            self.ui.doubleSpinBox_stddev_gamma.setEnabled(True)
            self.ui.doubleSpinBox_EYFit_gamma.setValue(fit_result_output.params['gamma'].value)
            self.ui.doubleSpinBox_stddev_gamma.setValue(fit_result_output.params['gamma'].stderr)
            Sr, Si, Psi, Q_0, Q_h = self.compute_ndp_from_gamma(fit_result_output.params['gamma'].value, self.ui.doubleSpinBox_EYinit_Delta.value())
        elif self.ui.checkBox_eyfit_fitSr.isChecked():
            self.ui.doubleSpinBox_EYFit_Sr.setEnabled(True)
            self.ui.doubleSpinBox_stddev_Sr.setEnabled(True)
            self.ui.doubleSpinBox_EYFit_Sr.setValue(fit_result_output.params['Sr'].value)
            self.ui.doubleSpinBox_stddev_Sr.setValue(fit_result_output.params['Sr'].stderr)


        self.write_line_EY_log_file("Reduced chi squared = " + str(fit_result_output.redchi))
        self.write_line_EY_log_file("R_squared = " + str(self.R_squared_ey))
        self.write_line_EY_log_file("Correlations (unreported correlations are <  0.100):")
        for var in fit_result_output.params:
             self.write_line_EY_log_file('--> '+var +' with '+ str(fit_result_output.params[var].correl))

        selected_slice = ''
        if self.ui.checkBox_AngularModeToggle.isChecked():
            selected_slice = '<br> slice%02i' % self.ui.spinBox_SelectedSlice.value()

        self.fit_results_plot_note = self.data_file_name + selected_slice\
                                     + '<br>F<span style=" vertical-align:sub;">c</span>='    + str(round(self.ui.doubleSpinBox_EYFit_fc.value(), 3)) + ' +- (' + str(round(self.ui.doubleSpinBox_stddev_ey_fc.value(), 3))\
                                     + ')<br>P<span style=" vertical-align:sub;">c</span>='   + str(round(self.ui.doubleSpinBox_EYFit_pc.value(), 3)) + ' +- (' + str(round(self.ui.doubleSpinBox_stddev_ey_pc.value(), 3))\
                                     + ')<br>N<span style=" vertical-align:sub;">Y</span>=' + str(round(self.ui.doubleSpinBox_EYFit_n.value(), 2)) + ' +- (' + str(round(self.ui.doubleSpinBox_stddev_n.value(), 0))\
                                     + ')<br>'+u"\u03C3"+'=' + str(round(self.ui.doubleSpinBox_ReflFit_sigma.value()*1000, 3)) + ' meV'\
                                     + '<br>'+u"\u03C7"+'<span style=" vertical-align:super;">2</span><span style=" vertical-align:sub;">Red.</span>='   + str(round(self.ui.doubleSpinBox_FitEY_RedChiSquare.value(), 3))\
                                     + '<br>Comp. ' + str(self.Components_List_Used_in_EYfit)+'('+self.ui.column_name_label.text()+')'

        dummy, self.Fit_Result_EY = self.residual_ey(fit_result_output.params, True)
        self.update_EY_plot(False)
        self.the_plot_EY_fit.setData(self.Theory_photonEnergy, self.Fit_Result_EY)

        if self.ui.checkBox_AngularModeToggle.isChecked() :
            name_fit_ey = "Fit_ey_comp"+str(self.Components_List_Used_in_EYfit)+'_slice%02i' % self.ui.spinBox_SelectedSlice.value()
            name_exp_ey = 'Exp_ey_norm_centred'+str(self.Components_List_Used_in_EYfit)+'_slice%02i' % self.ui.spinBox_SelectedSlice.value()
        else:
            name_fit_ey = "Fit_ey_comp"+str(self.Components_List_Used_in_EYfit)
            name_exp_ey = 'Exp_ey_norm_centred'+str(self.Components_List_Used_in_EYfit)

        self.Save_Data_and_PlotPicture(name_exp_ey,\
                                       ['Exp_photonEnergy_BraggCentered',\
                                        'Exp_EY_Normalised',\
                                        'Exp_EY_casaXPS_Error'],\
                                       [self.Exp_photonEnergy_BraggCentered+self.ui.doubleSpinBox_ReflFit_de.value(),\
                                        self.Exp_EY_Normalised/fit_result_output.params['N'].value,\
                                        self.Exp_EY_casaXPS_Error/fit_result_output.params['N'].value])

        self.Save_Data_and_PlotPicture(name_fit_ey,\
                                       ['Theory_photonEnergy', 'Fit_Result_EY'],\
                                       [self.Theory_photonEnergy, self.Fit_Result_EY],\
                                       self.Pyqt_View_ey_fit)

        self.autoSaveResults()
        self.update_EY_plot(True)
	self.ui.statusbar.showMessage('Experimental Electron Yield has been successfully fitted!', 5000)


    ## Re-loads the list of components to be used for the EY fit.
    # NOTE that if self.ui.signal_name.text() is '', [0] is returned anyway!
    def update_component_list(self):
        self.Components_List_Used_in_EYfit = np.fromstring(str(self.ui.signal_name.text()), dtype=int, sep=' ')

    ## calculate R^2, the Coefficient of determination
    ## quantity to test goodness of fit
    ## R^2 = 0: bad, R^2 = 1: good
    def calculate_the_R_squared_parameter(self,expData,theoData):
        ss_tot = sum((expData - np.mean(expData))**2) # total sum of squares
        ss_res = sum((expData - theoData)**2) # residual sum of square
        return (1 - ss_res/ss_tot)


    """
    =========================================================================
    saves Fc and Pc and a lot of other information to the given file
    with a given description
    =========================================================================
    saves the following:
    file header
    -----------
    Torricelli Revision
    date created
    date changed
    -----------
    columns with data:

    if the file is existing: The dataset is appended to the file, except such
    a dataset already exist. Then the following happens.
    Regarding auto-generated mode:
    if Name, Component and compname do already exist the data is overwritten!
    Like all the other files in the data folder, too. So this file correspond to
    all the other files in the folder (*.png, *.log, *.dat, etc.)
    Not auto-generated: Ask the user what to do and show him what is overwritten.

    usage:
    autoSaveResults() for auto generated file with standard path and filename
    autoSaveResults(saveFilePath='fullpath') for auto generated file with specified path and filename
    autoSaveResults(description='this is awesome') for auto generated file with specified description
    autoSaveResults(saveFilePath='fullpath', description='yeah!') combination of the both above
    autoSaveResults(saveFilePath='fullpath'
                description='C1s datasets - July 2015',
                add=boolean  - add to an existing file?
                ...
                keys as described above
                )
        mode to save a certain dataset in a specific file (add to a file or create a new one)
    """
    def autoSaveResults(self, saveFilePath='auto', description='automatically generated file', add=True, **kwargs):
        # list that stores the dictionaries with the results
        results_list  = []
        comment_lines = []

        # no keywords given by user -> result file is auto-generated
        # other usage of this method may be for future use
        if len(kwargs) == 0:

            # auto generate filename if desired
            if saveFilePath == 'auto':
                filename = 'RESULTS_'
                filename += str(self.ui.LineEdit_CurrentWorkingDirectory.text()).split(os.sep)[-1]
                filename += '_Torricelli_ver'+__version__+'.csv'
            saveFilePath = str(self.ui.LineEdit_CurrentWorkingDirectory.text()) + os.sep + 'results' + os.sep + filename
            current_results = self.get_dict_with_all_values()

            # if a result file is already existing
            # search for a corresponding line to replace it
            # otherwise append a line
            # Read in the existing file
            if os.path.isfile(saveFilePath):
                try:
                    with open(saveFilePath, 'rb') as saveFile:
                        # Skip the comment line of the file and save them for later
                        tmp_pos = saveFile.tell()
                    #for line in saveFile:
                        line = saveFile.readline()
                        while line!='':
                            if not line.startswith('#'):
                                saveFile.seek(tmp_pos)
                                break
                            elif line.startswith("# file changed: "):
                                comment_lines.append("# file changed: "+str(datetime.datetime.now())[:-7]+"\n")
                            else:
                                comment_lines.append(line)

                            tmp_pos = saveFile.tell()
                            line = saveFile.readline()

                        # csv reader object
                        CSVreader = csv.DictReader(saveFile, delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
                        # add dictionaries to a list
                        # every element of the list is a dictionary containing the contents of a line.
                        # This makes accessing and sorting lines easy
                        for row in CSVreader:
                            results_list.append(row)

                except IOError as err:
                    print "Problem with opening file: \n", saveFilePath
                    print "I/O error({0}): {1}" % (e.errno, e.strerror)
                except csv.Error:
                    print "There was an Error in generating the result file.\nfile %s, line %d: %s" % (saveFilePath, reader.line_num, e)
                    sys.exit("file %s, line %d: %s" % (saveFilePath, reader.line_num, e))

                # checks if the an dataset already exists by looking for
                # the filename-prefix, the component number and the slice number
                # if a dataset is found it is replaced and the for loop breaks
                # if a dataset is not found the loop iterates until the end
                # of the results_list and the dataset is appended in the else-clause
                for it, set_of_results in enumerate(results_list):
                    if  set_of_results['Name'] == current_results['Name']\
                    and set_of_results['Component'] == current_results['Component']\
                    and set_of_results['Slice nb']  == current_results['Slice nb']:

                        results_list[it] = current_results.copy()
                        break
                else:
                    results_list.append(current_results)

                # Sort the list by keys. Begin with key with the lowest priority
                # NOTE: sorted is stable. So hierarchical sort is possible in
                #       steps reversed by the order of priority
                results_list = sorted(results_list, key=itemgetter('Slice nb'))
                results_list = sorted(results_list, key=itemgetter('Component'))
                results_list = sorted(results_list, key=itemgetter('Name'))

            # When no existing file is found, the current results are the
            # only ones to write in the file which is created automatically
            else:
                # create a file header
                comment_lines = ["# Torricelli ver"+__version__+"\n", "# file created on: "+str(datetime.datetime.now())[:-7]+"\n", "# file changed: "+str(datetime.datetime.now())[:-7]+"\n"]
                results_list.append(current_results)

            # create or replace *.csv file and write data into it
            try:
                with open(saveFilePath, 'wb') as saveFile:
                    saveFile.writelines(comment_lines)
                    #CSVwriter = csv.DictWriter(saveFile, fieldnames=csvHeader, delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
                    CSVwriter = csv.DictWriter(saveFile, fieldnames=self.Argand_ColList+['Path'], delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
                    CSVwriter.writeheader()
                    for set_of_results in results_list:
                        CSVwriter.writerow(set_of_results)

            except IOError as err:
                print "Problem with writing file: \n", saveFilePath
                print "I/O error({0}): {1}" % (e.errno, e.strerror)
            except csv.Error:
                print "There was an Error in generating the result file.\nfile %s, line %d: %s" % (saveFilePath, reader.line_num, e)
                sys.exit("file %s, line %d: %s" % (saveFilePath, reader.line_num, e))

            # show a statusmessage when finished
            self.ui.statusbar.showMessage("Results of fit appended to " + filename)

        elif kwargs == 16 and not saveFilePath=='auto':
            print "NOT IMPLEMENTED! For future use maybe."
            print "User has the choice where to save the data in the future"
        elif kwargs == 16 and saveFilePath=='auto':
            print "ERROR: Could not save file. \nYou forgot to set the filepath!"
        else:
            print "ERROR: Could not save file. \nYour keywords were incomplete! Expected 16 keywords"


    #######################################################
    #########    Section Non Dipolar Parameters   #########
    #######################################################

    ## Opens a browser to look for the gamma file
    def look_for_gamma_file(self):
        gamma_iniFile = Torricelli_program_folder_path+os.sep+"imports"+os.sep+"Databases"+os.sep+"Nondipolar_parameters_of_angular_distribution_Z1to100.ini"
        if os.path.exists(gamma_iniFile):
            self.parserGamma = ConfigParser.ConfigParser()
            self.parserGamma.read(gamma_iniFile)

            # load the sections (= available elements)
            # first section is a comment section
            self.elements_in_gammaINI = ["None"] + self.parserGamma.sections()[1:]
            self.ui.comboBox_NonDipolar_Element.addItem(self.elements_in_gammaINI[0])
            for element in self.elements_in_gammaINI[1:]:
                self.ui.comboBox_NonDipolar_Element.addItem(element[:2])
            #self.shells = []
            self.gammaParams = []
            self.ui.comboBox_NonDipolar_Element.setCurrentIndex(0)
            self.display_Gamma_file(-1)
        else:
            print "ERROR: Database file containing gamma parameters file not found found!"
            print "Looked for: "+gamma_iniFile


    # simply display the content of the gamma text file
    def display_Gamma_file(self,resetQuery):
        self.ui.textEdit_gamma.clear()
        # resetQuery is -1 if comboBox is cleared and empty
        # this prevents the function to be executed twice
        if resetQuery != -1 and self.currentElem != 0:
            shellIndex = self.ui.comboBox_NonDipolar_Shells.currentIndex()
            self.E_b = float(ast.literal_eval(self.parserGamma.get(self.elements_in_gammaINI[self.currentElem],"eb"))[shellIndex])
            self.E_kin = ast.literal_eval(self.parserGamma.get(self.elements_in_gammaINI[self.currentElem],"e_kin"))
            self.gammaParams = ast.literal_eval(self.parserGamma.get(self.elements_in_gammaINI[self.currentElem],"gamma_params"))[shellIndex]
            coreLevel = str(self.ui.comboBox_NonDipolar_Element.currentText()).strip()+self.ui.comboBox_NonDipolar_Shells.currentText()

            self.ui.textEdit_gamma.append("%s\t%s" % ("CoreLevel","BindingEnergy[eV]"))
            self.ui.textEdit_gamma.append("%s\t%3i" % (coreLevel,self.E_b))
            self.ui.textEdit_gamma.append("%s\t%s" % ("E_kin[eV]","gamma"))
            for e_kin_ind,gamma in enumerate(self.gammaParams):
                self.ui.textEdit_gamma.append("%-4i\t%5.3f" % (self.E_kin[e_kin_ind],gamma))
        else:
            self.ui.textEdit_gamma.append("Please choose an element.\n\nBe aware that non-dipolar correction theory\nis only valid for s-subshells!\n") # nothing to do yet
            self.ui.textEdit_gamma.append("Please check that all values do\ncorrespond to the reference:")
            self.ui.textEdit_gamma.append("Trzhaskovskaya et al. Photoelectron\nangular distribution parameter\nfor elements Z = 1 to Z = 54")
            self.ui.textEdit_gamma.append("and")
            self.ui.textEdit_gamma.append("Trzhaskovskaya et al. Photoelectron\nangular distribution parameter\nfor elements Z = 54 to Z = 100")


    def nonDipolar_changeElement(self):
        self.currentElem = self.ui.comboBox_NonDipolar_Element.currentIndex()
        self.ui.spinBox_NonDipolar_Element_Z.setValue(self.currentElem)
        self.nonDipolar_changeShell()

    def nonDipolar_changeElementZ(self):
        elemZ = self.ui.spinBox_NonDipolar_Element_Z.value()
        self.ui.comboBox_NonDipolar_Element.setCurrentIndex(elemZ)
        #self.nonDipolar_changeShell()

    def nonDipolar_changeShell(self):
        self.ui.comboBox_NonDipolar_Shells.clear()
        if self.currentElem != 0:
            # add subshells available for this element to comboBox_NonDipolar_Shells
            self.currentShells = ast.literal_eval(self.parserGamma.get(self.elements_in_gammaINI[self.currentElem],"shells"))
            self.ui.comboBox_NonDipolar_Shells.addItems(self.currentShells)

    def saveGammaFile(self):
        saveDirectory = QtGui.QFileDialog.getSaveFileName(self, "Save Gamma File", self.ui.LineEdit_CurrentWorkingDirectory.text(), "data files (*.dat);; All (*)")
        if saveDirectory != '':
            with open(saveDirectory, 'w') as gammaFile:
                gammaFile.write(str(self.ui.textEdit_gamma.toPlainText()))
            self.ui.statusbar.showMessage('Gamma parameters exported to file!', 3000)


    def updatePhaseShiftDifference(self):
        # delta_p and delta_d are created from the NIST Electron Elastic-Scattering Cross-Section DatabaseV3-2, via the program "Elastic32" in the menu "Database/Phaseshift"
        # delta_p and delta_d correspond to col Phase Shift (+), line 1 and 2 resp.
        self.ui.doubleSpinBox_EYinit_Delta.setValue(self.ui.doubleSpinBox_ndp_delta_d.value() - self.ui.doubleSpinBox_ndp_delta_p.value())

    def setPhotoelectronKineticEnergy(self):
        if self.ui.comboBox_NonDipolar_Element.currentIndex() == 0 and self.ui.radioButton_DQ_approx.isChecked():
            print 'You forgot to choose an element for the photoelectron kinetic energy calculation!'
            self.E_b=0
        self.ui.doubleSpinBox_ndp_Ekin.setValue(self.ui.doubleSpinBox_ndp_EBragg.value() - self.E_b)


    ### Calculate the theoretical non-dipolar parameter gamma. Equations based on:
    # G. van Straaten, M. Franke, F. C. Bocquet, F. S. Tautz, C. Kumpf
    # Non-dipolar effects in photoelectron-based normal incidence x-ray standing wave experiments
    # J. Elec. Spec. Relat. Phenom., 222, p106 (2018).

    # The yield parameters SR, SI and Psi, are updated by the gamma. valueChanged signal
    def setGammaValue(self):
        if self.ui.radioButton_D_approx.isChecked(): # Dipole approx only
            self.ui.doubleSpinBox_EYinit_theo_gamma.setValue(0.0)
            self.ui.doubleSpinBox_EYinit_man_gamma.setValue(0.0)
            self.ui.radioButton_EYinit_theo_gamma.setChecked(True)
            self.ui.radioButton_EYinit_man_gamma.setEnabled(False)
            self.ui.doubleSpinBox_EYinit_man_gamma.setEnabled(False)

        else: # Dipole + Quadrupole approx
            self.ui.radioButton_EYinit_man_gamma.setChecked(True)
            self.ui.radioButton_EYinit_man_gamma.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_man_gamma.setEnabled(True)
            if self.ui.doubleSpinBox_ndp_Ekin.value() < 0:
                QtGui.QMessageBox.warning(self, "Warning", 'The photon energy is too small for this core-level.')
                return
            if self.ui.lineEdit_angles_path.text() =='':
                QtGui.QMessageBox.warning(self, "ERROR", "It seems like that you have not loaded an angle file that connects the slices to certain angles.\n\n "\
                                                        +"Manual values are being used")

            # The gamma parameters are from the articles from TRZHASKOVSKAYA et al. Atomic Data and Nuclear Data Tables vol77 p97 and vol82 p257 (2001 and 2002)
            # The gamma parameters from the paper were converted into the file: "imports/Databases/Nondipolar_parameters_of_angular_distribution_Z1to100.ini"
            # Please double check before use !
            try:
                # 1d linear interpolation to get the gamma parameter corresponding to the given kinetic energy
                given_E_kin = self.ui.doubleSpinBox_ndp_Ekin.value()
                if given_E_kin < self.E_kin[0] or given_E_kin > self.E_kin[-1]:
                    QtGui.QMessageBox.warning(self,"ERROR", "Given kinetic Energy is out of bounds\nExpect it to be between "+str(self.E_kin[0])+" and "+str(self.E_kin[-1])+" eV")
                    self.ui.radioButton_EYinit_man_gamma.setEnabled(True)
                    return
                else:
                    gamma = np.interp(given_E_kin, self.E_kin, self.gammaParams)
                    self.ui.radioButton_EYinit_theo_gamma.setChecked(True)
                    self.ui.doubleSpinBox_EYinit_theo_gamma.setValue(gamma)

            except ValueError as warn:
                QtGui.QMessageBox.warning(self, "Warning", str(warn))

    ## Function separated from theo_ndp() because it is to be used by residual_ey()
    def compute_ndp_from_gamma(self, gamma, Delta):
        electron_emission_angle = self.ui.doubleSpinBox_ndp_phi.value()*np.pi/180 # \phi
        Reflection_angle = 2*self.ui.doubleSpinBox_sample_deviation_NI.value()*np.pi/180 # 2 times \xi
        if self.ui.radioButton_pi_pol_light.isChecked(): #Both for dipole AND dipole+quadrupole!
            Q_0 = gamma*np.cos(electron_emission_angle)/3.
            Q_h = gamma*np.cos(electron_emission_angle-Reflection_angle)/3.
            P_electrons = self.ui.doubleSpinBox_EYinit_Pe.value()
            Sr = P_electrons*P_electrons*(1+Q_h)/(1-Q_0)
            Si, Psi  = cmath.polar(P_electrons*( 1 + (Q_h-Q_0)/2. + 1j*np.tan(Delta)*(Q_h+Q_0)/2. )/(1-Q_0))
            return Sr, Si, Psi, Q_0, Q_h
        else: # sigma pol,  #Both for dipole AND dipole+quadrupole!
            return 1, 1, 0, 0, 0

    # The function that updates the SR, SI, Psi, Q0 and QH values when GUI is changed.
    def setYieldParameters(self):
        if   self.ui.radioButton_EYinit_theo_gamma.isChecked(): gamma = self.ui.doubleSpinBox_EYinit_theo_gamma.value()
        elif self.ui.radioButton_EYinit_man_gamma.isChecked():  gamma = self.ui.doubleSpinBox_EYinit_man_gamma.value()
        else: gamma=0

        Sr, Si, Psi, Q_0, Q_h = self.compute_ndp_from_gamma(gamma, self.ui.doubleSpinBox_EYinit_Delta.value())
        self.ui.doubleSpinBox_EYinit_theo_SR.setValue(Sr)
        self.ui.doubleSpinBox_EYinit_abs_si.setValue(Si)
        self.ui.doubleSpinBox_EYinit_Psi.setValue(Psi)
        self.ui.doubleSpinBox_EYinit_Q0.setValue(Q_0)
        self.ui.doubleSpinBox_EYinit_QH.setValue(Q_h)



    ## Behaviour of the GUI concerning the enabling of initial values (gamma OR SR) and looks if Fc=0
    def ndp_choose_work_with_SR_or_gamma(self):
        # First almost disable everything
        self.ui.doubleSpinBox_EYinit_theo_gamma.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_man_gamma.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_man_SR.setEnabled(False)
        self.ui.checkBox_eyfit_fitgamma.setEnabled(False)
        self.ui.checkBox_eyfit_fitSr.setEnabled(False)
        self.ui.label_si.setEnabled(False)
        self.ui.label_si_fitResult.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_abs_si.setEnabled(False)
        self.ui.label_psi.setEnabled(False)
        self.ui.label_psi_fitResult.setEnabled(False)
        self.ui.label_Q0.setEnabled(False)
        self.ui.label_QH.setEnabled(False)
        self.ui.label_Q0_fitResult.setEnabled(False)
        self.ui.label_QH_fitResult.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_Q0.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_QH.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_Q0_fitResult.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_QH_fitResult.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_Psi.setEnabled(False)
        self.ui.label_sr_from_gamma.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_theo_SR.setEnabled(False)
        self.ui.doubleSpinBox_EYFit_fc.setEnabled(False)
        self.ui.doubleSpinBox_stddev_ey_fc.setEnabled(False)
        self.ui.doubleSpinBox_EYFit_pc.setEnabled(False)
        self.ui.doubleSpinBox_stddev_ey_pc.setEnabled(False)
        self.ui.doubleSpinBox_EYFit_n.setEnabled(False)
        self.ui.doubleSpinBox_stddev_n.setEnabled(False)
        self.ui.doubleSpinBox_EYFit_gamma.setEnabled(False)
        self.ui.doubleSpinBox_stddev_gamma.setEnabled(False)
        self.ui.doubleSpinBox_EYFit_Sr.setEnabled(False)
        self.ui.doubleSpinBox_stddev_Sr.setEnabled(False)
        self.ui.label_sr_from_gamma_fitResult.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_theo_SR_fitResult.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_abs_si_fitResult.setEnabled(False)
        self.ui.doubleSpinBox_EYinit_Psi_fitResult.setEnabled(False)

        # Then enable selectively
        if self.ui.checkBox_eyfit_fitFc.isChecked():
            self.ui.doubleSpinBox_EYFit_fc.setEnabled(True)
            self.ui.doubleSpinBox_stddev_ey_fc.setEnabled(True)
        if self.ui.checkBox_eyfit_fitPc.isChecked():
            self.ui.doubleSpinBox_EYFit_pc.setEnabled(True)
            self.ui.doubleSpinBox_stddev_ey_pc.setEnabled(True)
        if self.ui.checkBox_eyfit_fitN.isChecked():
            self.ui.doubleSpinBox_EYFit_n.setEnabled(True)
            self.ui.doubleSpinBox_stddev_n.setEnabled(True)
        if self.ui.checkBox_eyfit_fitgamma.isChecked():
            self.ui.doubleSpinBox_EYFit_gamma.setEnabled(True)
            self.ui.doubleSpinBox_stddev_gamma.setEnabled(True)
        if self.ui.checkBox_eyfit_fitSr.isChecked():
            self.ui.doubleSpinBox_EYFit_Sr.setEnabled(True)
            self.ui.doubleSpinBox_stddev_Sr.setEnabled(True)

        if self.ui.checkBox_eyfit_fitFc.isChecked() or self.ui.checkBox_eyfit_fitPc.isChecked():
            self.ui.checkBox_eyfit_fitgamma.setChecked(False)


        if abs(self.ui.doubleSpinBox_fc.value())>1e-3: # Non vanishing Fc
            self.ui.checkBox_eyfit_fitSr.setEnabled(False)
            self.ui.radioButton_EYinit_man_SR.setEnabled(False)
            self.ui.doubleSpinBox_EYinit_man_SR.setEnabled(False)
            if self.ui.radioButton_EYinit_man_SR.isChecked():
                self.ui.radioButton_EYinit_man_gamma.setChecked(True)
            self.ui.label_si.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_abs_si.setEnabled(True)
            self.ui.label_psi.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_Psi.setEnabled(True)
            self.ui.label_Q0.setEnabled(True)
            self.ui.label_QH.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_Q0.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_QH.setEnabled(True)

            if self.ui.checkBox_eyfit_fitgamma.isChecked():
                self.ui.label_si_fitResult.setEnabled(True)
                self.ui.doubleSpinBox_EYinit_abs_si_fitResult.setEnabled(True)
                self.ui.label_psi_fitResult.setEnabled(True)
                self.ui.doubleSpinBox_EYinit_Psi_fitResult.setEnabled(True)
                self.ui.label_Q0_fitResult.setEnabled(True)
                self.ui.label_QH_fitResult.setEnabled(True)
                self.ui.doubleSpinBox_EYinit_Q0_fitResult.setEnabled(True)
                self.ui.doubleSpinBox_EYinit_QH_fitResult.setEnabled(True)
                self.ui.doubleSpinBox_EYinit_theo_SR_fitResult.setEnabled(True)
                self.ui.label_sr_from_gamma_fitResult.setEnabled(True)


        if not self.ui.checkBox_eyfit_fitFc.isChecked() and abs(self.ui.doubleSpinBox_fc.value())<1e-3: #Fc=0 and fixed
            self.ui.doubleSpinBox_pc.setEnabled(False)
            self.ui.checkBox_eyfit_fitPc.setChecked(False)
            self.ui.checkBox_eyfit_fitPc.setEnabled(False)
            self.ui.doubleSpinBox_EYFit_pc.setEnabled(False)
            self.ui.doubleSpinBox_stddev_ey_pc.setEnabled(False)
            self.ui.doubleSpinBox_EYinit_Delta.setEnabled(False)
            self.ui.checkBox_eyfit_fitSr.setEnabled(True)
            self.ui.label_sr.setEnabled(True)
            self.ui.radioButton_EYinit_man_SR.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_man_SR.setEnabled(True)

            if self.ui.radioButton_EYinit_theo_gamma.isChecked() or self.ui.radioButton_EYinit_man_gamma.isChecked():
                self.ui.checkBox_eyfit_fitgamma.setEnabled(True)
                self.ui.checkBox_eyfit_fitSr.setEnabled(False)
                self.ui.doubleSpinBox_EYinit_man_SR.setEnabled(False)
                if self.ui.checkBox_eyfit_fitgamma.isChecked():
                    self.ui.doubleSpinBox_EYinit_theo_SR_fitResult.setEnabled(True)
                    self.ui.label_sr_from_gamma_fitResult.setEnabled(True)
                else:
                    self.ui.doubleSpinBox_EYinit_theo_SR_fitResult.setEnabled(False)
                    self.ui.label_sr_from_gamma_fitResult.setEnabled(False)

            elif self.ui.radioButton_EYinit_man_SR.isChecked():
                self.ui.checkBox_eyfit_fitSr.setEnabled(True)
                self.ui.doubleSpinBox_EYinit_man_SR.setEnabled(True)
        else:
            self.ui.doubleSpinBox_pc.setEnabled(True)
            self.ui.checkBox_eyfit_fitPc.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_Delta.setEnabled(True)



        if not self.ui.checkBox_eyfit_fitFc.isChecked() and not self.ui.checkBox_eyfit_fitPc.isChecked(): #Fc and Pc fixed
            if self.ui.radioButton_EYinit_theo_gamma.isChecked() or self.ui.radioButton_EYinit_man_gamma.isChecked():
                self.ui.checkBox_eyfit_fitgamma.setEnabled(True)
            elif self.ui.radioButton_EYinit_man_SR.isChecked():
                self.ui.checkBox_eyfit_fitSr.setEnabled(True)


        if self.ui.radioButton_EYinit_theo_gamma.isChecked():
            self.ui.doubleSpinBox_EYinit_theo_gamma.setEnabled(True)
            self.ui.label_sr_from_gamma.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_theo_SR.setEnabled(True)
            self.ui.checkBox_eyfit_fitSr.setChecked(False)
        elif self.ui.radioButton_EYinit_man_gamma.isChecked():
            self.ui.doubleSpinBox_EYinit_man_gamma.setEnabled(True)
            self.ui.label_sr_from_gamma.setEnabled(True)
            self.ui.doubleSpinBox_EYinit_theo_SR.setEnabled(True)
            self.ui.checkBox_eyfit_fitSr.setChecked(False)
        elif self.ui.radioButton_EYinit_man_SR.isChecked():
            self.ui.doubleSpinBox_EYinit_man_SR.setEnabled(True)
            self.ui.checkBox_eyfit_fitgamma.setChecked(False)

        if self.ui.checkBox_eyfit_fitgamma.isChecked():
            self.ui.doubleSpinBox_EYFit_gamma.setEnabled(True)
            self.ui.doubleSpinBox_stddev_gamma.setEnabled(True)
        if self.ui.checkBox_eyfit_fitSr.isChecked():
            self.ui.doubleSpinBox_EYFit_Sr.setEnabled(True)
            self.ui.doubleSpinBox_stddev_Sr.setEnabled(True)


    ##########################################################
    ## ------------------ Argand Diagram ------------------ ##
    ##########################################################
    ## "Group" assembles similar "Dataset" together
    ## Data are saved in self.ui.treeWidget_Argand_List
    ## self.Argand_col is a dict of column indexes

    ## Creates a group. In groups, will be gather datasets to be displayed with the same symbol and color
    def Argand_AddGroup(self, GroupDict_new, refresh=False):
        self.Argand_QTreeWidgetSignalsSwitch(on=False)
        if GroupDict_new is False: # Called through the 'Add group' button
            group_name, group_confirmed = QtGui.QInputDialog.getText(self, 'Create a new group', 'Group name:')
            if group_confirmed:
                GroupDict = self.Argand_default_group_dictionary.copy()
                GroupDict['Name'] = group_name
            else:
                return
        else:
            GroupDict = self.Argand_default_group_dictionary.copy()
            GroupDict.update(GroupDict_new)
        item = QtGui.QTreeWidgetItem(self.ui.treeWidget_Argand_List)
        self.ui.treeWidget_Argand_List.setCurrentItem(item)
        if 'checkState' in GroupDict: # pass checkState if known
            item.setCheckState( self.Argand_col['Name'],    QtCore.Qt.Checked if GroupDict['checkState'] == 'checked' else QtCore.Qt.Unchecked)
        else:
            item.setCheckState( self.Argand_col['Name'],    QtCore.Qt.Checked)
        item.setText(       self.Argand_col['Name'],    str(GroupDict['Name']))
        item.setText(       self.Argand_col['Symbol'],  str(GroupDict['Symbol']))
        item.setText(       self.Argand_col['Pc'],      str(GroupDict['Pc']))
        item.setText(       self.Argand_col['Fc'],      str(GroupDict['Fc']))
        item.setText(       self.Argand_col['Note'],    str(GroupDict['Note']))
        if type(GroupDict['Color']) == str or type(GroupDict['Color']) == tuple:
            color = eval(str(GroupDict['Color']))
            item.setBackgroundColor( self.Argand_col['Color'], QtGui.QColor(color[0], color[1], color[2]))
        elif type(GroupDict['Color']) == QtGui.QColor:
            item.setBackgroundColor( self.Argand_col['Color'], GroupDict['Color'])
        else: print 'Unkonwn group color type:', type(GroupDict['Color'])
        #item.setToolTip(   self.Argand_col['Name'], os.path.basename(str(DataDict['Path'])))
        item.setIcon(0, QtGui.QIcon(Torricelli_program_folder_path + os.sep+'imports'+os.sep+'Torricelli_icon.png'))
        item.setExpanded(True)
        item.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsUserCheckable))

        self.Argand_QTreeWidgetSignalsSwitch(on=True)
        if refresh: self.Argand_refresh_tree_and_plot()
        return item

    ## Generic function that adds a data point to the treeWidget and plots into the Argand diagram
    # takes in dict that contains all data and metadata of a point and adds it to the given group (gp)
    def Argand_AddDataset(self, gp, DataDict, refresh=False):
        if DataDict['Fc_err'] == '': DataDict['Fc_err'] = 0.0001
        if DataDict['Pc_err'] == '': DataDict['Pc_err'] = 0.0001
        self.Argand_QTreeWidgetSignalsSwitch(on=False)
        child = QtGui.QTreeWidgetItem(gp)
        child.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable))
        if 'checkState' in DataDict: # pass checkState if known
            child.setCheckState(self.Argand_col['Name'],      QtCore.Qt.Checked if DataDict['checkState'] == 'checked' else QtCore.Qt.Unchecked)
        else:
            child.setCheckState(self.Argand_col['Name'],      QtCore.Qt.Checked)
        child.setText(      self.Argand_col['Name'],      str(DataDict['Name']))
        child.setToolTip(   self.Argand_col['Name'],      str(DataDict['Path']))
        if type(DataDict['Color']) == str or type(DataDict['Color']) == tuple:
            color = eval(str(DataDict['Color']))
            child.setBackgroundColor( self.Argand_col['Color'], QtGui.QColor(color[0], color[1], color[2]))
        elif type(DataDict['Color']) == QtGui.QColor:
            child.setBackgroundColor( self.Argand_col['Color'], DataDict['Color'])
        else: print 'Unkonwn point color type:', type(DataDict['Color'])
        child.setText(      self.Argand_col['Symbol'],    str(DataDict['Symbol']))
        child.setText(      self.Argand_col['Pc'],        str(DataDict['Pc']))
        child.setText(      self.Argand_col['Pc_err'],    str(DataDict['Pc_err']))
        child.setText(      self.Argand_col['Fc'],        str(DataDict['Fc']))
        child.setText(      self.Argand_col['Fc_err'],    str(DataDict['Fc_err']))
        child.setText(      self.Argand_col['Sr'],        str(DataDict['Sr']))
        child.setText(      self.Argand_col['Sr_err'],    str(DataDict['Sr_err']))
        child.setText(      self.Argand_col['|Si|'],      str(DataDict['|Si|']))
        child.setText(      self.Argand_col['Psi'],       str(DataDict['Psi']))
        child.setText(      self.Argand_col['Q_0'],       str(DataDict['Q_0']))
        child.setText(      self.Argand_col['Q_H'],       str(DataDict['Q_H']))
        child.setText(      self.Argand_col['Gamma'],     str(DataDict['Gamma']))
        child.setText(      self.Argand_col['Gamma_err'], str(DataDict['Gamma_err']))
        child.setText(      self.Argand_col['Delta'],     str(DataDict['Delta']))
        child.setText(      self.Argand_col['Sigma'],     str(DataDict['Sigma']))
        child.setText(      self.Argand_col['Component'], str(DataDict['Component']))
        child.setText(      self.Argand_col['Slice nb'],  str(self.intOrEmpty(DataDict['Slice nb'])))
        child.setText(      self.Argand_col['delta hnu'], str(DataDict['delta hnu']))
        child.setText(      self.Argand_col['Yield file'],str(DataDict['Yield file']))
        child.setText(      self.Argand_col['Note'],      str(DataDict['Note']))
        child.setText(      self.Argand_col['Core level'],str(DataDict['Core level']))
        child.setText(      self.Argand_col['Phi'],       str(DataDict['Phi']))
        child.setText(      self.Argand_col['P el'],      str(DataDict['P el']))
        child.setText(      self.Argand_col['Zeta'],      str(DataDict['Zeta']))
        child.setText(      self.Argand_col['b sample'],  str(DataDict['b sample']))
        child.setText(      self.Argand_col['b DCM'],     str(DataDict['b DCM']))
        child.setText(      self.Argand_col['Xi'],        str(DataDict['Xi']))
        child.setText(      self.Argand_col['Pol.'],      str(DataDict['Pol.']))
        child.setText(      self.Argand_col['P Refl'],    str(DataDict['P Refl']))
        child.setText(      self.Argand_col['R2 Refl'],   str(DataDict['R2 Refl']))
        child.setText(      self.Argand_col['X2 Yield'],  str(DataDict['X2 Yield']))
        child.setText(      self.Argand_col['Monte Carlo analysis'], str(DataDict['Monte Carlo analysis']))
        child.setText(      self.Argand_col['DW'],        str(DataDict['DW']))
        child.setText(      self.Argand_col['Temp.'],     str(DataDict['Temp.']))
        child.setText(      self.Argand_col['(hkl)'],     str(DataDict['(hkl)']))
        child.setText(      self.Argand_col['Substrate'], str(DataDict['Substrate']))

        # Alignment settings
        #child.setTextElideMode(self.Argand_col['Yield file'], QtCore.Qt.ElideLeft)
        #child.setTextAlignment(self.Argand_col['Yield file'], QtCore.Qt.ElideLeft)

        # add Datapoint to diagram
        if child.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked:
            try:
                self.argand.addDataSet(data_argand=[float(child.text(self.Argand_col['Pc'])), float(child.text(self.Argand_col['Fc']))],\
                                       data_err=[self.Argand_error_OR_0(child.text(self.Argand_col['Pc_err'])), self.Argand_error_OR_0(child.text(self.Argand_col['Fc_err']))], \
                                       drawError=self.ui.checkBox_Argand_display_errorBars.isChecked(),\
                                       color=child.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                       symb=str(child.text(self.Argand_col['Symbol'])),\
                                       ident=id(child))
            except ValueError:
                self.argand.addDataSet(data_argand=[0.0, 0.0],\
                                       data_err=[0.0, 0.0], \
                                       drawError=self.ui.checkBox_Argand_display_errorBars.isChecked(),\
                                       color=child.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                       symb=str(child.text(self.Argand_col['Symbol'])),\
                                       ident=id(child))

        if child.text(self.Argand_col['Pc']) == '-' or float(child.text(self.Argand_col['Fc']))<1e-8:
            child.setCheckState(self.Argand_col['Name'], False)


        self.Argand_QTreeWidgetSignalsSwitch(on=True)
        if refresh: self.Argand_groupAverage([gp]) # recalculate group vector and replot it in argand diagram

    # If the error are not existing, the '-' will be replaced by very small value,
    # if the error bars exist then the value is just given.
    # input text, output float
    def Argand_error_OR_0(self, err):
        if ('-' == err) or ('' == err):
            return 1e-5
        else:
            return float(err)

    ## Recalculates averages and refresh display
    def Argand_updateItems(self, item_list, col=None, recalcGP=True):

        for item in item_list:

            # recalculate group average if points were edited
            if recalcGP and self.Argand_isDataPoint(item):
                self.Argand_groupAverage(gp_items=[item.parent()], refresh=False)

            # check if group item, then delete and replot groupAverage
            if self.Argand_isGroup(item):
                # remove group item if existing
                if id(item) in self.argand.originVectorDict:
                    self.argand.remove_originVector(id(item))
                # check/uncheck all children (child items are removed recursivly via this function)
                for i in range(item.childCount()):
                    item.child(i).setCheckState(self.Argand_col['Name'], item.checkState(self.Argand_col['Name']))
                if item.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked:
                    self.Argand_replotGroupAverage(item)

            # if not group item it is a child. Remove if existing and add new item if checked
            elif not self.Argand_isGroup(item):
                # remove item if existing
                if id(item) in self.argand.dataSetDict:
                    self.argand.remove_dataSet(id(item))
                # add item if checked
                if item.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked:
                    try:
                        self.argand.addDataSet(data_argand=[float(item.text(self.Argand_col['Pc'])), float(item.text(self.Argand_col['Fc']))],\
                                               data_err=[float(item.text(self.Argand_col['Pc_err'])), float(item.text(self.Argand_col['Fc_err']))], \
                                               drawError=self.ui.checkBox_Argand_display_errorBars.isChecked(),\
                                               color=item.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                               symb=str(item.text(self.Argand_col['Symbol'])),\
                                               ident=id(item))
                    except ValueError:
                        self.argand.addDataSet(data_argand=[0.0, 0.0],\
                                               data_err=[0.0, 0.0], \
                                               drawError=self.ui.checkBox_Argand_display_errorBars.isChecked(),\
                                               color=item.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                               symb=str(item.text(self.Argand_col['Symbol'])),\
                                               ident=id(item))

        self.Argand_selectionChanged()




    ## Removes the selected group and its datasets, or the selected current datasets
    # Since the items in the diagram are connected with the id() of the TreeWidgetItems
    # we can access each single element and remove it. There is no need of replotting the whole diagram.
    def Argand_Remove(self, item_list):
        # do not use the remove signal.
        # reason: if several items are removed the signal would be emitted after each removed item
        # In this way the group average is calculated AFTER removal of ALL the (selected) items
        name=''
        for i in range(len(item_list)):
            if i<10:
                name = name + str(item_list[i].text(self.Argand_col['Name'])) + '\n'
        if len(item_list)>=10:
            name = name + '...'
        reply = QtGui.QMessageBox.question(self, 'Delete items',\
                                           "Are you sure you want to delete the following item(s)?\n"+name,\
                                           QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            groupsChanged = set()
            item_list_ch = set()
            item_list_gp = set()

            # Devide item_list in children and groups to avoid conflicts if removing both simultaneously
            for currentItem in item_list:
                if not self.Argand_isGroup(currentItem):
                    item_list_ch.add(currentItem)
                elif self.Argand_isGroup(currentItem):
                    item_list_gp.add(currentItem)
                else:
                    print "ERROR while removing item: unknown item type."

            # Make sure you delete points BEFORE groups!
            # Otherwise there is a bug when deleting points of a group together with the parent group.
            for currentItem in item_list_ch: # Iterate through all points
                if not self.Argand_isGroup(currentItem):
                    # if the group that is changed will be deleted, too
                    # avoid that the group will be updated because
                    # it will not exist anymore
                    if not currentItem.parent() in item_list:
                        groupsChanged.add(currentItem.parent())
                    self.argand.remove_dataSet(id(currentItem))

                    # delete the item in the TreeWidget
                    sip.delete(currentItem) # using the C++ 'delete' command... works fine and immediately

            # Deleting groups including their children
            for currentItem in item_list_gp: # Iterate through all groups
                # If a group is deleted, make sure the children are deleted, too
                if self.Argand_isGroup(currentItem):
                    for i in range(currentItem.childCount()):
                        self.argand.remove_dataSet(id(currentItem.child(i)))
                    self.argand.remove_originVector(id(currentItem))

                    # delete the item in the TreeWidget
                    sip.delete(currentItem) # using the C++ 'delete' command... works fine and immediately

            # recalculate the group average of the groups that changed and are still existant
            self.Argand_groupAverage(gp_items=groupsChanged)


    ## This will remove all elements of your list and clear the Argand Diagram
    def Argand_RemoveAll(self):
        dialog = QDialog_removeAll()
        if dialog.exec_():
            self.Argand_Save(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+self.argand_SaveSubFolder+'autosave_'+self.timestamp()+'_beforeRemoveAll.csv')
            self.ui.treeWidget_Argand_List.clear() # clear the TreeWidget
            self.argand.clearArgand() # clear the argandDiagram


    ## Ask the user to choose the .log file containing Torricelli fit results in which results are loaded
    def Argand_ValueLogFile(self):
        current_item = self.ui.treeWidget_Argand_List.currentItem()
        if current_item.parent() is None:
            current_gp = current_item
        else:
            current_gp = current_item.parent()
        if current_gp is not None and self.Argand_isGroup(current_gp):
            dataset_names = QtGui.QFileDialog.getOpenFileNames(self, "Open Files", self.ui.LineEdit_CurrentWorkingDirectory.text(), "EY fit results(*.log);; All (*)")
            for dataset_name in dataset_names:
                if dataset_name is not '':
                    try:
                        with open(dataset_name, 'r') as log_file:
                            lastLine = log_file.readlines()[-1]
                            dic = self.Argand_default_data_dictionary
                            if 5==len(lastLine.split('\t')): # Output from old Torricelli version (before r70)
                                dic.update({'Fc'        : lastLine.split('\t')[0].split('=')[1],\
                                            'Pc'        : lastLine.split('\t')[1].split('=')[1],\
                                            'Q'         : lastLine.split('\t')[3].split('=')[1],\
                                            'Delta'     : lastLine.split('\t')[4].split('=')[1],\
                                            'Path'      : dataset_name,\
                                            'Color'     : current_gp.backgroundColor(self.Argand_col['Color']),\
                                            'Symbol'    : 'o'})
                                self.Argand_AddDataset(current_gp, dic)
                            else:
                                QtGui.QMessageBox.warning(self, "Warning", 'You are trying to open a log file that EITHER did not converge OR has an unknown format')
                    except IOError as e:
                        QtGui.QMessageBox.warning(self, "Warning", "Problem with the selected file.")
                        print "I/O error({0}): {1}".format(e.errno, e.strerror)


    ##  Requires the user to type the values in.
    def Argand_ManualValues(self):
        current_item = self.ui.treeWidget_Argand_List.currentItem()
        if current_item.parent() is None:
            current_gp = current_item
        else:
            current_gp = current_item.parent()

        if current_gp is not None and self.Argand_isGroup(current_gp):
            dic = self.Argand_default_data_dictionary.copy()
            dialog = QDialog_manualVal()
            if dialog.exec_(): # only if OK is clicked
                name = str(dialog.ui.lineEdit_name.text())
                if name == "":
                    name = 'Manually added'
                dic.update({'Pc'        : dialog.ui.doubleSpinBox_pc.value(),\
                            'Fc'        : dialog.ui.doubleSpinBox_fc.value(),\
                            'Gamma'     : dialog.ui.doubleSpinBox_gamma.value(),\
                            'SR'        : dialog.ui.doubleSpinBox_SR.value(),\
                            'Delta'     : dialog.ui.doubleSpinBox_delta.value(),\
                            'Pc_err'    : dialog.ui.doubleSpinBox_pcErr.value(),\
                            'Fc_err'    : dialog.ui.doubleSpinBox_fcErr.value(),\
                            'Gamma_err' : dialog.ui.doubleSpinBox_gammaErr.value(),\
                            'SR_err'    : dialog.ui.doubleSpinBox_SRErr.value(),\
                            'Symbol'    : 'o',\
                            'Color'     : current_gp.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                            'Name'      : name})
                self.Argand_AddDataset(current_gp, dic)


    ## Displays the selected items in the Diagram
    # Works only for data sets. No average value of the group yet.
    def Argand_replotDiagram(self):
        self.ui.statusbar.showMessage("LOADING & PLOTTING - in progress")
        self.argand.clearArgand()
        # show a ProgressBar in statusbar while plotting
        progressLabel0 = QtGui.QLabel()
        progressLabel1 = QtGui.QLabel()
        progressLabel2 = QtGui.QLabel()
        progressBarGROUP = QtGui.QProgressBar()
        progressBarCHILD = QtGui.QProgressBar()
        progressLabel0.setText("PLOTTING - ")
        progressLabel1.setText("Groups: ")
        progressLabel2.setText("Datapoints of group: ")
        self.ui.statusbar.addPermanentWidget(progressLabel0)
        self.ui.statusbar.addPermanentWidget(progressLabel1)
        self.ui.statusbar.addPermanentWidget(progressBarGROUP)
        self.ui.statusbar.addPermanentWidget(progressLabel2)
        self.ui.statusbar.addPermanentWidget(progressBarCHILD)

        # Unfortunately QTreeWidgetItemIterator does not work in Python
        # Using: https://riverbankcomputing.com/pipermail/pyqt/2007-July/016823.html
        root = self.ui.treeWidget_Argand_List.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count): # Iterate on the groups
            gp = root.child(i)
            if gp.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked:
                if str(gp.text(self.Argand_col['Pc_err'])) == '-': g_Pcerr = 0.0
                else : g_Pcerr = float(gp.text(self.Argand_col['Pc_err']))
                if str(gp.text(self.Argand_col['Fc_err'])) == '-': g_Fcerr = 0.0
                else : g_Fcerr = float(gp.text(self.Argand_col['Fc_err']))
                try:
                    self.argand.addOriginVector(pc=float(gp.text(self.Argand_col['Pc'])),\
                                                fc=float(gp.text(self.Argand_col['Fc'])),\
                                                pc_err=g_Pcerr,\
                                                fc_err=g_Fcerr,\
                                                drawOriginLine = self.ui.checkBox_Argand_display_originVectors.isChecked(),\
                                                drawError = self.ui.checkBox_Argand_display_group_errorBars.isChecked(),\
                                                symb=str(gp.text(self.Argand_col['Symbol'])),\
                                                color=gp.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                                ident=id(gp))
                # if no float value for pc or fc is given draw an origin vector with pc and fc equal 0
                except ValueError:
                    print("\nWarning: Group vector positions and fractions are not computable. Group is empty or one data set has corrupt values.\n")
                    self.argand.addOriginVector(pc=0.0,\
                                                fc=0.0,\
                                                pc_err=0.0,\
                                                fc_err=0.0,\
                                                drawOriginLine = self.ui.checkBox_Argand_display_originVectors.isChecked(),\
                                                drawError = self.ui.checkBox_Argand_display_group_errorBars.isChecked(),\
                                                symb=str(gp.text(self.Argand_col['Symbol'])),\
                                                color=gp.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                                ident=id(gp))

                gp_children = gp.childCount()
                for j in range(gp_children): # Iterate in all points in a group
                    point = gp.child(j)
                    if point.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked:
                        if str(gp.text(self.Argand_col['Pc_err'])) == '-': Pcerr = 0.0
                        else : Pcerr = float(point.text(self.Argand_col['Pc_err']))
                        if str(gp.text(self.Argand_col['Fc_err'])) == '-': Fcerr = 0.0
                        else : Fcerr = float(point.text(self.Argand_col['Fc_err']))

                        try:
                            self.argand.addDataSet(data_argand=[float(point.text(self.Argand_col['Pc'])), float(point.text(self.Argand_col['Fc']))],\
                                                   data_err=[Pcerr, Fcerr],\
                                                       #[float(point.text(self.Argand_col['Pc_err'])), float(point.text(self.Argand_col['Fc_err']))],\
                                                   drawError=self.ui.checkBox_Argand_display_errorBars.isChecked(), \
                                                   color=point.backgroundColor(self.Argand_col['Color']).getRgb()[0:3], \
                                                   symb=str(point.text(self.Argand_col['Symbol'])), \
                                                   ident=id(point))
                        except ValueError:
                            print("\nWarning: Dataset vector positions and fractions are not computable. Group is empty or one data set has corrupt values.\n")
                            self.argand.addDataSet(data_argand=[0.0, 0.0],\
                                                   data_err=[0.0, 0.0],\
                                                       #[float(point.text(self.Argand_col['Pc_err'])), float(point.text(self.Argand_col['Fc_err']))],\
                                                   drawError=self.ui.checkBox_Argand_display_errorBars.isChecked(), \
                                                   color=point.backgroundColor(self.Argand_col['Color']).getRgb()[0:3], \
                                                   symb=str(point.text(self.Argand_col['Symbol'])), \
                                                   ident=id(point))

                    progressBarGROUP.setValue(float((i+1))/child_count*100)
                    progressBarCHILD.setValue(float((j+1))/gp_children*100)
                    # old but gold:
                    #self.ui.statusbar.showMessage("PLOTTING - "+self.progressBar(i+1,child_count,50,prefix="Groups: ")+"   "+self.progressBar(j+1,gp_children,50,prefix="Datapoints of group: "), 20000)

        # remove the progress bars
        self.ui.statusbar.removeWidget(progressLabel0)
        self.ui.statusbar.removeWidget(progressLabel1)
        self.ui.statusbar.removeWidget(progressBarGROUP)
        self.ui.statusbar.removeWidget(progressLabel2)
        self.ui.statusbar.removeWidget(progressBarCHILD)
        self.Argand_splitVector()
        self.Argand_Labels(self.ui.checkBox_displayLabels.isChecked())
        self.ui.statusbar.showMessage("LOADING & PLOTTING - complete", 10000)


    ## replots the group average vectors if there were changes in the treeWidget
    def Argand_replotGroupAverage(self, item):
        if self.Argand_isGroup(item) and item.childCount()>0:
            # remove the old group vector if there is already one in the diagram
            if id(item) in self.argand.originVectorDict:
                self.argand.remove_originVector(ident=id(item))
            if item.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked:
                try:
                    self.argand.addOriginVector(pc=float(item.text(self.Argand_col['Pc'])),\
                                                fc=float(item.text(self.Argand_col['Fc'])),\
                                                pc_err=self.Argand_error_OR_0(item.text(self.Argand_col['Pc_err'])),\
                                                fc_err=self.Argand_error_OR_0(item.text(self.Argand_col['Fc_err'])),\
                                                drawOriginLine = self.ui.checkBox_Argand_display_originVectors.isChecked(),\
                                                drawError = self.ui.checkBox_Argand_display_group_errorBars.isChecked(),\
                                                symb=str(item.text(self.Argand_col['Symbol'])),\
                                                color=item.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                                ident=id(item))
                except ValueError:
                    print("\nWarning: Group vector positions and fractions are not computable. Group is empty or one data set has corrupt values.\n")
                    self.argand.addOriginVector(pc=0.0,\
                                                fc=0.0,\
                                                pc_err=0.0,\
                                                fc_err=0.0,\
                                                drawOriginLine = self.ui.checkBox_Argand_display_originVectors.isChecked(),\
                                                drawError = self.ui.checkBox_Argand_display_group_errorBars.isChecked(),\
                                                symb=str(item.text(self.Argand_col['Symbol'])),\
                                                color=item.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                                ident=id(item))
        # remove group vector if the number of childs is empty
        elif self.Argand_isGroup(item) and item.childCount()==0 and id(item) in self.argand.originVectorDict:
                self.argand.remove_originVector(ident=id(item))

        self.Argand_Labels(self.ui.checkBox_displayLabels.isChecked())


    ## Compute the average Fc and Pc for all groups
    # Uses a proper error propagation
    def Argand_groupAverage(self, gp_items=[], refresh=True):
        self.Argand_QTreeWidgetSignalsSwitch(on=False)
        root = self.ui.treeWidget_Argand_List.invisibleRootItem()
        # if no items are given process all group items
        if len(gp_items) == 0:
            gp_items = map(root.child, range(root.childCount()))
        if root.childCount()==0: return # There is nothing at all!

        gp_items_with_possible_averaging = gp_items
        # if at least on point has no error bars, then no average is calculated:
        for current_gp in gp_items: # Iterate on the groups
            for child_index in range(current_gp.childCount()):
                if current_gp.child(child_index).text(self.Argand_col['Pc_err']) == '-' or current_gp.child(child_index).text(self.Argand_col['Fc_err']) == '-' or current_gp.child(child_index).text(self.Argand_col['Pc_err']) == '' or current_gp.child(child_index).text(self.Argand_col['Fc_err']) == '' or float(current_gp.child(child_index).text(self.Argand_col['Pc_err']))<1e-8 or float(current_gp.child(child_index).text(self.Argand_col['Fc_err']))<1e-8:
                    current_gp.setText(self.Argand_col['Pc'], '0')
                    current_gp.setText(self.Argand_col['Fc'], '0')
                    current_gp.setText(self.Argand_col['Pc_err'], '-')
                    current_gp.setText(self.Argand_col['Fc_err'], '-')
                    gp_items_with_possible_averaging.remove(current_gp)
                    break

        for current_gp in gp_items_with_possible_averaging: # Iterate on the groups
            if current_gp.childCount() == 0:
                current_gp.setText(self.Argand_col['Pc'], '-')
                current_gp.setText(self.Argand_col['Fc'], '-')
                current_gp.setText(self.Argand_col['Pc_err'], '-')
                current_gp.setText(self.Argand_col['Fc_err'], '-')
            elif current_gp.childCount() == 1:
                current_gp.setText(self.Argand_col['Pc'], current_gp.child(0).text(self.Argand_col['Pc']))
                current_gp.setText(self.Argand_col['Fc'], current_gp.child(0).text(self.Argand_col['Fc']))
                current_gp.setText(self.Argand_col['Pc_err'], current_gp.child(0).text(self.Argand_col['Pc_err']))
                current_gp.setText(self.Argand_col['Fc_err'], current_gp.child(0).text(self.Argand_col['Fc_err']))
            else: # At least 2 points
                # First go into cartesian coordinates, where the average is performed
                av_Re = 0
                av_Im = 0
                av_weighting_norm_factor_Re = 0
                av_weighting_norm_factor_Im = 0
                for child_index in range(current_gp.childCount()):
                    try:
                        child_pc = float(current_gp.child(child_index).text(self.Argand_col['Pc']))
                        child_fc = float(current_gp.child(child_index).text(self.Argand_col['Fc']))
                    except ValueError:
                        child_pc = 0.0
                        child_fc = 0.0
                        QtGui.QMessageBox.warning(self, "ERROR", "Your coherent position or coherent fraction is not computable. Check your yield fit!")
                    pc_err_child = float(current_gp.child(child_index).text(self.Argand_col['Pc_err']))
                    fc_err_child = float(current_gp.child(child_index).text(self.Argand_col['Fc_err']))
                    err_child_Re = np.sqrt( (np.cos(2*np.pi*child_pc)*fc_err_child)**2 + (2*np.pi*child_fc*np.sin(2*np.pi*child_pc)*pc_err_child)**2 )
                    err_child_Im = np.sqrt( (np.sin(2*np.pi*child_pc)*fc_err_child)**2 + (2*np.pi*child_fc*np.cos(2*np.pi*child_pc)*pc_err_child)**2 )
                    av_weighting_norm_factor_Re = av_weighting_norm_factor_Re + 1/(err_child_Re)**2
                    av_weighting_norm_factor_Im = av_weighting_norm_factor_Im + 1/(err_child_Im)**2
                    av_Re = av_Re + child_fc*np.cos(2*np.pi*child_pc)/(err_child_Re)**2
                    av_Im = av_Im + child_fc*np.sin(2*np.pi*child_pc)/(err_child_Im)**2

                av_Re = av_Re / av_weighting_norm_factor_Re
                av_Im = av_Im / av_weighting_norm_factor_Im
                av_err_Re = np.sqrt(1/av_weighting_norm_factor_Re)
                av_err_Im = np.sqrt(1/av_weighting_norm_factor_Im)
                # In the case of data point spread larger than the propagated error bars,
                # let's compute the std deviation with respect to weighted averages
                av_err_Re_StdDev = 0
                av_err_Im_StdDev = 0
                for child_index in range(current_gp.childCount()): # (as av_Re and av_Im are required, we need a second loop!)
                    try:
                        child_pc = float(current_gp.child(child_index).text(self.Argand_col['Pc']))
                        child_fc = float(current_gp.child(child_index).text(self.Argand_col['Fc']))
                    except ValueError:
                        child_pc = 0.0
                        child_fc = 0.0
                        QtGui.QMessageBox.warning(self, "ERROR", "Your coherent position or coherent fraction is not computable. Check your yield fit!")
                    av_err_Re_StdDev = av_err_Re_StdDev + (child_fc*np.cos(2*np.pi*child_pc)-av_Re)**2
                    av_err_Im_StdDev = av_err_Im_StdDev + (child_fc*np.sin(2*np.pi*child_pc)-av_Im)**2
                av_err_Re_StdDev = np.sqrt( av_err_Re_StdDev/ (current_gp.childCount()-1))
                av_err_Im_StdDev = np.sqrt( av_err_Im_StdDev/ (current_gp.childCount()-1))

                #Now back to polar coordinates
                av_pc = np.arctan2(av_Im, av_Re) / (2*np.pi)
                if av_pc<0. : av_pc=av_pc+1.
                av_fc = np.sqrt(av_Re**2 + av_Im**2)
                av_err_pc_ErrorPropagation = np.sqrt( (av_Im*av_err_Re       /(2*np.pi*av_fc**2))**2 + (av_Re*av_err_Im       /(2*np.pi*av_fc**2))**2 )
                av_err_pc_StdDev           = np.sqrt( (av_Im*av_err_Re_StdDev/(2*np.pi*av_fc**2))**2 + (av_Re*av_err_Im_StdDev/(2*np.pi*av_fc**2))**2 )
                av_err_fc_ErrorPropagation = np.sqrt( (av_Re*av_err_Re       /av_fc             )**2 + (av_Im*av_err_Im       /av_fc             )**2 )
                av_err_fc_StdDev           = np.sqrt( (av_Re*av_err_Re_StdDev/av_fc             )**2 + (av_Im*av_err_Im_StdDev/av_fc             )**2 )

                #if np.isnan(av_pc) or np.isnan(av_fc) or np.isnan(max(av_err_pc_ErrorPropagation, av_err_pc_StdDev)) or np.isnan(max(av_err_fc_ErrorPropagation, av_err_fc_StdDev))):


                current_gp.setText(self.Argand_col['Pc'], str('%.4f'%av_pc))
                current_gp.setText(self.Argand_col['Fc'], str('%.4f'%av_fc))
                # Choose the largest error bars:
                current_gp.setText(self.Argand_col['Pc_err'], str(max(av_err_pc_ErrorPropagation, av_err_pc_StdDev)))
                current_gp.setText(self.Argand_col['Fc_err'], str(max(av_err_fc_ErrorPropagation, av_err_fc_StdDev)))

        if refresh: self.Argand_replotGroupAverage(current_gp) # replot the group average vector
        self.Argand_QTreeWidgetSignalsSwitch(on=True)


    ## convert a complex (cartesian) value to positon and fraction
    # Makes sure that 0<pc<1
    def Argand_convertComplex2Argand(self, pos_cartesian):
        pc = np.angle(pos_cartesian)/(2*np.pi)
        fc = np.absolute(pos_cartesian)
        while pc > 1.:
            pc = pc - 1.
        while pc < 0.:
            pc = pc + 1.
        return pc, fc

    ## connecting/disconnecting singals sensitive to changings in the TreeWidget
    # it is important that one is able to connect/disconnect this signals easily
    # because if you are e.g. loading a file you do not want Torricelli to react
    # after every line. This increases performance!
    def Argand_QTreeWidgetSignalsSwitch(self, on=-1):
        # if on is not given, switch between on and off
        if on==-1:
            if self.Argand_QTreeWidgetSignalsOn:
                on = False
            else:
                on = True
        elif on == self.Argand_QTreeWidgetSignalsOn:
            return on # already set as wished, nothing to do
        # connecting/disconnecting singals sensitive to changings in the TreeWidget
        if on:
            self.ui.treeWidget_Argand_List.itemDoubleClicked.connect(self.Argand_editColumn)
            self.ui.treeWidget_Argand_List.itemClicked.connect(self.Argand_editColumn)
            self.ui.treeWidget_Argand_List.itemSelectionChanged.connect(self.Argand_selectionChanged)
            self.ui.treeWidget_Argand_List.itemChanged.connect(lambda item, col: self.Argand_updateItems(item_list=[item], col=col, recalcGP=True))
        else:
            self.ui.treeWidget_Argand_List.itemDoubleClicked.disconnect()
            self.ui.treeWidget_Argand_List.itemClicked.disconnect()
            self.ui.treeWidget_Argand_List.itemSelectionChanged.disconnect()
            self.ui.treeWidget_Argand_List.itemChanged.disconnect()
        self.Argand_QTreeWidgetSignalsOn = on
        return on


    def Argand_isDataPoint(self, item):
        return (item.parent() is not self.ui.treeWidget_Argand_List and not self.Argand_isGroup(item))

    ## return True if the selected item is a group
    #  return False if the selected item a dataset
    def Argand_isGroup(self, item):
        return (item.parent() is None)

    ## Return the RGB of selected item
    def Agand_currentColor(self):
        ci = self.ui.treeWidget_Argand_List.currentItem()
        return ci.backgroundColor(self.Argand_col['Color']).getRgb()[0:3] #This return also alpha

    def Argand_selectionChanged(self):
        items = self.ui.treeWidget_Argand_List.selectedItems()
        self.argand.markSelected(map(id,items))

    ## allows to edit the specified column
    def Argand_editColumn(self, item_clicked, col):
        # Only execute if the right mouse button is used
        # set item non editable if column should not be handled via standard editor of QTreeWidget
        if not self.Argand_isGroup(item_clicked):# make sure not to change group item flags (they are always non editable since they are calculated)
            signalsON = self.Argand_QTreeWidgetSignalsSwitch(on=False) #changing flags shall not emit signals
            # Use the standard edit mode of QTreeWidget for other columns that should be editable
            if col in self.editableColumns:
                item_clicked.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable))
                if self.TreeWidgetMouseButtonReleasedEvent == QtCore.Qt.RightButton: # add the right click as a "editTrigger"
                    self.ui.treeWidget_Argand_List.editItem(item_clicked, col)
            elif col not in self.editableColumns:
                item_clicked.setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable))
            self.Argand_QTreeWidgetSignalsSwitch(on=True)

        if self.TreeWidgetMouseButtonReleasedEvent == QtCore.Qt.RightButton or\
           self.TreeWidgetMouseButtonReleasedEvent == QtCore.QEvent.MouseButtonDblClick:
            # A small window pops up to ask for a new name
            if col == self.Argand_col['Name']:
                item_list = self.ui.treeWidget_Argand_List.selectedItems()
                dialog = QDialog_rename()
                dialog.ui.lineEdit_newName.setText(item_list[0].text(self.Argand_col['Name']))
                if dialog.exec_():
                    prefix = dialog.ui.lineEdit_newName.text()
                    if len(item_list) == 1:
                        item_list[0].setText(self.Argand_col['Name'], prefix)
                    else:
                        for i,item in enumerate(item_list):
                            name = prefix + "_{:02d}".format(i)
                            item.setText(self.Argand_col['Name'], name)
                else:
                    return
            # A small window pops up to ask for the symbol to use
            elif col == self.Argand_col['Symbol']:
                dialog = QDialog_symbol()
                if dialog.exec_(): # if OK is clicked
                    if dialog.ui.radioButton_o.isChecked():
                        s = 'o'
                    elif  dialog.ui.radioButton_t.isChecked():
                        s = 't'
                    elif  dialog.ui.radioButton_s.isChecked():
                        s = 's'
                    elif  dialog.ui.radioButton_d.isChecked():
                        s = 'd'
                    elif  dialog.ui.radioButton_plus.isChecked():
                        s = '+'
                    elif  dialog.ui.radioButton_None.isChecked():
                        s = 'n'
                    item_list = self.ui.treeWidget_Argand_List.selectedItems()
                    for item in item_list:
                        item.setText(self.Argand_col['Symbol'], s)
                    self.Argand_updateItems(item_list, recalcGP=False)

                else: # if Cancel is clicked or escape pressed
                    return
            # Ask the user to choose a color if the porper column is clicked.
            elif col == self.Argand_col['Color']:
                color = QtGui.QColorDialog(self).getColor()
                if color.isValid(): # color is invalid if the user aborts choosing a color
                    item_list = self.ui.treeWidget_Argand_List.selectedItems()
                    for item in item_list:
                        item.setBackground(self.Argand_col['Color'], color)
                    self.Argand_updateItems(item_list, recalcGP=False)


    ## Regroups the selected items to group by slices
    def Argand_GpBySlice(self):
        self.Argand_Save(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+self.argand_SaveSubFolder+'autosave_'+self.timestamp()+'_beforeRegroup.csv')
        dialog = QDialog_regroup()
        if dialog.exec_(): # if OK is clicked
            suffix = dialog.ui.lineEdit_GpNameSuffix.text()
            item_list = self.ui.treeWidget_Argand_List.selectedItems()
            item_set_full = set()
            # distinguish between group and element selection
            for item in item_list:
                if self.Argand_isGroup(item):
                    for i in range(item.childCount()):
                        item_set_full.add(item.child(i))
                else:
                    item_set_full.add(item)
            # set of slices
            slices_set = set()
            for item in item_set_full:
                # int(float(x)) for the case that slice_nb is saved as float
                slices_set.add(int(float(item.text(self.Argand_col['Slice nb']))))

            # create groups and at items
            for slice_nb in slices_set:
                color = int(255*slice_nb/len(slices_set))
                gp_dict = {}
                gp_dict.update({'Name':'{:02d}_'.format(slice_nb)+suffix, 'Color':'({:d},{:d},{:d})'.format(color,0,255-color)})
                new_gp = self.Argand_AddGroup(gp_dict, refresh=False)
                for item in item_set_full:
                    if int(float(item.text(self.Argand_col['Slice nb']))) == slice_nb:
                        # for some reason new_gp.addChild(item) is not working
                        # but adding a clone of the child is working!
                        # So I just clone the item and remove it from its previous parent manually
                        item.setBackground(self.Argand_col['Color'],QtGui.QColor(color,0,255-color))
                        new_gp.addChild(item.clone())
            # delete the original items (including groups if groups wre selected, too)
            for item in item_list:
                sip.delete(item)
            self.Argand_refresh_tree_and_plot()

        else:
            pass # The user pressed cancel, do nothing
        # regroup

    ## Draws a polygon around the current item that represent two vectors whose sum equals the current item.
    def Argand_splitVector(self):
        current_item = self.ui.treeWidget_Argand_List.currentItem()
        if self.ui.checkBox_splitVector.isChecked() and current_item != None:
            nA = 0.5
            pc_sum = float(current_item.text(self.Argand_col['Pc']))
            fc_sum = float(current_item.text(self.Argand_col['Fc']))
            # setting initial values for split vectors
            fc_split = 1.0
            # The quotient fc_sum/fc_split has to be between -1..1
            # otherwise the following mathematics will fail
            # it is supposed to be between 0..1 anyway since fractions are positive
            # The fraction of splitted vectors are always greater than f_sum
            if fc_split < fc_sum:
                print "WARNING: Invalid initial value for split vector. fc_split has to be greater than fc_sum"
                print "         This can happen if the vector you are trying to split has a fraction greater than 1"
                print "         If that is the case: Why do you want to split it anyway?"
                print "         However, resetted initial split fraction from 1.0 to yourFc+0.1"
                fc_split = fc_sum + 0.1

            delta_p = np.arccos(fc_sum/fc_split)/(2*np.pi) # magical equation from markus
            pcA = pc_sum - delta_p
            pcB = pc_sum + delta_p
            fcA = fcB = fc_split
            self.argand.addSplitVector(pcA,
                                       fcA,
                                       pc_sum,
                                       fc_sum,
                                       pcB,
                                       fcB,
                                       nA)
            self.ui.doubleSpinBox_Argand_pcA.setValue(pcA)
            self.ui.doubleSpinBox_Argand_fcA.setValue(fcA)
            self.ui.doubleSpinBox_Argand_pcB.setValue(pcB)
            self.ui.doubleSpinBox_Argand_fcB.setValue(fcB)
            self.ui.doubleSpinBox_Argand_nA.setValue(nA)
            self.Argand_Labels(self.ui.checkBox_displayLabels.isChecked())
            # using SignalProxy instead of just connect the signal so the event rate can be limited
            # this is important for the drag event, otherwise every tiny movement would result in
            # recalculating the vector positions and so in non fluent movements
            self.proxy = pg.SignalProxy(self.argand.splitVectorList[-1].node_mouse_moved, rateLimit=60, slot=self.Argand_update_splitVector_position_proxy)
            self.argand.splitVectorList[-1].SigDragFinished.connect(lambda pos: self.Argand_splitMoveFinished(pos))
            #self.argand.splitVectorList[-1].node_mouse_moved.connect(self.Argand_update_splitVector_position)
        elif len(self.argand.splitVectorList) > 0:
            self.argand.splitVectorList[-1].node_mouse_moved.disconnect()
            self.argand.splitVectorList[-1].SigDragFinished.disconnect()
            self.argand.removeAll_SplitVector()
        else:
            pass

    def Argand_splitMoveFinished(self, pos_cartesian_A):
        if self.ui.checkBox_symmetricSplit.isChecked():
            self.Argand_splitVector_symmetricRepositioning(pos_cartesian_A)
        else:
            self.Argand_update_splitVector_position(pos_cartesian_A)

    def Argand_splitVector_symmetricRepositioning_update(self):
        if self.ui.checkBox_symmetricSplit.isChecked():
            # Get current position of Split vector A (cartesian)
            self.Argand_splitVector_symmetricRepositioning(self.argand.splitVectorList[-1].getPosArray()[1])
        else:
            pass

    def Argand_splitVector_symmetricRepositioning(self, pos_cartesian_A):
        if self.ui.checkBox_symmetricSplit.isChecked():
            # split vector A coordinates
            xA, yA = pos_cartesian_A
            # currently marked original vector coordinates
            current_item = self.ui.treeWidget_Argand_List.currentItem()
            pc_sum = float(current_item.text(self.Argand_col['Pc']))
            fc_sum = float(current_item.text(self.Argand_col['Fc']))
            x_sum, y_sum = self.argand.convertPcFc_to_cartesian(pc_sum, fc_sum)
            #pos_cartesian_sum = np.array([x_sum, y_sum])

            # calculation of the new position for symmetric case (using a bit linear algebra)
            m_sum = y_sum/x_sum # gradient of original vector
            m_orth = -1/m_sum   # gradient of orthogonal
            b_orth = y_sum - m_orth*x_sum # ordinate of orthogonal
            b_2 = yA - m_sum*xA # vector through split vector point and orthogonal (called vector 2)
            # intercept point of vector 2 and orthogonal (equals new position of split vector A)
            xA_new, yA_new = np.linalg.solve([[-m_orth, 1], [-m_sum, 1]],[b_orth, b_2]) # [coeffs],[ordinates]

            # reposition split vector A (vector B is updated automatically)
            self.Argand_update_splitVector_position([xA_new, yA_new])
        else:
            pass

    # update the SplitVector in the Argand diagram when the spinBoxes are changed manually by the user (must press enter, or loose focus)
    def Argand_update_SplitVector_plot(self):
        xA, yA = self.argand.convertPcFc_to_cartesian(self.ui.doubleSpinBox_Argand_pcA.value(), self.ui.doubleSpinBox_Argand_fcA.value())
        self.Argand_update_splitVector_position(np.array([xA, yA]))
        self.Argand_update_Split_display(True)

    # since we are using a SignalProxy the arguments are given in a tuple
    # the parameter received by the signal is the first element
    def Argand_update_splitVector_position_proxy(self, event):
        self.Argand_update_splitVector_position(event[0])

    ## Update the node position of the SplitVector polygon in order to get the sum on the current item
    # Get the position of the mouse-moved node in cartesian coordinate list:
    def Argand_update_splitVector_position(self, pos_cartesian_A):

        # Node that should be splitted
        current_item = self.ui.treeWidget_Argand_List.currentItem()
        pc_sum = float(current_item.text(self.Argand_col['Pc']))
        fc_sum = float(current_item.text(self.Argand_col['Fc']))
        x_sum, y_sum = self.argand.convertPcFc_to_cartesian(pc_sum, fc_sum)
        #pos_cartesian_sum = np.array([x_sum, y_sum])

        # Set split vector A
        xA, yA = pos_cartesian_A[0], pos_cartesian_A[1]

        # Node move by the mouse:
        pcA, fcA = self.Argand_convertComplex2Argand(xA+ 1j*yA)
        nA = self.ui.doubleSpinBox_Argand_nA.value()
        self.ui.doubleSpinBox_Argand_nB.setValue(1-nA)

        # transform cartesian coordinates into complex notation
        pos_complex_sum = x_sum + 1j*y_sum
        pos_complex_A   = xA    + 1j*yA

        # calculate split vector B corresponding to vector A
        # -----------------------------------------------
        # nA is the weighting of Vector A (nA + nB = 1)
        # z_sum = nA*zA + nB*zB
        # with z equal to a complex representation of pc and fc
        # z = fc*exp(2*pi*j*pc) in polar coordinates
        # z = fc*cos(2*pi*pc) + j*fc*sin(2*pi*pc)
        #  <=>     z = x_cart + j*y_cart           in argand plane coordinates
        pos_complex_B = (pos_complex_sum - pos_complex_A*nA) / (1-nA)
        pcB, fcB = self.Argand_convertComplex2Argand(pos_complex_B)

        # calculate position B to cartesian coordinates (not neccessary)
        # xB, yB = self.argand.convertPcFc_to_cartesian(pcB, fcB)
        # pos_cartesian_B = np.array([xB, yB])

        # move the nodes
        self.argand.moveNode_i(self.argand.splitVectorList[0], 1, pcA, fcA)
        self.argand.moveNode_i(self.argand.splitVectorList[0], 2, pc_sum, fc_sum) # updates when changing current item
        self.argand.moveNode_i(self.argand.splitVectorList[0], 3, pcB, fcB)
        self.argand.moveNode_i(self.argand.splitVectorList[0], 4, pcA, fcA*nA) # adding two vectors with weighted fraction
        self.argand.moveNode_i(self.argand.splitVectorList[0], 5, pcB, fcB*(1-nA))
        self.ui.doubleSpinBox_Argand_pcA.setValue(pcA)
        self.ui.doubleSpinBox_Argand_fcA.setValue(fcA)
        self.ui.doubleSpinBox_Argand_pcB.setValue(pcB)
        self.ui.doubleSpinBox_Argand_fcB.setValue(fcB)

    ## concetinate doubles
    # not implemented yet
    #def Argand_removeDoubles():
    #    root = self.ui.treeWidget_Argand_List.invisibleRootItem()
    #    for childIndexI in range(root.childCount()):
    #        childI = root.child(childIndexI)
    #        for childIndexJ in range(root.childCount()):
    #            childJ = root.child(childIndexJ)
    #            if childIndexI != childIndexJ \
    #            and childI.text(self.Argand_col['Name']) == childJ.text(self.Argand_col['Name']):
    #                pass

    ## Called after data has been changed
    # all columns are resized, averages recalculated and the Argand diagram refreshed.
    def Argand_refresh_tree_and_plot(self):
        self.Argand_QTreeWidgetSignalsSwitch(on=False)
        for c in range(self.ui.treeWidget_Argand_List.columnCount()):
            self.ui.treeWidget_Argand_List.resizeColumnToContents(c)
        #self.Argand_removeDoubles() #not implemented yet
        self.Argand_groupAverage(refresh=False) # do not refresh because it is followed by replot
        self.Argand_replotDiagram()
        self.Argand_QTreeWidgetSignalsSwitch(on=True)

    ## regarding Argand_Save and Argand_Load
    # -------------------------------------------
    # The loading and saving is robust against changes in the format of the csv file
    # For saving in a csv file the Argand_default_data_dictionary is used for the fieldnames
    # that atuomatically contains all columns of the QTreeWidget. Additionally to that a
    # other columns like e.g. 'Type', 'checkState' are added
    # if no critical information is missing it can be loaded even if columns are missing
    # missing information will are set to '0' as default
    # conversion to load from old format v3.3.273 is implemented

    ## Save the content of the treeWidget to a standard CSV file
    def Argand_Save(self, auto_save=False):
        if auto_save is False:
            newfile_dial = QtGui.QFileDialog()
            newfile_dial.setDefaultSuffix('.csv')
            file_path = newfile_dial.getSaveFileName(self, "Open File", self.ui.LineEdit_CurrentWorkingDirectory.text(), "Torricelli summary file(*.csv)")
        else:
            file_path = auto_save
        if '' != file_path:
            try:
                # Make sure the possibly missing extension is added
                path_without_ext, ext = os.path.splitext(str(file_path))
                file_path = path_without_ext + '.csv'

                if os.path.isfile(file_path): # backup version of the previous file.
                    shutil.move(file_path, file_path+'~')

                with open(file_path, 'w') as csvfile:
                    csvfile.write("# Torricelli ver"+__version__+"\n")
                    fieldnames = ['Type']+['checkState']+self.Argand_ColList+['Path']
                    w = csv.DictWriter(csvfile, delimiter=';', quoting=csv.QUOTE_NONNUMERIC, fieldnames=fieldnames)
                    w.writeheader()
                    root = self.ui.treeWidget_Argand_List.invisibleRootItem()
                    currentDict = {}
                    for i_gp in range(root.childCount()): # Iterate on the groups
                        gp = root.child(i_gp)
                        # clear the dict, fill it with defaults, overwirte defaults with values present in the QTreeWidget
                        currentDict.clear()
                        currentDict.update(self.Argand_default_data_dictionary)
                        currentDict.update({'Type'        : 'Group',\
                                            'checkState'  : 'checked' if gp.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked else 'unchecked',\
                                            'Name'        : str(gp.text(self.Argand_col['Name'])),\
                                            'Pc'          : self.floatOrEmpty(gp.text(self.Argand_col['Pc'])),\
                                            'Pc_err'      : self.floatOrEmpty(gp.text(self.Argand_col['Pc_err'])),\
                                            'Fc'          : self.floatOrEmpty(gp.text(self.Argand_col['Fc'])),\
                                            'Fc_err'      : self.floatOrEmpty(gp.text(self.Argand_col['Fc_err'])),\
                                            'Color'       : gp.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                            'Symbol'      : str(gp.text(self.Argand_col['Symbol'])),\
                                            'Path'        : str(gp.toolTip(self.Argand_col['Name'])),\
                                            'Note'        : str(gp.text(self.Argand_col['Note']))})
                        w.writerow(currentDict)
                        for j_child in range(gp.childCount()): # Iterate in all points in a group
                            point = gp.child(j_child)
                            # clear the dict, fill it with defaults, overwirte defaults with values present in the QTreeWidget
                            currentDict.clear()
                            currentDict.update(self.Argand_default_data_dictionary)
                            currentDict.update({'Type'        : 'Point',\
                                                'checkState'  : 'checked' if point.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked else 'unchecked',\
                                                'Name'        : str(point.text(self.Argand_col['Name'])),\
                                                'Pc'          : self.floatOrEmpty(point.text(self.Argand_col['Pc'])),\
                                                'Pc_err'      : self.floatOrEmpty(point.text(self.Argand_col['Pc_err'])),\
                                                'Fc'          : self.floatOrEmpty(point.text(self.Argand_col['Fc'])),\
                                                'Fc_err'      : self.floatOrEmpty(point.text(self.Argand_col['Fc_err'])),\
                                                'Sr'          : self.floatOrEmpty(point.text(self.Argand_col['Sr'])),\
                                                'Sr_err'      : self.floatOrEmpty(point.text(self.Argand_col['Sr_err'])),\
                                                '|Si|'        : self.floatOrEmpty(point.text(self.Argand_col['|Si|'])),\
                                                'Psi'         : self.floatOrEmpty(point.text(self.Argand_col['Psi'])),\
                                                'Q_0'         : self.floatOrEmpty(point.text(self.Argand_col['Q_0'])),\
                                                'Q_H'         : self.floatOrEmpty(point.text(self.Argand_col['Q_H'])),\
                                                'Gamma'       : self.floatOrEmpty(point.text(self.Argand_col['Gamma'])),\
                                                'Gamma_err'   : self.floatOrEmpty(point.text(self.Argand_col['Gamma_err'])),\
                                                'Delta'       : self.floatOrEmpty(point.text(self.Argand_col['Delta'])),\
                                                'Phi'         : self.floatOrEmpty(point.text(self.Argand_col['Phi'])),\
                                                'P el'        : self.floatOrEmpty(point.text(self.Argand_col['P el'])),\
                                                'Zeta'        : self.floatOrEmpty(point.text(self.Argand_col['Zeta'])),\
                                                'b sample'    : self.floatOrEmpty(point.text(self.Argand_col['b sample'])),\
                                                'b DCM'       : self.floatOrEmpty(point.text(self.Argand_col['b DCM'])),\
                                                'Xi'          : self.floatOrEmpty(point.text(self.Argand_col['Xi'])),\
                                                'Pol.'        : str(point.text(self.Argand_col['Pol.'])),\
                                                'Temp.'       : self.floatOrEmpty(point.text(self.Argand_col['Temp.'])),\
                                                'P Refl'      : self.floatOrEmpty(point.text(self.Argand_col['P Refl'])),\
                                                'R2 Refl'     : self.floatOrEmpty(point.text(self.Argand_col['R2 Refl'])),\
                                                'X2 Yield'    : self.floatOrEmpty(point.text(self.Argand_col['X2 Yield'])),\
                                                'Component'   : str(point.text(self.Argand_col['Component'])),\
                                                'Slice nb'    : self.intOrEmpty(point.text(self.Argand_col['Slice nb'])),\
                                                'Sigma'       : self.floatOrEmpty(point.text(self.Argand_col['Sigma'])),\
                                                'delta hnu'   : self.floatOrEmpty(point.text(self.Argand_col['delta hnu'])),\
                                                'Color'       : point.backgroundColor(self.Argand_col['Color']).getRgb()[0:3],\
                                                'Symbol'      : str(point.text(self.Argand_col['Symbol'])),\
                                                'Core level'  : str(point.text(self.Argand_col['Core level'])),\
                                                'Monte Carlo analysis'      : str(point.text(self.Argand_col['Monte Carlo analysis'])),\
                                                'Substrate'   : str(point.text(self.Argand_col['Substrate'])),\
                                                'DW'          : str(point.text(self.Argand_col['DW'])),\
                                                '(hkl)'       : str(point.text(self.Argand_col['(hkl)'])),\
                                                'Path'        : str(point.toolTip(self.Argand_col['Name'])),\
                                                'Yield file'  : str(point.text(self.Argand_col['Yield file'])),\
                                                'Note'        : str(point.text(self.Argand_col['Note']))})
                            w.writerow(currentDict)

            except csv.Error as e:
                sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

    def floatOrEmpty(self, text):
        if text=='' or 'None'==text:
            return ''
        elif text=='-':
            return '-'
        else:
            return float(text)

    def intOrEmpty(self, text):
        return '' if text=='' else int(float(text))

    ## Loads a standard CSV file into the treeWidget
    def Argand_Load(self):
        # beautiful waiting cursor while loading (has to be followed by restoreOverrideCursor() at some point)
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        # loading from a file involves a lot of adding and changing of items
        # disconnect signals sensitive to these changes while loading a file
        signalsON = self.Argand_QTreeWidgetSignalsSwitch(on=False)
        self.ui.statusbar.showMessage("LOADING & PLOTTING - in progress")
        # show a ProgressBar in statusbar while loading the file
        progressLabel = QtGui.QLabel()
        progressBarLOADING = QtGui.QProgressBar()
        progressLabel.setText(" LOADING  -  file: ")
        self.ui.statusbar.addPermanentWidget(progressLabel)
        self.ui.statusbar.addPermanentWidget(progressBarLOADING)

        file_path = QtGui.QFileDialog.getOpenFileName(self, "Open File", self.ui.LineEdit_CurrentWorkingDirectory.text(), "Torricelli summary file(*.csv);; All (*)")
        if '' != file_path:
            try:
                total_lines = len(open(file_path).readlines()) # it really just takes <1s for ~10^6 lines
                with open(file_path, 'r') as csvfile:
                    version = filter(lambda c: c.isdigit() or c=='.', csvfile.readline()) # Ignore the first line (contains Torricelli version)
                    csvOutdated = StrictVersion(version) < StrictVersion('3.3.273') # is True if the csv is from an old Torricelli Version
                    if csvOutdated:
                        self.ui.statusbar.showMessage('The csv file you are loading is outdated! (From Torricelli v3.3.272 or earlier',10000)
                        QtGui.QMessageBox.warning(self, "Warning", '<b>The csv file you want to load is outdated!</b><br>'\
                                                                  +'It seems to be from Torricelli v3.3.272 or earlier. '\
                                                                  +'I should be able to load it anyway but please check if everything is correct. '\
                                                                  +'Columns that were non-existant in the older Torricelli version remain empty.<br><br>'\
                                                                  +'To be on the safe side and to avoid this message '
                                                                  +'resave your data table in this Torricelli version.')
                    reader = csv.DictReader(csvfile, delimiter=';', quoting=csv.QUOTE_NONNUMERIC) # keys are taken from first row
                    for i,row in enumerate(reader):
                        # progressBar for long files
                        # remember i starts with 0 and and one comment and one header line is skipped
                        # so you need i+3 for the progressBar
                        progressBarLOADING.setValue(float(i+3)/total_lines*100)

                        if 'Group' == row['Type']:
                            dic_group = self.Argand_default_group_dictionary.copy()
                            dic_group.update(row)
                            if csvOutdated:
                                dic_group.update({'Name':dic_group.pop('Group Name','NewGroup')})
                            gp = self.Argand_AddGroup(dic_group, refresh=False)
                        elif 'Point' == row['Type']:
                            dic_point = self.Argand_default_data_dictionary.copy()
                            dic_point.update(row)
                            if csvOutdated:
                                dic_point.update({'Name':dic_point.get('Path','NewPoint')})
                            self.Argand_AddDataset(gp, dic_point, refresh=False)
                        else:
                            print 'Your .csv has content problems!'
                            return
                    self.ui.statusbar.removeWidget(progressLabel)
                    self.ui.statusbar.removeWidget(progressBarLOADING)
                    self.Argand_refresh_tree_and_plot()

            except csv.Error as e:
                sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

        # connect the signals again
        self.Argand_QTreeWidgetSignalsSwitch(on=True)
        # restore to system default cursor
        QtGui.QApplication.restoreOverrideCursor()

    # toggles if sorting is enabled or disabled
    def Argand_sortOnOff(self):
        if self.ui.checkBox_SortOnOff.isChecked():
            #self.ui.treeWidget_Argand_List.isSortingEnabled():
            self.ui.treeWidget_Argand_List.setSortingEnabled(True)
            self.ui.treeWidget_Argand_List.sortItems(self.Argand_col['Name'], QtCore.Qt.AscendingOrder)
        else:
            self.ui.treeWidget_Argand_List.setSortingEnabled(False)


    ## Function called by the user once she/he is happy with the fit result and want to keep the value.
    def Argand_saveFitResult_and_plot(self):
        path, lastFold = os.path.split(str(self.ui.LineEdit_CurrentWorkingDirectory.text()))
        path, lastButOneFold = os.path.split(path)
        gp_name = lastButOneFold + '/' + lastFold + '_' + str(self.ui.column_name_label.text())

        # check if the group corresponding to this folder already exists, otherwise creates it
        root = self.ui.treeWidget_Argand_List.invisibleRootItem()
        gp_already_exists = False
        for i_gp in range(root.childCount()): # Iterate on the groups
            gp = root.child(i_gp)
            if str(gp.text(self.Argand_col['Name'])) == gp_name:
                gp_already_exists = True
                gp_liveAn = gp
        if not gp_already_exists:
            gp_liveAn = self.Argand_AddGroup({'Name':gp_name})

        self.Argand_AddDataset(gp_liveAn, self.get_dict_with_all_values(), refresh=True)
        self.Argand_Save(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+self.argand_SaveSubFolder+'autosave_'+self.timestamp()+'_newFitResultAdded.csv')

    # return a dictionay that contains all informations/parameters that can be saved. This also contains the fit results!
    def get_dict_with_all_values(self):
        dic = self.Argand_default_data_dictionary.copy()
        name_str = str(self.ui.LineEdit_CurrentWorkingDirectory.text()).split(os.sep)[-1]
        if "sum" in name_str or "Slice" in name_str:
            # to avoid a discussion with francois what is the correct working directory
            name_str = str(self.ui.LineEdit_CurrentWorkingDirectory.text()).split(os.sep)[-2]

        dic.update({'Name'      : name_str,\
                    'Fc'        : self.ui.doubleSpinBox_EYFit_fc.value() if self.ui.doubleSpinBox_EYFit_fc.isEnabled() else self.ui.doubleSpinBox_fc.value(),\
                    'Pc'        : self.get_final_Pc(),\
                    'Gamma'     : self.get_final_gamma(),\
                    'Gamma_err' : self.get_final_gamma_err(),\
                    'Delta'     : self.ui.doubleSpinBox_EYinit_Delta.value() if self.ui.radioButton_DQ_approx.isChecked() else '-',\
                    'Fc_err'    : self.ui.doubleSpinBox_stddev_ey_fc.value() if self.ui.doubleSpinBox_stddev_ey_fc.isEnabled() else '-',\
                    'Pc_err'    : self.ui.doubleSpinBox_stddev_ey_pc.value() if self.ui.doubleSpinBox_stddev_ey_pc.isEnabled() else '-',\
                    'Sr'        : self.get_final_Sr(),\
                    'Sr_err'    : self.ui.doubleSpinBox_stddev_Sr.value()    if self.ui.doubleSpinBox_stddev_Sr.isEnabled()    else '-',\
                    '|Si|'      : self.get_final_Si(),\
                    'Psi'       : self.get_final_Psi(),\
                    'Q_0'       : self.get_final_Q0() ,\
                    'Q_H'       : self.get_final_QH() ,\
                    'Component' : str(self.ui.column_name_label.text()),\
                    'Slice nb'  : int(self.ui.spinBox_SelectedSlice.value()),\
                    'Sigma'     : self.ui.doubleSpinBox_ReflFit_sigma.value(),\
                    'delta hnu' : self.ui.doubleSpinBox_ReflFit_de.value(),\
                    'Path'      : str(self.ui.LineEdit_CurrentWorkingDirectory.text()),\
                    'Symbol'    : 's',\
                    'Core level': str(self.ui.comboBox_NonDipolar_Element.currentText()).strip()+self.ui.comboBox_NonDipolar_Shells.currentText(),\
                    'Phi'       : self.ui.doubleSpinBox_ndp_phi.value(),\
                    'P el'      : self.ui.doubleSpinBox_EYinit_Pe.value(),\
                    'Zeta'      : self.ui.doubleSpinBox_sample_miscut.value(),\
                    'b sample'  : self.ui.doubleSpinBox_b_cr.value(),\
                    'b DCM'     : self.ui.doubleSpinBox_b_mo.value(),\
                    'Xi'        : self.ui.doubleSpinBox_sample_deviation_NI.value(),\
                    'Pol.'      : 'Pi' if self.ui.radioButton_pi_pol_light.isChecked() else 'Sigma',\
                    'P Refl'    : self.ui.doubleSpinBox_sample_P_Refl.value(),\
                    'R2 Refl'   : self.ui.doubleSpinBox_ReflFit_RSquared.value(),\
                    'X2 Yield'  : self.ui.doubleSpinBox_FitEY_RedChiSquare.value(),\
                    'Monte Carlo analysis' : self.get_final_MCA(),\
                    'Substrate' : str(self.ui.comboBox_Sample_Elemental_Element.currentText())    if self.ui.radioButton_Sample_Elemental.isChecked() else str(self.ui.comboBox_Sample_Compound_Element.currentText()),\
                    'DW'        : str(self.ui.comboBox_Sample_Elemental_DWMethod.currentText())   if self.ui.radioButton_Sample_Elemental.isChecked() else str(self.ui.comboBox_Sample_Compound_DWMethod.currentText()),\
                    'Temp.'     : self.ui.doubleSpinBox_Sample_Elemental_Temperature.value() if self.ui.radioButton_Sample_Elemental.isChecked() else self.ui.doubleSpinBox_Sample_Compound_Temperature.value(),\
                    '(hkl)'     : str(self.ui.spinBox_Sample_Elemental_h.value())+str(self.ui.spinBox_Sample_Elemental_k.value())+str(self.ui.spinBox_Sample_Elemental_l.value()) if self.ui.radioButton_Sample_Elemental.isChecked() else str(self.ui.spinBox_Sample_Compound_h.value())+str(self.ui.spinBox_Sample_Compound_k.value())+str(self.ui.spinBox_Sample_Compound_l.value()),\
                    'Yield file': str(self.ui.ey_name.text())})
        return dic


    def get_final_Psi(self):
        if not self.ui.radioButton_EYinit_man_SR.isChecked():
            if self.ui.checkBox_eyfit_fitgamma.isChecked(): return self.ui.doubleSpinBox_EYinit_Psi_fitResult.value()
            else: return self.ui.doubleSpinBox_EYinit_Psi.value()
        else: return '-'
    def get_final_MCA(self):
        if self.ui.checkBox_ignore_MonteCarlo.isChecked(): return 'Without'
        else: return 'With MC'
    def get_final_Q0(self):
        if not self.ui.radioButton_EYinit_man_SR.isChecked():
            if self.ui.checkBox_eyfit_fitgamma.isChecked(): return self.ui.doubleSpinBox_EYinit_Q0_fitResult.value()
            else: return self.ui.doubleSpinBox_EYinit_Q0.value()
        else: return '-'
    def get_final_QH(self):
        if not self.ui.radioButton_EYinit_man_SR.isChecked():
            if self.ui.checkBox_eyfit_fitgamma.isChecked(): return self.ui.doubleSpinBox_EYinit_QH_fitResult.value()
            else: return self.ui.doubleSpinBox_EYinit_QH.value()
        else: return '-'


    def get_final_Pc(self):
        if self.ui.doubleSpinBox_EYFit_fc.value()>1e-4:
            if self.ui.doubleSpinBox_EYFit_pc.isEnabled(): return self.ui.doubleSpinBox_EYFit_pc.value()
            else:  return self.ui.doubleSpinBox_pc.value()
        else: return '-'

    def get_final_Si(self): # Function necessary to self.Argand_saveFitResult_and_plot()
        if self.ui.doubleSpinBox_EYFit_fc.value()>1e-4:
            if self.ui.doubleSpinBox_EYinit_abs_si_fitResult.isEnabled(): return self.ui.doubleSpinBox_EYinit_abs_si_fitResult.value()
            else: return self.ui.doubleSpinBox_EYinit_abs_si.value()
        else:
            return '-'

    def get_final_Psi(self): # Function necessary to self.Argand_saveFitResult_and_plot()
        if self.ui.doubleSpinBox_EYFit_fc.value()>1e-4:
            if not self.ui.radioButton_EYinit_man_SR.isChecked():
                if self.ui.doubleSpinBox_EYinit_Psi_fitResult.isEnabled(): return self.ui.doubleSpinBox_EYinit_Psi_fitResult.value()
                else: return self.ui.doubleSpinBox_EYinit_Psi.value()
            else: return '-'
        else:
            return '-'

    def get_final_Q0(self): # Function necessary to self.Argand_saveFitResult_and_plot()
        if self.ui.doubleSpinBox_EYFit_fc.value()>1e-4:
            if self.ui.doubleSpinBox_EYinit_Q0_fitResult.isEnabled(): return self.ui.doubleSpinBox_EYinit_Q0_fitResult.value()
            else: return self.ui.doubleSpinBox_EYinit_Q0.value()
        else:
            return '-'

    def get_final_QH(self): # Function necessary to self.Argand_saveFitResult_and_plot()
        if self.ui.doubleSpinBox_EYFit_fc.value()>1e-4:
            if self.ui.doubleSpinBox_EYinit_QH_fitResult.isEnabled(): return self.ui.doubleSpinBox_EYinit_QH_fitResult.value()
            else: return self.ui.doubleSpinBox_EYinit_QH.value()
        else:
            return '-'

    def get_final_gamma(self): # Function necessary to self.Argand_saveFitResult_and_plot()
        if self.ui.radioButton_EYinit_man_SR.isChecked(): return '-'
        else:
            if self.ui.checkBox_eyfit_fitgamma.isChecked(): return self.ui.doubleSpinBox_EYFit_gamma.value()
            else: return self.get_init_value_gamma()

    def get_final_gamma_err(self): # Function necessary to self.Argand_saveFitResult_and_plot()
        if not self.ui.radioButton_EYinit_man_SR.isChecked() and self.ui.checkBox_eyfit_fitgamma.isChecked(): return self.ui.doubleSpinBox_stddev_gamma.value()
        else: return '-'

    def get_final_Sr(self): # Function necessary to self.Argand_saveFitResult_and_plot()
        if self.ui.radioButton_EYinit_man_SR.isChecked():
            if self.ui.checkBox_eyfit_fitSr.isChecked():
                return self.ui.doubleSpinBox_EYFit_Sr.value()
            else:
                return self.ui.doubleSpinBox_EYinit_man_SR.value()
        else: # working with gamma
            if self.ui.checkBox_eyfit_fitgamma.isChecked():
                return self.ui.doubleSpinBox_EYinit_theo_SR_fitResult.value()
            else:
                return self.ui.doubleSpinBox_EYinit_theo_SR.value()



    def Argand_Labels(self, checked):
        # Split vector labels
        for vec in self.argand.splitVectorList:
            if checked:
                splitvec_label = ['','<big>F<sub>A</sub></big>','','<big>F<sub>B</sub></big>','n<sub>A</sub>&middot;F<sub>A</sub>','n<sub>B</sub>&middot;F<sub>B</sub>']
            else:
                splitvec_label = ['','','','','','']
            vec.setTexts(splitvec_label)

        # average vector labels
        if self.ui.checkBox_Argand_display_originVectors.isChecked():
            root = self.ui.treeWidget_Argand_List.invisibleRootItem()
            child_count = root.childCount()

            for i in range(child_count):
                gp = root.child(i)
                if gp.checkState(self.Argand_col['Name']) == QtCore.Qt.Checked:

                    vec = self.argand.originVectorDict[id(gp)]

                    if checked:
                        originvec_label = ['', '<big>'+str(gp.text(self.Argand_col['Name']))+'</big>']
                    else:
                        originvec_label = ['','']

                    vec.setTexts(originvec_label)

    def Argand_update_Split_display(self, state):
        self.ui.label_23.setEnabled(state)
        self.ui.label_24.setEnabled(state)
        self.ui.label_26.setEnabled(state)
        self.ui.label_28.setEnabled(state)
        self.ui.label_25.setEnabled(state)
        self.ui.doubleSpinBox_Argand_pcA.setEnabled(state)
        self.ui.doubleSpinBox_Argand_pcB.setEnabled(state)
        self.ui.doubleSpinBox_Argand_fcA.setEnabled(state)
        self.ui.doubleSpinBox_Argand_fcB.setEnabled(state)
        self.ui.doubleSpinBox_Argand_nA.setEnabled(state)
        self.ui.doubleSpinBox_Argand_nB.setEnabled(state)
        if self.ui.doubleSpinBox_Argand_nA.value() == 0.5:
            self.ui.checkBox_symmetricSplit.setEnabled(state)
        else:
            self.ui.checkBox_symmetricSplit.setChecked(False)
            self.ui.checkBox_symmetricSplit.setEnabled(False)

    def Argand_updateFcPcGrid(self, *args):
        self.argand.changeAxisAndGrid(polarGridNr = self.ui.spinBox_Fc_grid_lines.value(), radialGridNr = self.ui.spinBox_Pc_grid_lines.value())
        #self.Argand_replotDiagram()


    def ArgandList_editable(self):
        if self.ui.checkBox_ArgandList_editable.isChecked():
            self.editableColumns = map(self.Argand_col.get, self.editableColList)
        else:
            self.editableColumns = map(self.Argand_col.get, self.noteditableColList)

    ###########################################################################
    ### --------------- General methods concerning the GUI ---------------  ###
    ###########################################################################

    ## Tooltips allows to display information to the user that is object-specific.
    #  They are all listed here
    def set_all_ToolTips(self): #self.ui..setToolTip('')
        xi    = u"\u03BE"
        theta = u"\u03B8"
        zeta  = u"\u03B6"
        deg   = u"\u00B0"
        phi   = u"\u03C6"
        chi   = u"\u03C7"
        sigma = u"\u03C3"
        delta = u"\u03B4"
        nu    = u"\u03BD"

        ### Theoretical reflectivity and phase
        find_Geometry = "\n\n\t--> All angles are defined in a drawing in the tab \'Geometry\' <--"
        self.ui.label_52.setToolTip('Double Crystal Monochromator')
        self.ui.doubleSpinBox_sample_P_Refl.setToolTip('Polarization factor for the x-ray')
        self.ui.doubleSpinBox_sample_miscut.setToolTip('Miscut.\nShould be close to 0'+deg+find_Geometry)
        self.ui.doubleSpinBox_sample_deviation_NI.setToolTip('Deviation from normal incidence.\nPositive values mean that the sample normal points towards the analyzer.\nShould be close to 0'+deg+find_Geometry)
        self.ui.doubleSpinBox_theta.setToolTip('Angle between the incoming beam and the atomic plane\n'+theta+' = 90-'+xi+find_Geometry)
        self.ui.doubleSpinBox_b_cr.setToolTip('Asymmetry parameter')
        self.ui.doubleSpinBox_theoReflRange.setToolTip('Here you can set the photon energy range for calculating the theoretical reflectivity.\nThis range must be wider than your experimental reflectivity otherwise the\nfitting of the reflectivity will fail because interpolation of your experimental\ndata will exceed the range of available datapoints!\n\n\tRecommended value: 8 eV')
        self.ui.radioButton_sigma_pol_light.setToolTip('Electric field perpendicular to the plane of incidence')
        self.ui.radioButton_pi_pol_light.setToolTip('Electric field in the plane of incidence')
        toolTip_checkedValues = 'Yes: the crystallographic values were confirmed by an XSW experiment.\nNo: Values compiled from the litterature, but not verified in an XSW experiment.'
        self.ui.label_DCM_CheckedValue.setToolTip(toolTip_checkedValues)
        self.ui.label_CheckedValue.setToolTip(toolTip_checkedValues)
        self.ui.label_Elemental_CheckedValue.setToolTip(toolTip_checkedValues)
        self.ui.label_Compound_CheckedValue.setToolTip(toolTip_checkedValues)

        ### Import experimental data
        self.ui.spinBox_SelectedSlice.setToolTip('Slice number. The 0th slice corresponds to the smallest phi value.'+find_Geometry)
        phi_toolTip = phi+'^e_j is the angle between the incoming x-ray beam\nand the center of the slice under consideration.'+find_Geometry
        self.ui.label_sliceAngle.setToolTip(phi_toolTip)
        self.ui.label_AngleOfSlice.setToolTip(phi_toolTip)
        set_S = 'Set of XPS components to be added and analyzed together\n0 is default\nTo sum several components, list them separated by a space: e.g. \"1 3 4\"'
        self.ui.signal_name.setToolTip(set_S)
        self.ui.label_signal.setToolTip(set_S)
        self.ui.checkBox_AngularModeToggle.setToolTip('Use this if you concatenated several XSW data sets in a\nsingle casaXPS file (e.g. for fitting many slices at once)'+find_Geometry)
        sliceAngle_toolTip = "File that consists of a list of angles that corresponds to the slices.\nYou can write this file manually or use the file created by the DataBrowser"
        self.ui.label_angles.setToolTip(sliceAngle_toolTip)
        self.ui.lineEdit_angles_path.setToolTip(sliceAngle_toolTip)
        self.ui.button_angles_file.setToolTip(sliceAngle_toolTip)
        self.ui.button_display_angles.setToolTip(sliceAngle_toolTip)
        self.ui.checkBox_ignore_MonteCarlo.setToolTip('Allows the user to ignore the statistical errors.\n(Note however that the statistical errors columns must still be present in the yield file, even they are only filled with zeros)\nTo be used ONLY for fast analysis during a beam-time!')
        self.ui.checkBox_ignore_hvCheck.setToolTip('Check this if the photon energies are wrongly defined in the yield file.')
        self.ui.label_angles_file_info.setToolTip('Information stored in the 2nd and 3rd header line of the angle file')

        ### Fit reflectivity
        R2 = 'Coefficient of determination is a number that indicates how well data fit a statistic model.\nRanges from 0 (bad fit) to 1 (good fit).'
        r_chi2 = 'Pearson Chi square'
        y_chi2 = 'Reduced Chi square ('+chi+'_red):\n'+chi+'_red >> 1: Poor fit.\n'+chi+'_red > 1: The fit has not fully captured the data or the the error variance has been underestimated.\n'+chi+'_red = 1: Good fit\n'+chi+'_red < 1: the model is over-fitting the data: either the model is improperly fitting noise, or the error variance has been overestimated.'
        self.ui.label_refl_RSquared.setToolTip(R2)
        self.ui.doubleSpinBox_ReflFit_RSquared.setToolTip(R2)
        self.ui.label_22.setToolTip(R2)
        self.ui.label_refl_chi.setToolTip(r_chi2)
        self.ui.label_2.setToolTip(r_chi2)
        self.ui.doubleSpinBox_ReflFit_RedChiSquare.setToolTip(r_chi2)

        ### Fit Yield
        self.ui.checkBox_display_manual_EY.setToolTip('Displays properly only after having fitted once')
        phi_ndp_tooltip = "Angle between the incoming x-ray beam\nand the center of the slice under consideration.\nYou have to load an angles file in the import tab that connects slice numbers to angles, or type here manually the phi values."
        self.ui.label_theta_p_2.setToolTip(phi_ndp_tooltip)
        self.ui.doubleSpinBox_ndp_phi.setToolTip(phi_ndp_tooltip)
        fit_Sr_or_gamma = 'Fit SR or gamma only in the case of intendely disordered system,\nthat is with Fc fixed to 0.'
        self.ui.label_sr.setToolTip(fit_Sr_or_gamma)
        self.ui.label_gamma.setToolTip(fit_Sr_or_gamma)
        self.ui.checkBox_eyfit_fitSr.setToolTip(fit_Sr_or_gamma)
        self.ui.checkBox_eyfit_fitgamma.setToolTip(fit_Sr_or_gamma)
        self.ui.label_ey_RSquared.setToolTip(R2)
        self.ui.label_15.setToolTip(R2)
        self.ui.doubleSpinBox_eyFit_RSquared.setToolTip(R2)
        self.ui.label_fit_ey_chi.setToolTip(y_chi2)
        self.ui.label_16.setToolTip(y_chi2)
        self.ui.doubleSpinBox_FitEY_RedChiSquare.setToolTip(y_chi2)
        self.ui.label_initialChiSquared.setToolTip(y_chi2)
        self.ui.label_9.setToolTip(y_chi2)
        self.ui.doubleSpinBox_manual_chisq.setToolTip(y_chi2)
        self.ui.comboBox_NonDipolar_Shells.setToolTip('Non-dipolar parameter theory valid for s-subshells only!')
        self.ui.label_20.setToolTip('Non-dipolar parameter theory valid for s-subshells only!')
        m = 'Please check that all values do correspond to the reference:\nTrzhaskovskaya et al. Photoelectron angular distribution parameter for elements Z = 1 TO Z = 54'
        self.ui.label_3.setToolTip(m)
        self.ui.comboBox_NonDipolar_Element.setToolTip(m)
        self.ui.label_21.setToolTip(m)
        self.ui.spinBox_NonDipolar_Element_Z.setToolTip(m)
        self.ui.textEdit_gamma.setToolTip(m)
        self.ui.pushButton_exportGammaFile.setToolTip(m)
        self.ui.label_35.setToolTip(m)

        ### Argand diagram
        self.ui.checkBox_splitVector.setToolTip('Decompose the currenlty selected point into two vector A and B.')
        self.ui.checkBox_symmetricSplit.setToolTip('Force the fraction of A and B to be the same')
        tooltip_refresh = "After changing the grid, you have to press the Refresh button."
        self.ui.spinBox_Pc_grid_lines.setToolTip(tooltip_refresh)
        self.ui.spinBox_Fc_grid_lines.setToolTip(tooltip_refresh)
        self.ui.label_12.setToolTip(tooltip_refresh)
        self.ui.label_11.setToolTip(tooltip_refresh)



    ## Prepares the main window, and initialises the variables
    # launched only once by __init__
    def PrepareGUI_InitVariables(self):
        self.setWindowTitle('Torricelli __ The friendly X-Ray Standing Wave data analysis software __ ver'+__version__)
        self.setWindowIcon(QtGui.QIcon('imports/Torricelli_icon.png'))
        self.set_all_ToolTips()
        self.ui.splitter.setSizes([640,600])
        self.ndp_choose_work_with_SR_or_gamma()


        #self.ui.checkBox_offNormal_correction.setToolTip("Usually one does not have exact normal incidence in NIXSW since one has to measure the intensity of the reflected beam.\n"\
        #                    +"Therefore the angle between incident and reflected beam is not zero. Realistic values are between 0\xb0 and 5\xb0.\n"\
        #                    +"This polar angle offset from 0\xb0 (normal incidence condition) can have a not negligible effect on the calculation of the non dipolar parameters!\n"\
        #                    +"Attention: The correction still assumes that the incident beam makes an angle of exactly 90\xb0 with the optical axis of the detector.\n"\
        #                    +"The user can choose to take this into account by checking <off-normal correction> and giving the angle between incident and reflected beam in deg.\n"\
        #                    +"Positive values for this angle mean a polar correction towards the analyzer.\n"\
        #                    +"Since the Q parameter makes no sense anymore using this correction it is disabled when <off-normal correction> is checked.")

        self.ui.label_fit_ey_chi.setPixmap(QtGui.QPixmap(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'chi_red2.png'))
        #self.ui.label_refl_chi.setScaledContents(False)
        self.ui.label_refl_chi.setPixmap(QtGui.QPixmap(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'chi_2_Pearson.png'))
        self.ui.label_initialChiSquared.setPixmap(QtGui.QPixmap(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'chi_red2.png'))

        self.fit_results_plot_note = ''
        # theoretical arrays
        self.Theory_photonEnergy        = np.array([])
        self.Theory_Refl_sample         = np.array([])
        self.Theory_Phase_Sample        = np.array([])
        self.Theory_Refl_Monochromator  = np.array([])
        self.Theory_Phase_Monochromator = np.array([])
        self.Theory_Squared_Refl_Monochromator_norm               = np.array([])
        self.Theory_ReflSample_cc_ReflMono2 = np.array([])
        #self.Theory_Refl_Sample_Correlated_Monochromator_squared  = np.array([])
        #self.Theory_Phase_Sample_Convoluted_Sqrt_Monochromator = np.array([])
        # experimental arrays
        self.Exp_photonEnergy               = np.array([])
        self.Exp_photonEnergy_BraggCentered = np.array([])
        self.Exp_Refl_Normalised            = np.array([])
        self.Exp_Refl_Estimated_Error       = np.array([])
        self.Exp_EY_Normalised              = np.array([])
        self.Exp_EY_casaXPS_Error           = np.array([])

        ### section: Fit reflectivity ###
        self.R_squared_refl = 0

        ### section: Fit yield ###
        # loads the database ini file with all the gamma values elements up to Z=54
        self.look_for_gamma_file()
        self.E_b = 0
        self.nb_slices = 0
        self.Components_List_Used_in_EYfit  = np.array([0]) # default value (compelled by the np.fromstring function)
        self.R_squared_ey = 0
        self.Theo_Sample_EY_cc_Gauss_cc_RMono2 = np.array([])

        ### Argand TreeWidget ###
        # dict of the treeWidget column content and corresponding numbers ('path' is saved in the toolTip())
        self.Argand_ColList = [ 'Name',
                                'Symbol',
                                'Color',
                                'Component',
                                'Slice nb',
                                'Phi',
                                'Pc',
                                'Fc',
                                'Pc_err',
                                'Fc_err',
                                'Core level',
                                'Gamma',
                                'Gamma_err',
                                'Q_0',
                                'Q_H',
                                'Delta',
                                'P el',
                                'Sr',
                                'Sr_err',
                                '|Si|',
                                'Psi',#u'\u03A8'
                                'Zeta',
                                'b sample',
                                'b DCM',
                                'Xi',
                                'Pol.',
                                'P Refl',
                                'Substrate',
                                '(hkl)',
                                'DW',
                                'Temp.',
                                'delta hnu',
                                'Sigma',
                                'R2 Refl',
                                'X2 Yield',
                                'Monte Carlo analysis',
                                'Yield file',
                                'Note']
        self.Argand_col = dict(zip(self.Argand_ColList,range(len(self.Argand_ColList))))
        # Set the header ot the TreeWidget according to Argand_ColList
        self.ui.treeWidget_Argand_List.setHeaderLabels(QtCore.QStringList(self.Argand_ColList))
        self.ui.treeWidget_Argand_List.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | QtGui.QAbstractItemView.EditKeyPressed) # sets the events to enter into the edit mode
        self.editableColList = ['Component', 'Core level', 'Phi', 'Element','Subshell','Components','Slice nb','Phi','Pc','Fc','Pc_err','Fc_err','Gamma','Gamma_err','Q_0','Q_H','Delta','P el','Sr','Sr_err','|Si|','Psi','Zeta','b sample','b DCM','Xi','Pol.','P Refl','Substrate','(hkl)','DW','Temp.','delta hnu','Sigma','R2 Refl','X2 Yield','Monte Carlo analysis','Note']
        self.noteditableColList = ['Note']
        self.editableColumns = map(self.Argand_col.get, self.noteditableColList)
        self.argand_SaveSubFolder = ''
        # Default dict containing data use to fill data points in a group
        self.Argand_default_data_dictionary  = dict.fromkeys(self.Argand_ColList,'')
        self.Argand_default_group_dictionary = dict.fromkeys(self.Argand_ColList,'')
        self.groupsChangedViaDrag = set()
        self.Argand_QTreeWidgetSignalsOn = False
        # set some defaults
        self.Argand_default_data_dictionary.update({'Name'      : 'NewDataPoint',\
                                                    'Symbol'    : 'o',\
                                                    'Color'     : QtGui.QColor(0,0,0),\
                                                    'Path'      : ''})
        # set some defaults
        self.Argand_default_group_dictionary.update({'Name'      : 'NewGroup',\
                                                     'Symbol'    : '+',\
                                                     'Color'     : QtGui.QColor(0,0,0)})
        self.ui.treeWidget_Argand_List.sortItems(self.Argand_col['Name'], QtCore.Qt.AscendingOrder)
        # style settings
        self.ui.treeWidget_Argand_List.setTextElideMode(QtCore.Qt.ElideMiddle)

        self.TreeWidgetMouseButtonReleasedEvent = None
        # Argand Diagram
        self.argand = ArgandPlotWidget()
        self.ui.label_ArgandVersion.setText('pyArgand v'+str(self.argand.__version__))
        self.ui.verticalLayout_argand.addWidget(self.argand)

        self.prepare_the_plot_panels()
        self.Connect_QtWidgets_and_Functions()
        self.read_in_user_settings()
        self.ui.tab_Main.setCurrentIndex(0)
        self.refresh_sample_P_value()
        self.refresh_sample_b_and_theta_value()

        self.ui.comboBox_DCM_DWMethod.addItem('None')
        self.ui.comboBox_Sample_Elemental_DWMethod.addItem('None')
        self.ui.comboBox_Sample_Compound_DWMethod.addItem('None')

        self.refresh_forth_Miller_Bravais_indice()
        self.Sample_ElementalCompound_choice_changed()

        self.addVersionToAbout()

    def addVersionToAbout(self):
        tmp_str = self.ui.textEdit_aboutTxt.toHtml()
        str_Torricelli = "{id}  <b>v{version}</b> - last modified: <b>{date}</b> by <b>{author}</b><br>".format(id=self.__svnID__.split(' ')[1], version=self.__version__, date=self.__modDate__, author=self.__changedBy__)
        str_pyArgand   = "{id}    <b>v{version}</b> - last modified: <b>{date}</b> by <b>{author}</b><br>".format(id=self.argand.__svnID__.split(' ')[1], version=self.argand.__version__, date=self.argand.__modDate__, author=self.argand.__changedBy__)
        new_str        = str_Torricelli + str_pyArgand + tmp_str
        # Font settings
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(QtGui.QFont.Normal)
        # add modified text
        self.ui.textEdit_aboutTxt.setFont(font)
        self.ui.textEdit_aboutTxt.setHtml(new_str)


    ## Defines the pyqtgraph panels where all plots will be done.
    def prepare_the_plot_panels(self):
        grid_transparency = 0.1

        self.Pyqt_View_raw_refl = pg.PlotWidget(title='I0-Normalised reflectivity')
        self.Pyqt_View_raw_refl.setLabel('left', "Reflectivity", units=' arb. units')
        self.Pyqt_View_raw_refl.setLabel('bottom', "Photon energy", units='eV')
        self.Pyqt_View_raw_refl.showGrid(x=True, y=False, alpha=grid_transparency)
        self.Pyqt_View_raw_refl.showAxis('top', show=True)         #('top', showValues=False) # Where to write this ?!!
        self.ui.horizontalLayout_raw_refl.addWidget(self.Pyqt_View_raw_refl)
        self.Pyqt_View_raw_refl.enableAutoRange()

        self.Pyqt_View_raw_ey = pg.PlotWidget(title='Summed electron yield of given components (I0-normalised)')
        self.Pyqt_View_raw_ey.setLabel('left', "Electron yield", units=' arb. units')
        self.Pyqt_View_raw_ey.setLabel('bottom', "Photon energy", units='eV')
        self.Pyqt_View_raw_ey.showGrid(x=True, y=True, alpha=grid_transparency)
        self.Pyqt_View_raw_ey.showAxis('top', show=True)
        self.ui.horizontalLayout_raw_ey.addWidget(self.Pyqt_View_raw_ey)
        #self.Pyqt_View_raw_refl.enableAutoRange()
        self.Pyqt_View_raw_ey.enableAutoRange()

        self.Pyqt_View_idealRefl = pg.PlotWidget(title='Ideal reflectivities and Phase')
        self.Pyqt_View_idealRefl.setLabel('left', "Reflectivity or Phase/Pi")
        self.Pyqt_View_idealRefl.setLabel('bottom', "Photon energy relative to theoretical Bragg energy", units='eV')
        self.Pyqt_View_idealRefl.showGrid(x=True, y=True, alpha=grid_transparency)
        self.Pyqt_View_idealRefl.showAxis('top', show=True)
        self.ui.verticalLayout_idealReflec.addWidget(self.Pyqt_View_idealRefl)

        self.Pyqt_View_refl_fit = pg.PlotWidget(title='Reflectivity fit result')
        self.Pyqt_View_refl_fit.setLabel('left', "Reflectivity", units=' arb. units')
        self.Pyqt_View_refl_fit.setLabel('bottom', "Photon energy relative to theoretical Bragg energy", units='eV')
        self.Pyqt_View_refl_fit.showGrid(x=True, y=True, alpha=grid_transparency)
        self.Pyqt_View_refl_fit.showAxis('top', show=True)
        self.ui.verticalLayout_fit_refl.addWidget(self.Pyqt_View_refl_fit)
        self.Pyqt_View_refl_fit.enableAutoRange()

        self.Pyqt_View_ey_fit = pg.PlotWidget(title='Electron Yield fit result')
        self.Pyqt_View_ey_fit.setLabel('left', 'Normalised Photoelectron yield', units=' arb. units')
        self.Pyqt_View_ey_fit.setLabel('bottom', "Photon energy relative to theoretical Bragg energy", units='eV')
        self.Pyqt_View_ey_fit.showGrid(x=True, y=True, alpha=grid_transparency)
        self.Pyqt_View_ey_fit.showAxis('top', show=True)
        self.ui.verticalLayout_fit_ey.addWidget(self.Pyqt_View_ey_fit)
        self.Pyqt_View_ey_fit.enableAutoRange()


    ## Action to be taken when Torrivelli is quited:
    # Saves a number of information (folder, values)
    # This file will be read by next use by read_in_user_settings
    def closeEvent(self, event):
        user_file_name =  Torricelli_program_folder_path + os.sep+'imports'+os.sep+'user_settings'
        user_file = open(user_file_name, 'w')
        user_file.write(self.ui.LineEdit_CurrentWorkingDirectory.text()+'\n')
        # Tab Theoretical refl and phase
        user_file.write(str(self.ui.doubleSpinBox_theoReflRange.value())+'\n')
        user_file.write(str(self.ui.doubleSpinBox_sample_deviation_NI.value())+'\n')
        user_file.write(str(self.ui.doubleSpinBox_sample_miscut.value())+'\n')
        user_file.write(str(self.ui.radioButton_Sample_Elemental.isChecked())+'\n') # Elemental or Compound
        user_file.write(str(self.ui.comboBox_Sample_Elemental_Element.currentIndex())+'\n')
        user_file.write(str(self.ui.comboBox_Sample_Compound_Element.currentIndex())+'\n')
        user_file.write(str(self.ui.spinBox_Sample_Elemental_h.value())+'\n')
        user_file.write(str(self.ui.spinBox_Sample_Elemental_k.value())+'\n')
        user_file.write(str(self.ui.spinBox_Sample_Elemental_l.value())+'\n')
        user_file.write(str(self.ui.spinBox_Sample_Compound_h.value())+'\n')
        user_file.write(str(self.ui.spinBox_Sample_Compound_k.value())+'\n')
        user_file.write(str(self.ui.spinBox_Sample_Compound_l.value())+'\n')
        # Tab Fit Yield
        user_file.write(str(self.ui.radioButton_D_approx.isChecked())+'\n')
        user_file.write(str(self.ui.spinBox_NonDipolar_Element_Z.value())+'\n') # Z element
        user_file.write(str(self.ui.doubleSpinBox_ndp_delta_p.value())+'\n') # delta p
        user_file.write(str(self.ui.doubleSpinBox_ndp_delta_d.value())+'\n') # delta d
        user_file.write(str(self.ui.doubleSpinBox_ndp_phi.value())+'\n') # phi
        user_file.write(str(self.ui.doubleSpinBox_EYinit_man_gamma.value())+'\n') # manual gamma
        user_file.write(str(self.ui.doubleSpinBox_EYinit_man_SR.value())+'\n') # manual sr

        user_file.close()
        # save argand diagram if there is one
        root = self.ui.treeWidget_Argand_List.invisibleRootItem()
        if root.childCount() > 0:
            self.Argand_Save(str(self.ui.LineEdit_CurrentWorkingDirectory.text())+os.sep+self.argand_SaveSubFolder+'autosave_'+self.timestamp()+'_lastSession.csv')
        event.accept() # in this particular case, the closeEvent(), one should keep the event.accept(), as advised here:
        # http://doc.qt.digia.com/qq/qq11-events.html


    ## Loads a number of information (folder, values) saved from the last use of
    # Torricelli. This file has been created by: closeEvent
    def read_in_user_settings(self):
        try:
            with open(Torricelli_program_folder_path + os.sep+'imports'+os.sep+'user_settings', 'r') as f:
                self.ui.LineEdit_CurrentWorkingDirectory.setText(f.readline().rstrip('\n'))
                self.choose_dataFolder(self.ui.LineEdit_CurrentWorkingDirectory.text())

                # Tab theoretical reflectivity and phase
                self.ui.doubleSpinBox_theoReflRange.setValue(float(f.readline().rstrip('\n')))
                self.ui.doubleSpinBox_sample_deviation_NI.setValue(float(f.readline().rstrip('\n')))
                self.ui.doubleSpinBox_sample_miscut.setValue(float(f.readline().rstrip('\n')))
                if f.readline().rstrip('\n') in ['True']:
                    self.ui.radioButton_Sample_Elemental.setChecked(True)
                else:
                    self.ui.radioButton_Sample_Compound.setChecked(True)
                self.ui.comboBox_Sample_Elemental_Element.setCurrentIndex(int(f.readline().rstrip('\n')))
                self.ui.comboBox_Sample_Compound_Element.setCurrentIndex( int(f.readline().rstrip('\n')))
                self.ui.spinBox_Sample_Elemental_h.setValue(int(f.readline().rstrip('\n')))
                self.ui.spinBox_Sample_Elemental_k.setValue(int(f.readline().rstrip('\n')))
                self.ui.spinBox_Sample_Elemental_l.setValue(int(f.readline().rstrip('\n')))
                self.ui.spinBox_Sample_Compound_h.setValue( int(f.readline().rstrip('\n')))
                self.ui.spinBox_Sample_Compound_k.setValue( int(f.readline().rstrip('\n')))
                self.ui.spinBox_Sample_Compound_l.setValue( int(f.readline().rstrip('\n')))


                # Tab Fit yield
                if f.readline().rstrip('\n') in ['True']:
                    self.ui.radioButton_D_approx.setChecked(True)
                else:
                    self.ui.radioButton_DQ_approx.setChecked(True)
                self.ui.spinBox_NonDipolar_Element_Z.setValue(int(f.readline().rstrip('\n')))
                self.ui.doubleSpinBox_ndp_delta_p.setValue(float(f.readline().rstrip('\n')))
                self.ui.doubleSpinBox_ndp_delta_d.setValue(float(f.readline().rstrip('\n')))
                self.ui.doubleSpinBox_ndp_phi.setValue(float(f.readline().rstrip('\n')))
                self.ui.doubleSpinBox_EYinit_man_gamma.setValue(float(f.readline().rstrip('\n')))
                self.ui.doubleSpinBox_EYinit_man_SR.setValue(float(f.readline().rstrip('\n')))

        except (IOError, ValueError) as e:
            print e, '\nEither your \"user_settings\" files does not exist yet, of the format is too old. A new file is created'
            self.ui.LineEdit_CurrentWorkingDirectory.setText(u'SET THE WORKING DIRECTORY !!! AS WELL AS \u03BE AND \u03B2')
            self.ui.statusbar.showMessage("Default folder and file number used.", 5000)
            self.ui.doubleSpinBox_theoReflRange.setValue(10)
            self.ui.comboBox_Sample_Elemental_Element.setCurrentIndex(10)
            self.ui.spinBox_NonDipolar_Element_Z.setValue(6)
            self.ui.doubleSpinBox_sample_miscut.setValue(0)
            self.ui.doubleSpinBox_sample_deviation_NI.setValue(3.5)
            self.ui.radioButton_pi_pol_light.setChecked(True)
            self.ui.doubleSpinBox_ndp_phi.setValue(90)
            self.ui.doubleSpinBox_ndp_delta_p.setValue(0)
            self.ui.doubleSpinBox_ndp_delta_d.setValue(0)

    def angularModeOption(self):
        # toggle between angular single slice mode and "normal" mode
        if self.ui.checkBox_AngularModeToggle.isChecked():
            self.ui.statusbar.showMessage("NOTE: You are using the angular-resolved functionality: usual photon energy checks on the data are not performed!")

            self.Transform_R_and_EY_userFile_to_TorricelliFriendly(calledFromAngularCheckBox=True)

            # further settings for spinBox_SelectedSlice have to be done in Transform_R_and_EY_userFile_to_TorricelliFriendly

            self.ui.label_select_slice.setEnabled(True)
            self.ui.label_AngleOfSlice.setEnabled(True)
            self.ui.label_sliceAngle.setEnabled(True)
            self.ui.label_angles.setEnabled(True)
            self.ui.lineEdit_angles_path.setEnabled(True)
            self.ui.button_angles_file.setEnabled(True)
            self.ui.button_display_angles.setEnabled(True)
        else:
            self.ui.label_select_slice.setEnabled(False)
            self.ui.label_AngleOfSlice.setEnabled(False)
            self.ui.label_sliceAngle.setEnabled(False)
            self.ui.label_angles.setEnabled(False)
            self.ui.lineEdit_angles_path.setEnabled(False)
            self.ui.lineEdit_angles_path.setText('')
            self.ui.button_angles_file.setEnabled(False)
            self.ui.button_display_angles.setEnabled(False)
            self.ui.spinBox_SelectedSlice.setEnabled(False)
            self.ui.label_angles_file_info.setText('')


    ## Connects all GUI buttons, lineEdit, tab and so on to the appropriate functions.
    def Connect_QtWidgets_and_Functions(self):
        root = self.ui.treeWidget_Argand_List.invisibleRootItem()
        self.ui.button_CurrentWorkingDirectory.clicked.connect(self.choose_dataFolder)
        self.ui.signal_name.textEdited.connect(self.update_component_list)
        ## Section Structure Factors
        self.ui.comboBox_DCM_Element.currentIndexChanged.connect(self.update_structure_DCM)
        self.ui.doubleSpinBox_DCM_Temperature.valueChanged.connect(self.update_structure_DCM)
        self.ui.comboBox_Sample_Elemental_Element.currentIndexChanged.connect(self.update_structure_Sample_Elemental)
        self.ui.doubleSpinBox_Sample_Elemental_Temperature.valueChanged.connect(self.update_structure_Sample_Elemental)
        self.ui.comboBox_Sample_Compound_Element.currentIndexChanged.connect(self.update_structure_Sample_Compound)
        self.ui.doubleSpinBox_Sample_Compound_Temperature.valueChanged.connect(self.update_structure_Sample_Compound)
        self.ui.comboBox_DCM_Element.setCurrentIndex(2)#Si
        self.update_structure_Sample_Compound(0) # As 0 is default, the currentIndexChanged is not send, and therefore no Structure is displayed
        self.ui.pushButton_calculateAllStructureFactors.clicked.connect(self.calculate_structure_factors)
        self.ui.pushButton_editDCM.clicked.connect(self.allow_DCM_parameter_modification)
        self.ui.radioButton_Sample_Elemental.clicked.connect(self.Sample_ElementalCompound_choice_changed)
        self.ui.radioButton_Sample_Compound.clicked.connect(self.Sample_ElementalCompound_choice_changed)
        self.ui.spinBox_DCM_h.valueChanged.connect(self.refresh_forth_Miller_Bravais_indice)
        self.ui.spinBox_DCM_k.valueChanged.connect(self.refresh_forth_Miller_Bravais_indice)
        self.ui.spinBox_Sample_Elemental_h.valueChanged.connect(self.refresh_forth_Miller_Bravais_indice)
        self.ui.spinBox_Sample_Elemental_k.valueChanged.connect(self.refresh_forth_Miller_Bravais_indice)
        self.ui.spinBox_Sample_Compound_h.valueChanged.connect(self.refresh_forth_Miller_Bravais_indice)
        self.ui.spinBox_Sample_Compound_k.valueChanged.connect(self.refresh_forth_Miller_Bravais_indice)
        self.ui.doubleSpinBox_sample_deviation_NI.valueChanged.connect(self.refresh_sample_b_and_theta_value)
        self.ui.doubleSpinBox_sample_miscut.valueChanged.connect(self.refresh_sample_b_and_theta_value)
        self.ui.doubleSpinBox_sample_deviation_NI.valueChanged.connect(self.refresh_sample_P_value)
        self.ui.radioButton_pi_pol_light.clicked.connect(self.refresh_sample_P_value)
        self.ui.radioButton_sigma_pol_light.clicked.connect(self.refresh_sample_P_value)
        # If some parameter is changed: clear the results
        self.ui.radioButton_Sample_Elemental.clicked.connect(self.clear_structFact_display)
        self.ui.radioButton_Sample_Compound.clicked.connect(self.clear_structFact_display)
        self.ui.comboBox_DCM_Element.currentIndexChanged.connect(self.clear_structFact_display)
        self.ui.doubleSpinBox_DCM_Temperature.valueChanged.connect(self.clear_structFact_display)
        self.ui.comboBox_Sample_Elemental_Element.currentIndexChanged.connect(self.clear_structFact_display)
        self.ui.doubleSpinBox_Sample_Elemental_Temperature.valueChanged.connect(self.clear_structFact_display)
        self.ui.comboBox_Sample_Compound_Element.currentIndexChanged.connect(self.clear_structFact_display)
        self.ui.doubleSpinBox_Sample_Compound_Temperature.valueChanged.connect(self.clear_structFact_display)
        self.ui.comboBox_DCM_DWMethod.currentIndexChanged.connect(self.clear_structFact_display)
        self.ui.comboBox_Sample_Elemental_DWMethod.currentIndexChanged.connect(self.clear_structFact_display)
        self.ui.comboBox_Sample_Compound_DWMethod.currentIndexChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_DCM_h.valueChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_DCM_k.valueChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_DCM_l.valueChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_Sample_Elemental_h.valueChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_Sample_Elemental_k.valueChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_Sample_Elemental_l.valueChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_Sample_Compound_h.valueChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_Sample_Compound_k.valueChanged.connect(self.clear_structFact_display)
        self.ui.spinBox_Sample_Compound_l.valueChanged.connect(self.clear_structFact_display)
        ## Section Import Files
        self.ui.button_refl_file.clicked.connect(self.open_refl)
        self.ui.button_display_refl.clicked.connect(self.display_refl)
        self.ui.button_ey_file.clicked.connect(self.open_ey)
        self.ui.button_display_ey.clicked.connect(self.display_ey)
        self.ui.button_angles_file.clicked.connect(self.open_angles)
        self.ui.button_display_angles.clicked.connect(self.display_angles)
        self.ui.button_import.clicked.connect(self.Transform_R_and_EY_userFile_to_TorricelliFriendly)
        self.ui.checkBox_AngularModeToggle.toggled.connect(self.angularModeOption)
        self.ui.spinBox_SelectedSlice.valueChanged.connect(self.Transform_R_and_EY_userFile_to_TorricelliFriendly)
        ## Section Fit Reflectivity
        self.ui.button_set_refl.clicked.connect(self.set_refl_par)
        self.ui.button_fit_refl.clicked.connect(self.fit_Refl)
        ## Section Fit EY: Fc, Pc, N, and Q and ndp calculation
        ## Subsection Non Dipolar Parameters
        self.ui.comboBox_NonDipolar_Element.currentIndexChanged.connect(self.nonDipolar_changeElement)
        self.ui.spinBox_NonDipolar_Element_Z.valueChanged.connect(self.nonDipolar_changeElementZ)
        self.ui.comboBox_NonDipolar_Shells.currentIndexChanged.connect(lambda val: self.display_Gamma_file(val))
        self.ui.pushButton_exportGammaFile.clicked.connect(self.saveGammaFile)
        ## Subection Fit EY
        self.ui.pushButton_reset_initial_parameters.clicked.connect(self.reset_ey_par)
        self.ui.button_fit_ey.clicked.connect(self.fit_ElYield)
        self.ui.pushButton_set_fitParam_for_manual.clicked.connect(self.set_fitEYparam_forManualUse)
        self.ui.horizontalSlider_manual_fc.sliderMoved.connect(lambda val, who="fc": self.EY_initSlider_valueChanged(who))
        self.ui.horizontalSlider_manual_fc.actionTriggered.connect(lambda val, who="fc": self.EY_initSlider_valueChanged(who))
        self.ui.doubleSpinBox_fc.valueChanged.connect(lambda val, who="fc": self.EY_initSpin_valueChanged(who))
        self.ui.horizontalSlider_manual_pc.sliderMoved.connect(lambda val, who="pc": self.EY_initSlider_valueChanged(who))
        self.ui.horizontalSlider_manual_pc.actionTriggered.connect(lambda val, who="pc": self.EY_initSlider_valueChanged(who))
        self.ui.doubleSpinBox_pc.valueChanged.connect(lambda val, who="pc": self.EY_initSpin_valueChanged(who))
        self.ui.checkBox_display_manual_EY.clicked.connect(self.update_EY_plot)
        self.ui.checkBox_ignore_MonteCarlo.toggled.connect(self.update_chiSquared)
        self.ui.pushButton_saveToArgand.clicked.connect(self.Argand_saveFitResult_and_plot)
        self.ui.radioButton_EYinit_theo_gamma.toggled.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.radioButton_EYinit_man_gamma.toggled.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.radioButton_EYinit_man_SR.toggled.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.checkBox_eyfit_fitFc.clicked.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.doubleSpinBox_fc.valueChanged.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.checkBox_eyfit_fitPc.clicked.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.checkBox_eyfit_fitN.clicked.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.checkBox_eyfit_fitgamma.clicked.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.checkBox_eyfit_fitSr.clicked.connect(self.ndp_choose_work_with_SR_or_gamma)
        self.ui.doubleSpinBox_ndp_delta_p.valueChanged.connect(self.updatePhaseShiftDifference)
        self.ui.doubleSpinBox_ndp_delta_d.valueChanged.connect(self.updatePhaseShiftDifference)
        self.ui.doubleSpinBox_ndp_phi.valueChanged.connect(self.refresh_sample_P_value)
        self.ui.spinBox_NonDipolar_Element_Z.valueChanged.connect(self.setPhotoelectronKineticEnergy)
        self.ui.comboBox_NonDipolar_Shells.currentIndexChanged.connect(self.setPhotoelectronKineticEnergy)
        self.ui.doubleSpinBox_ndp_EBragg.valueChanged.connect(self.setPhotoelectronKineticEnergy)

        self.ui.radioButton_D_approx.clicked.connect(self.setGammaValue)
        self.ui.radioButton_DQ_approx.clicked.connect(self.setGammaValue)
        self.ui.doubleSpinBox_ndp_Ekin.valueChanged.connect(self.setGammaValue)

        self.ui.doubleSpinBox_EYinit_man_gamma.valueChanged.connect(self.setYieldParameters)
        self.ui.doubleSpinBox_EYinit_theo_gamma.valueChanged.connect(self.setYieldParameters)
        self.ui.radioButton_EYinit_theo_gamma.clicked.connect(self.setYieldParameters)
        self.ui.radioButton_EYinit_man_gamma.clicked.connect(self.setYieldParameters)
        self.ui.doubleSpinBox_EYinit_Delta.valueChanged.connect(self.setYieldParameters)
        self.ui.doubleSpinBox_EYinit_Pe.valueChanged.connect(self.setYieldParameters)
        self.ui.radioButton_D_approx.clicked.connect(self.setYieldParameters)
        self.ui.radioButton_DQ_approx.clicked.connect(self.setYieldParameters)
        self.ui.doubleSpinBox_ndp_Ekin.valueChanged.connect(self.setYieldParameters)

        ## Section: Argand diagram
        self.vb = self.argand.plotItem.vb # define ViewBox of the ArgandPlotWidget
        self.ui.treeWidget_Argand_List.invisibleRootItem().setFlags(QtCore.Qt.ItemFlags(QtCore.Qt.ItemIsEnabled))
        self.Argand_QTreeWidgetSignalsSwitch(on=True)
        # following line does not work for no apparent reason (using a combination of rowsInserted and rowsRemoved instead)
        #self.ui.treeWidget_Argand_List.model().rowsMoved.connect(lambda sourceParent,sourceStart,sourceEnd,destParent,destStart, testStr='moved': self.test(testStr))
        #self.ui.treeWidget_Argand_List.model().rowsInserted.connect(lambda parentIndex, start, end, what='inserted': self.Argand_itemsMoved(parentIndex, start, end, what))
        #self.ui.treeWidget_Argand_List.model().rowsRemoved.connect(lambda parentIndex,start,end, what='removed': self.Argand_itemsMoved(parentIndex, start, end, what))
        self.ui.pushButton_Argand_AddGroup.clicked.connect(self.Argand_AddGroup)
        self.ui.pushButton_Argand_Remove.clicked.connect(lambda: self.Argand_Remove(self.ui.treeWidget_Argand_List.selectedItems()))
        self.ui.pushButton_Argand_removeAll.clicked.connect(self.Argand_RemoveAll)
        self.ui.pushButton_Argand_AddDataset.clicked.connect(self.Argand_ValueLogFile)
        self.ui.pushButton_Argand_ManualValues.clicked.connect(self.Argand_ManualValues)
        self.ui.pushButton_Argand_Save.clicked.connect(self.Argand_Save)
        self.ui.pushButton_Argand_Load.clicked.connect(self.Argand_Load)
        self.ui.checkBox_splitVector.clicked.connect(self.Argand_update_Split_display)
        self.ui.checkBox_splitVector.clicked.connect(self.Argand_splitVector)
        self.ui.doubleSpinBox_Argand_nA.valueChanged.connect(self.Argand_update_SplitVector_plot)
        self.ui.doubleSpinBox_Argand_pcA.valueChanged.connect(self.Argand_update_SplitVector_plot)
        self.ui.doubleSpinBox_Argand_fcA.valueChanged.connect(self.Argand_update_SplitVector_plot)
        self.ui.doubleSpinBox_Argand_nA.editingFinished.connect(self.Argand_splitVector_symmetricRepositioning_update)
        self.ui.doubleSpinBox_Argand_pcA.editingFinished.connect(self.Argand_splitVector_symmetricRepositioning_update)
        self.ui.doubleSpinBox_Argand_fcA.editingFinished.connect(self.Argand_splitVector_symmetricRepositioning_update)
        self.ui.checkBox_displayLabels.toggled.connect(lambda checked: self.Argand_Labels(checked))
        self.ui.checkBox_symmetricSplit.toggled.connect(self.Argand_splitVector_symmetricRepositioning_update)
        self.ui.pushButton_GpBySlice.clicked.connect(self.Argand_GpBySlice)
        self.ui.checkBox_Argand_display_originVectors.clicked.connect(lambda checked: self.Argand_updateItems(item_list=map(root.child, range(root.childCount())),recalcGP=False))
        self.ui.checkBox_Argand_display_group_errorBars.clicked.connect(lambda checked: self.Argand_updateItems(item_list=map(root.child, range(root.childCount())),recalcGP=False))
        self.ui.checkBox_Argand_display_errorBars.clicked.connect(self.Argand_replotDiagram)
        self.ui.pushButton_refresh.clicked.connect(self.Argand_refresh_tree_and_plot)
        self.ui.spinBox_Fc_grid_lines.editingFinished.connect(self.Argand_updateFcPcGrid)
        self.ui.spinBox_Pc_grid_lines.editingFinished.connect(self.Argand_updateFcPcGrid)
        self.ui.checkBox_SortOnOff.clicked.connect(self.Argand_sortOnOff)
        self.ui.checkBox_ArgandList_editable.clicked.connect(self.ArgandList_editable)

        ## Section: Geometry, About, License:
        self.ui.label_geometry.setPixmap(QtGui.QPixmap(Torricelli_program_folder_path+os.sep+'imports'+os.sep+'Geometry.png'))


        # ---------------------
        # using signal proxy
        # ---------------------
        # signal is triggered if mouse is moved
        # slot is a function that is called if the signal is triggered (here: mouse is moved)
        # the slot-funcion is given a list of arguments of the signal event
        # here: the first argument is a QPointF object which contains the position of the cursor
        self.proxy = pg.SignalProxy(self.argand.plotItem.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

    #def progressBar(self, value, endvalue, bar_length=50, prefix=""):
    #    percent = float(value) / endvalue
    #    arrow = '=' * int(round(percent * bar_length)-1) + '>'
    #    spaces = ' ' * (bar_length - len(arrow))
    #    return str(prefix+"[{0}] {1}%".format(arrow + spaces, int(round(percent * 100))))

    ## Catches when the keys 'n' or 'p' are pressed by the user on the keyboard
    # in turn, the next/previous tab is selected.
    def keyPressEvent(self, event) :
        key = event.key()

        if event.type() == QtCore.QEvent.KeyPress and 16777239==key: # This number is not elegent, Corresponds to Ctrl+PageUp
            self.ui.tab_Main.setCurrentIndex(self.ui.tab_Main.currentIndex() + 1)
        elif event.type() == QtCore.QEvent.KeyPress and 16777238==key: #Ctrl+PageDown
            self.ui.tab_Main.setCurrentIndex(self.ui.tab_Main.currentIndex() - 1)
        # deletes a line in the Argand TreeWidget if pressing del
        elif (len(self.ui.treeWidget_Argand_List.selectedItems()) > 0 and
            event.type() == QtCore.QEvent.KeyPress and
            event.key()  == QtCore.Qt.Key_Delete):
            # removes the selected Items
            self.Argand_Remove(self.ui.treeWidget_Argand_List.selectedItems())
        elif (len(self.ui.treeWidget_Argand_List.selectedItems()) > 0 and
            event.type() == QtCore.QEvent.KeyPress and
            event.key()  == QtCore.Qt.Key_Escape):
            for item in self.ui.treeWidget_Argand_List.selectedItems():
                item.setSelected(False)
        elif (len(self.ui.treeWidget_Argand_List.selectedItems()) > 0 and
            event.type() == QtCore.QEvent.KeyPress and
            event.key()  == QtCore.Qt.Key_F2):
            pass
        else:
            super(Torricelli, self).keyPressEvent(event)


    # Create Method for recognition of mouse movement
    def mouseMoved(self,evt):
        # from the list of arguments in evt just use the first one
        # this is of type QPointF which contains the position of the curor
        self.pos = evt[0]
        # following code is executed if the mouse position is
        # within the boundaries of the ArgandPlotWidget-Object
        if self.argand.plotItem.sceneBoundingRect().contains(self.pos):
            # translate the mouse position to the coordinates in the ViewBox of the PlotWidget
            self.mousePoint = self.vb.mapSceneToView(self.pos)
            self.ui.label_livePc.setText("Pc = %0.4f" % (np.arctan2(self.mousePoint.y(),self.mousePoint.x())/(2*np.pi) if np.arctan2(self.mousePoint.y(),self.mousePoint.x())/(2*np.pi)>=0 else (np.arctan2(self.mousePoint.y(),self.mousePoint.x())+2*np.pi)/(2*np.pi)))
            self.ui.label_liveFc.setText("Fc = %0.4f" % np.sqrt(self.mousePoint.x()**2+self.mousePoint.y()**2))


# Starts the program
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = Torricelli()
    myapp.show()
    sys.exit(app.exec_())
