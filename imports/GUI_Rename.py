# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'imports/GUI_Rename.ui'
#
# Created: Mon Sep 12 16:02:51 2016
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_Dialog_Rename(object):
    def setupUi(self, Dialog_Rename):
        Dialog_Rename.setObjectName(_fromUtf8("Dialog_Rename"))
        Dialog_Rename.resize(368, 149)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog_Rename)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(Dialog_Rename)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 1)
        self.label = QtGui.QLabel(Dialog_Rename)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtGui.QLabel(Dialog_Rename)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.lineEdit_newName = QtGui.QLineEdit(Dialog_Rename)
        self.lineEdit_newName.setPlaceholderText(_fromUtf8(""))
        self.lineEdit_newName.setObjectName(_fromUtf8("lineEdit_newName"))
        self.gridLayout.addWidget(self.lineEdit_newName, 1, 0, 1, 1)
        self.label_2 = QtGui.QLabel(Dialog_Rename)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)

        self.retranslateUi(Dialog_Rename)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog_Rename.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog_Rename.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_Rename)

    def retranslateUi(self, Dialog_Rename):
        Dialog_Rename.setWindowTitle(_translate("Dialog_Rename", "Rename", None))
        self.label.setText(_translate("Dialog_Rename", "Please choose a new Name for the element:", None))
        self.label_3.setToolTip(_translate("Dialog_Rename", "If a group is selected all the containing items will be regrouped. The argand diagram is automatically saved before regrouping.", None))
        self.label_3.setText(_translate("Dialog_Rename", "the name will be a prefix following by an iterator.", None))
        self.label_2.setText(_translate("Dialog_Rename", "If you have selected more than one Item,", None))

