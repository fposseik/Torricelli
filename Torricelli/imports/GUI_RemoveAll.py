# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI_RemoveAll.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog_RemoveAll(object):
    def setupUi(self, Dialog_RemoveAll):
        Dialog_RemoveAll.setObjectName("Dialog_RemoveAll")
        Dialog_RemoveAll.resize(368, 195)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog_RemoveAll)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog_RemoveAll)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No|QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.label = QtWidgets.QLabel(Dialog_RemoveAll)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(Dialog_RemoveAll)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)

        self.retranslateUi(Dialog_RemoveAll)
        self.buttonBox.accepted.connect(Dialog_RemoveAll.accept)
        self.buttonBox.rejected.connect(Dialog_RemoveAll.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_RemoveAll)

    def retranslateUi(self, Dialog_RemoveAll):
        _translate = QtCore.QCoreApplication.translate
        Dialog_RemoveAll.setWindowTitle(_translate("Dialog_RemoveAll", "Remove all"))
        self.label.setText(_translate("Dialog_RemoveAll", "ATTENTION!\n"
"\n"
"This will remove all elements of your list\n"
"and clear the Argand Diagram!\n"
""))
        self.label_3.setToolTip(_translate("Dialog_RemoveAll", "If a group is selected all the containing items will be regrouped. The argand diagram is automatically saved before regrouping."))
        self.label_3.setText(_translate("Dialog_RemoveAll", "\n"
"Are you sure you want to do this?\n"
""))

