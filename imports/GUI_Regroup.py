# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'imports/GUI_Regroup.ui'
#
# Created: Fri Jul 15 09:39:16 2016
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

class Ui_Dialog_Regroup(object):
    def setupUi(self, Dialog_Regroup):
        Dialog_Regroup.setObjectName(_fromUtf8("Dialog_Regroup"))
        Dialog_Regroup.resize(355, 146)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog_Regroup)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(Dialog_Regroup)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 1)
        self.label = QtGui.QLabel(Dialog_Regroup)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtGui.QLabel(Dialog_Regroup)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.lineEdit_GpNameSuffix = QtGui.QLineEdit(Dialog_Regroup)
        self.lineEdit_GpNameSuffix.setPlaceholderText(_fromUtf8(""))
        self.lineEdit_GpNameSuffix.setObjectName(_fromUtf8("lineEdit_GpNameSuffix"))
        self.gridLayout.addWidget(self.lineEdit_GpNameSuffix, 1, 0, 1, 1)
        self.label_2 = QtGui.QLabel(Dialog_Regroup)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)

        self.retranslateUi(Dialog_Regroup)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog_Regroup.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog_Regroup.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_Regroup)

    def retranslateUi(self, Dialog_Regroup):
        Dialog_Regroup.setWindowTitle(_translate("Dialog_Regroup", "Dialog", None))
        self.label.setText(_translate("Dialog_Regroup", "Please choose a group name suffix:", None))
        self.label_3.setToolTip(_translate("Dialog_Regroup", "If a group is selected all the containing items will be regrouped. The argand diagram is automatically saved before regrouping.", None))
        self.label_3.setText(_translate("Dialog_Regroup", "The selected items will be regrouped by slice.", None))
        self.label_2.setText(_translate("Dialog_Regroup", "(XX_yourGroupNameSuffix,     XX = slice Nb)", None))

