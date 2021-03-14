import json

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QDialog, QMessageBox


class NickName(QDialog):
    signal = pyqtSignal()

    def __init__(self, parent, session, ipport, name, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)
        self.session = session
        self.ipport = ipport
        self.name = name
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.setupUI()

    def setupUI(self):
        user = QLabel('Username')
        self.name = QLabel('%s' % self.name)
        nick = QLabel('Nickname')
        self.edit = QLineEdit()

        submitbtn = QPushButton()
        submitbtn.setText('Submit')
        submitbtn.clicked.connect(self.submit)

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.addWidget(user, 0, 0, Qt.AlignRight)
        grid.addWidget(self.name, 0, 1)
        grid.addWidget(nick, 1, 0, Qt.AlignRight)
        grid.addWidget(self.edit, 1, 1)
        grid.addWidget(submitbtn, 2, 0, 1, 2, Qt.AlignCenter | Qt.AlignBottom)
        self.setLayout(grid)

    def submit(self):
        username = self.name.text().split(' ')[0]
        nickname = self.edit.text()

        if nickname == '':
            QMessageBox.about(self, 'Message', 'Required fields are empty!')
            return None

        r = self.session.post(
            'http://%s/setnickname/' % self.ipport, data={'username': username, 'nickname': nickname}, verify=False)
        status = json.loads(r.content.decode('utf-8'))['status']
        if status == 1:
            QMessageBox.about(self, 'Message', 'Nickname revised successfully!')
            self.signal.emit()
        elif status == 0:
            QMessageBox.about(self, 'Message', 'Network request error! Please try again later!')
        self.close()
