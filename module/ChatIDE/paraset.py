from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QDialog, QPushButton, QLabel, QLineEdit, QGridLayout


class ParameterSetting(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.reg = 0.0005
        self.bat = 32
        self.tim = 600
        self.setupUI()

    def setupUI(self):
        ok = QPushButton()
        ok.setText('OK')
        ok.clicked.connect(self.confirm)
        reg = QLabel('Regularization coefficient:')
        batch_size = QLabel('Batch size:')
        time_interval = QLabel('Time interval (s):')
        self.regedit = QLineEdit()
        self.regedit.setText(str(self.reg))
        self.batch_size = QLineEdit()
        self.batch_size.setText(str(self.bat))
        self.time_interval = QLineEdit()
        self.time_interval.setText(str(self.tim))
        pDoubleValidator = QDoubleValidator()
        pDoubleValidator.setRange(0, 1)
        pDoubleValidator.setNotation(QDoubleValidator.StandardNotation)
        pDoubleValidator.setDecimals(5)
        self.regedit.setValidator(pDoubleValidator)
        pIntValidator = QIntValidator()
        pIntValidator.setRange(0, 1000)
        self.batch_size.setValidator(pIntValidator)
        self.time_interval.setValidator(pIntValidator)

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.addWidget(reg, 0, 0, Qt.AlignRight)
        grid.addWidget(self.regedit, 0, 1)
        grid.addWidget(batch_size, 1, 0, Qt.AlignRight)
        grid.addWidget(self.batch_size, 1, 1)
        grid.addWidget(time_interval, 2, 0, Qt.AlignRight)
        grid.addWidget(self.time_interval, 2, 1)
        grid.addWidget(ok, 3, 0, 1, 2, Qt.AlignCenter | Qt.AlignBottom)
        self.setLayout(grid)

    def confirm(self):
        self.close()

    def closeEvent(self, event):
        self.reg = float(self.regedit.text()) if self.regedit.text().strip() != '' else self.reg
        self.bat = int(self.batch_size.text()) if self.batch_size.text().strip() != '' else self.bat
        self.tim = int(self.time_interval.text()) if self.time_interval.text().strip() != '' else self.tim
        event.accept()

