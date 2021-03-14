import json

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QVBoxLayout, QPushButton, QMessageBox


class Reserve(QDialog):

    def __init__(self, parent, session, ipport, *args, **kwargs):
        QDialog.__init__(self, parent, *args, **kwargs)
        self.session = session
        self.ipport = ipport
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.setupUI()

    def setupUI(self):
        label = QLabel('GPU type selection')
        reserve = QPushButton()
        reserve.setText('Reserve')
        reserve.clicked.connect(self.reserve)
        self.cbtype = QComboBox()
        r = self.session.get('http://%s/gputype/' % self.ipport)
        gputype = json.loads(r.content.decode('utf-8'))['gputype']
        self.cbtype.addItems(gputype)
        vlayout = QVBoxLayout()
        vlayout.addWidget(label, 0, Qt.AlignLeft)
        vlayout.addWidget(self.cbtype)
        vlayout.addWidget(reserve, 1, Qt.AlignCenter)
        self.setLayout(vlayout)

    def reserve(self):
        text = self.cbtype.currentText()
        data = {'gpu': text}
        r = self.session.post('http://%s/reserve/' % self.ipport, data=data, verify=False)
        if r.status_code < 400:
            QMessageBox.about(self, 'Message', 'GPU reservation success! '
                                               'We will locally build a new GPU work station '
                                               'according to this '
                                               'configuration within seven days!')
        else:
            QMessageBox.about(self, 'Message', 'GPU reservation failed! '
                                               'Please try again later!')
        self.close()
