# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'imports/GUI_SymbolList.ui'
#
# Created: Thu Oct 22 14:29:35 2015
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog_SymbolList(object):
    def setupUi(self, Dialog_SymbolList):
        Dialog_SymbolList.setObjectName(_fromUtf8("Dialog_SymbolList"))
        Dialog_SymbolList.resize(223, 182)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog_SymbolList)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.radioButton_o = QtGui.QRadioButton(Dialog_SymbolList)
        self.radioButton_o.setChecked(True)
        self.radioButton_o.setObjectName(_fromUtf8("radioButton_o"))
        self.verticalLayout.addWidget(self.radioButton_o)
        self.radioButton_t = QtGui.QRadioButton(Dialog_SymbolList)
        self.radioButton_t.setObjectName(_fromUtf8("radioButton_t"))
        self.verticalLayout.addWidget(self.radioButton_t)
        self.radioButton_s = QtGui.QRadioButton(Dialog_SymbolList)
        self.radioButton_s.setObjectName(_fromUtf8("radioButton_s"))
        self.verticalLayout.addWidget(self.radioButton_s)
        self.radioButton_d = QtGui.QRadioButton(Dialog_SymbolList)
        self.radioButton_d.setObjectName(_fromUtf8("radioButton_d"))
        self.verticalLayout.addWidget(self.radioButton_d)
        self.radioButton_plus = QtGui.QRadioButton(Dialog_SymbolList)
        self.radioButton_plus.setObjectName(_fromUtf8("radioButton_plus"))
        self.verticalLayout.addWidget(self.radioButton_plus)
        self.radioButton_None = QtGui.QRadioButton(Dialog_SymbolList)
        self.radioButton_None.setObjectName(_fromUtf8("radioButton_None"))
        self.verticalLayout.addWidget(self.radioButton_None)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog_SymbolList)
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog_SymbolList)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog_SymbolList.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog_SymbolList.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_SymbolList)

    def retranslateUi(self, Dialog_SymbolList):
        Dialog_SymbolList.setWindowTitle(QtGui.QApplication.translate("Dialog_SymbolList", "List of symbols", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_o.setText(QtGui.QApplication.translate("Dialog_SymbolList", "&Circle (o)", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_t.setText(QtGui.QApplication.translate("Dialog_SymbolList", "&Triangle (t)", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_s.setText(QtGui.QApplication.translate("Dialog_SymbolList", "&Square (s)", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_d.setText(QtGui.QApplication.translate("Dialog_SymbolList", "&Diamond (d)", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_plus.setText(QtGui.QApplication.translate("Dialog_SymbolList", "&Plus (+)", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButton_None.setText(QtGui.QApplication.translate("Dialog_SymbolList", "&None (n)", None, QtGui.QApplication.UnicodeUTF8))

