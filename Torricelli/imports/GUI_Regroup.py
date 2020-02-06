# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI_Regroup.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog_Regroup(object):
    def setupUi(self, Dialog_Regroup):
        Dialog_Regroup.setObjectName("Dialog_Regroup")
        Dialog_Regroup.resize(355, 149)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog_Regroup)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog_Regroup)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 1)
        self.label = QtWidgets.QLabel(Dialog_Regroup)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(Dialog_Regroup)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.lineEdit_GpNameSuffix = QtWidgets.QLineEdit(Dialog_Regroup)
        self.lineEdit_GpNameSuffix.setPlaceholderText("")
        self.lineEdit_GpNameSuffix.setObjectName("lineEdit_GpNameSuffix")
        self.gridLayout.addWidget(self.lineEdit_GpNameSuffix, 1, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog_Regroup)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)

        self.retranslateUi(Dialog_Regroup)
        self.buttonBox.accepted.connect(Dialog_Regroup.accept)
        self.buttonBox.rejected.connect(Dialog_Regroup.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_Regroup)

    def retranslateUi(self, Dialog_Regroup):
        _translate = QtCore.QCoreApplication.translate
        Dialog_Regroup.setWindowTitle(_translate("Dialog_Regroup", "Dialog"))
        self.label.setText(_translate("Dialog_Regroup", "Please choose a group name suffix:"))
        self.label_3.setToolTip(_translate("Dialog_Regroup", "If a group is selected all the containing items will be regrouped. The argand diagram is automatically saved before regrouping."))
        self.label_3.setText(_translate("Dialog_Regroup", "The selected items will be regrouped by slice."))
        self.label_2.setText(_translate("Dialog_Regroup", "(XX_yourGroupNameSuffix,     XX = slice Nb)"))

