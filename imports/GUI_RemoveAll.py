# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI_RemoveAll.ui'
#
# Created: Thu Dec 08 15:09:44 2016
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog_RemoveAll(object):
    def setupUi(self, Dialog_RemoveAll):
        Dialog_RemoveAll.setObjectName(_fromUtf8("Dialog_RemoveAll"))
        Dialog_RemoveAll.resize(368, 195)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog_RemoveAll)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(Dialog_RemoveAll)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.No|QtGui.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.label = QtGui.QLabel(Dialog_RemoveAll)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtGui.QLabel(Dialog_RemoveAll)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)

        self.retranslateUi(Dialog_RemoveAll)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog_RemoveAll.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog_RemoveAll.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_RemoveAll)

    def retranslateUi(self, Dialog_RemoveAll):
        Dialog_RemoveAll.setWindowTitle(_translate("Dialog_RemoveAll", "Remove all", None))
        self.label.setText(_translate("Dialog_RemoveAll", "ATTENTION!\n"
"\n"
"This will remove all elements of your list\n"
"and clear the Argand Diagram!\n"
"", None))
        self.label_3.setToolTip(_translate("Dialog_RemoveAll", "If a group is selected all the containing items will be regrouped. The argand diagram is automatically saved before regrouping.", None))
        self.label_3.setText(_translate("Dialog_RemoveAll", "\n"
"Are you sure you want to do this?\n"
"", None))

