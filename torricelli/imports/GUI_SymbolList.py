# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI_SymbolList.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog_SymbolList(object):
    def setupUi(self, Dialog_SymbolList):
        Dialog_SymbolList.setObjectName("Dialog_SymbolList")
        Dialog_SymbolList.resize(223, 182)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog_SymbolList)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.radioButton_o = QtWidgets.QRadioButton(Dialog_SymbolList)
        self.radioButton_o.setChecked(True)
        self.radioButton_o.setObjectName("radioButton_o")
        self.verticalLayout.addWidget(self.radioButton_o)
        self.radioButton_t = QtWidgets.QRadioButton(Dialog_SymbolList)
        self.radioButton_t.setObjectName("radioButton_t")
        self.verticalLayout.addWidget(self.radioButton_t)
        self.radioButton_s = QtWidgets.QRadioButton(Dialog_SymbolList)
        self.radioButton_s.setObjectName("radioButton_s")
        self.verticalLayout.addWidget(self.radioButton_s)
        self.radioButton_d = QtWidgets.QRadioButton(Dialog_SymbolList)
        self.radioButton_d.setObjectName("radioButton_d")
        self.verticalLayout.addWidget(self.radioButton_d)
        self.radioButton_plus = QtWidgets.QRadioButton(Dialog_SymbolList)
        self.radioButton_plus.setObjectName("radioButton_plus")
        self.verticalLayout.addWidget(self.radioButton_plus)
        self.radioButton_None = QtWidgets.QRadioButton(Dialog_SymbolList)
        self.radioButton_None.setObjectName("radioButton_None")
        self.verticalLayout.addWidget(self.radioButton_None)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog_SymbolList)
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog_SymbolList)
        self.buttonBox.accepted.connect(Dialog_SymbolList.accept)
        self.buttonBox.rejected.connect(Dialog_SymbolList.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_SymbolList)

    def retranslateUi(self, Dialog_SymbolList):
        _translate = QtCore.QCoreApplication.translate
        Dialog_SymbolList.setWindowTitle(_translate("Dialog_SymbolList", "List of symbols"))
        self.radioButton_o.setText(_translate("Dialog_SymbolList", "&Circle (o)"))
        self.radioButton_t.setText(_translate("Dialog_SymbolList", "&Triangle (t)"))
        self.radioButton_s.setText(_translate("Dialog_SymbolList", "&Square (s)"))
        self.radioButton_d.setText(_translate("Dialog_SymbolList", "&Diamond (d)"))
        self.radioButton_plus.setText(_translate("Dialog_SymbolList", "&Plus (+)"))
        self.radioButton_None.setText(_translate("Dialog_SymbolList", "&None (n)"))

