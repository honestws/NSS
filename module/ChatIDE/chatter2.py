import json
import time

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QWidget, QToolTip, QTextBrowser, QTextEdit, QPushButton, QSplitter, QVBoxLayout, QHBoxLayout


class Chatter(QWidget):
    signal = pyqtSignal()
    to_socket = pyqtSignal(str)

    def __init__(self, session, ipport, roomid, parent=None):
        super().__init__(parent=parent)
        self.mainWindow = parent
        self.filename = 'chatter'
        self.session = session
        self.ipport = ipport
        self.roomid = roomid
        self.sendername = ''
        self.mbs = ''
        self.textBR = QTextBrowser(self)
        self.textEdit = QTextEdit("Talk sth", self)
        self.sendbtn = QPushButton('Send (Ctrl+Enter)', self)
        self.refreshbtn = QPushButton('Refresh member status (Ctrl+R)', self)
        self.initUI()

    def initUI(self):
        QToolTip.setFont(QFont('微软雅黑', 12))
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)

        self.textBR.setFont(font)
        self.textBR.toPlainText()
        self.textBR.setStyleSheet('QTextBrowser{background-color:rgb(0,0,0)}')
        self.textEdit.setFont(font)
        self.textEdit.setStyleSheet('QTextEdit{background-color:rgb(0,0,0); color: white}')

        self.sendbtn.setFont(font)
        self.sendbtn.setStyleSheet(
            'QPushButton{padding-left: 10px; padding-right: 10px; padding-top: 5px; padding-bottom: 5px;}')
        self.refreshbtn.setFont(font)
        self.refreshbtn.setStyleSheet(
            'QPushButton{padding-left: 10px; padding-right: 10px; padding-top: 5px; padding-bottom: 5px;}')
        self.refreshbtn.clicked.connect(self.refreshbtn_clicked)
        vsplitter = QSplitter(Qt.Vertical)
        vsplitter.addWidget(self.textBR)
        vsplitter.addWidget(self.textEdit)
        vsplitter.setSizes([200, 100])

        vlayout = QVBoxLayout()
        vlayout.addWidget(vsplitter)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.refreshbtn, 0, Qt.AlignLeft)
        hlayout.addWidget(self.sendbtn, 0, Qt.AlignRight)
        vlayout.addLayout(hlayout)

        self.sendbtn.clicked.connect(self.sendbtn_clicked)
        seq1 = QKeySequence(Qt.CTRL + Qt.Key_Return)
        self.sendbtn.setShortcut(seq1)
        seq2 = QKeySequence(Qt.CTRL + Qt.Key_R)
        self.refreshbtn.setShortcut(seq2)
        self.setLayout(vlayout)

    def msg_rcv(self, msg):
        self.textBR.insertHtml(msg)
        cursor = self.textBR.textCursor()
        pos = len(self.textBR.toPlainText())
        cursor.setPosition(pos)
        self.textBR.ensureCursorVisible()
        self.textBR.setTextCursor(cursor)

    def msg_send(self, msg):
        self.to_socket.emit(msg)

    def sendbtn_clicked(self):
        msg0 = self.textEdit.toPlainText().replace('\n', '<br>').replace(' ', '&nbsp;')
        if msg0.replace(' ', '') == '':
            self.textEdit.clear()
            self.textEdit.setFocus()
            return None
        msgtime = time.ctime()
        msg1_ch = "<font color='orange'>" + self.sendername + "</font>"  # name
        msgtime_ch = "<font color='orange'>" + msgtime + "</font>"  # time
        msg0_ch = "<font color='white'>" + msg0 + "</font>"  # message
        msg_final = "<br>" + msg1_ch + ' ' + msgtime_ch + "<br>" + msg0_ch
        self.msg_send(msg_final)
        self.textEdit.clear()
        self.textEdit.setFocus()

    def refreshbtn_clicked(self):
        r = self.session.post('http://%s/getrequestuser/' % self.ipport)
        res = json.loads(r.content.decode('utf-8'))
        self.sendername = res['username'] + " " + res['nickname']
        self.signal.emit()

    def getcodeviewinfo(self):
        r = self.session.post('http://%s/getnickbyroomid/' % self.ipport, data={'roomid': self.roomid})
        usernick = json.loads(r.content.decode('utf-8'))
        self.mbs = ''
        for key, val in usernick.items():
            self.mbs += '%s %s\n; ' % (key, val)

    def text(self):
        self.getcodeviewinfo()
        return self.mbs
