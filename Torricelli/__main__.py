import sys
from PyQt5.QtWidgets import QApplication
from Torricelli import Torricelli

app = QApplication(sys.argv)
myapp = Torricelli()
myapp.show()
sys.exit(app.exec_())
