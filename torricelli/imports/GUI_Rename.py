# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI_Rename.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog_Rename(object):
    def setupUi(self, Dialog_Rename):
        Dialog_Rename.setObjectName("Dialog_Rename")
        Dialog_Rename.resize(368, 149)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog_Rename)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog_Rename)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 1)
        self.label = QtWidgets.QLabel(Dialog_Rename)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(Dialog_Rename)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.lineEdit_newName = QtWidgets.QLineEdit(Dialog_Rename)
        self.lineEdit_newName.setPlaceholderText("")
        self.lineEdit_newName.setObjectName("lineEdit_newName")
        self.gridLayout.addWidget(self.lineEdit_newName, 1, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog_Rename)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)

        self.retranslateUi(Dialog_Rename)
        self.buttonBox.accepted.connect(Dialog_Rename.accept)
        self.buttonBox.rejected.connect(Dialog_Rename.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_Rename)

    def retranslateUi(self, Dialog_Rename):
        _translate = QtCore.QCoreApplication.translate
        Dialog_Rename.setWindowTitle(_translate("Dialog_Rename", "Rename"))
        self.label.setText(_translate("Dialog_Rename", "Please choose a new Name for the element:"))
        self.label_3.setToolTip(_translate("Dialog_Rename", "If a group is selected all the containing items will be regrouped. The argand diagram is automatically saved before regrouping."))
        self.label_3.setText(_translate("Dialog_Rename", "the name will be a prefix following by an iterator."))
        self.label_2.setText(_translate("Dialog_Rename", "If you have selected more than one Item,"))

