import json
import time
import numpy as np
from PyQt5 import QtWebSockets
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject, QThread, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QWidget, QToolTip, QTextBrowser, QTextEdit, QPushButton, QSplitter, \
    QVBoxLayout, QHBoxLayout, QLabel
from pyqtgraph import GraphicsLayoutWidget

from nssproto import req, res


class ExevWrapper(QObject):
    train = pyqtSignal(object)
    test = pyqtSignal(object)
    grads = pyqtSignal(object)
    applying = pyqtSignal(object)
    evaluating = pyqtSignal()

    def __init__(self, EXEV, reg, bat, ckp_path, data_path, roomid):
        QObject.__init__(self)
        self.EXEV = EXEV
        self.reg = reg
        self.bat = bat
        self.ckp_path = ckp_path
        self.data_path = data_path
        self.roomid = roomid
        self.exev = self.EXEV(self.reg, self.bat, self.ckp_path, self.data_path, self.roomid)
        self.plotname = self.exev.getname()
        self.applying.conect(self.apply)
        self.evaluating.conect(self.evaluate)

    def apply(self, p=None):
        if p is None:
            p = self.exev.vec_params
        self.exev.apply(p)
        vec_grads, train_record = self.exev.extractor.send(None)
        self.train.emit(train_record)
        self.grads.emit(vec_grads)

    def evaluate(self):
        test_record = self.exev.evaluate()
        self.test.emit(test_record)


class ExevThread(QThread):
    train = pyqtSignal(object)
    test = pyqtSignal(object)
    grads = pyqtSignal(object)
    applying = pyqtSignal(object)
    evaluating = pyqtSignal()
    ready = pyqtSignal()

    def __init__(self, EXEV, reg, bat, ckp_path, data_path, roomid):
        QThread.__init__(self)
        self.EXEV = EXEV
        self.reg = reg
        self.bat = bat
        self.ckp_path = ckp_path
        self.data_path = data_path
        self.roomid = roomid
        self.plotname = None
        self.wrapper = None

    def run(self):
        self.wrapper = ExevWrapper(self.EXEV, self.reg, self.bat, self.ckp_path, self.data_path, self.roomid)
        self.wrapper.test.connect(self.testtransfer)
        self.wrapper.train.connect(self.traintransfer)
        self.wrapper.grads.connect(self.gradstransfer)
        self.plotname = self.wrapper.plotname
        self.ready.emit()
        self.applying.connect(self.wrapper.apply)
        self.evaluating.connect(self.wrapper.evaluate)
        self.exec_()

    def wrapperstart(self):
        self.wrapper.apply()

    def testtransfer(self, o):
        self.test.emit(o)

    def traintransfer(self, o):
        self.train.emit(o)

    def gradstransfer(self, o):
        self.grads.emit(o)


class Shower(GraphicsLayoutWidget):
    def __init__(self, name, mode):
        GraphicsLayoutWidget.__init__(self)
        self.name = name
        self.pcurve = dict()
        for n in self.name:
            p = self.addPlot(title='%s %s' % (n, mode))
            curve = p.plot(pen=(255, 255, 255, 200))
            self.pcurve.update({n: (p, curve)})
            self.nextRow()

    def update(self, data_dict):
        for key, val in data_dict.items():
            self.pcurve[key][1].setData(np.array(val))


class ShowerPanel(QWidget):
    test_rcv = pyqtSignal(object)
    train_rcv = pyqtSignal(object)

    def __init__(self, parent, plotname):
        super().__init__(parent=parent)
        self.filename = 'Shower'
        self.mainWindow = parent
        self.info = QLabel()
        self.train_shower = Shower(plotname, 'train')
        self.test_shower = Shower(plotname, 'test')
        self.train_rcv.connect(self.train_shower.update)
        self.test_rcv.connect(self.test_shower.update)
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout()
        layout.addWidget(self.info)
        layout.addWidget(self.train_shower)
        layout.addWidget(self.test_shower)
        self.setLayout(layout)

    @staticmethod
    def text():
        return ''


class Chatter(QWidget):
    signal = pyqtSignal()
    train = pyqtSignal(object)
    info = pyqtSignal(str)
    err = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.mainWindow = parent
        r = self.mainWindow.session.post('http://%s/getrequestuser/' % self.mainWindow.ipport)
        res = json.loads(r.content.decode('utf-8'))
        self.sendername = res['username'] + " " + res['nickname']
        self.username = res['username']
        self.user_lr = np.array(1)
        self.showerpanel = None
        self.initUI()
        r = self.mainWindow.session.post('http://%s/getroomchataddr/' % self.mainWindow.ipport,
                                         data={'roomid': self.mainWindow.roomid})
        res = json.loads(r.content.decode('utf-8'))
        addr = 'ws://' + res['chataddr']
        self.socket = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.socket.error.connect(self.error)
        self.socket.open(QUrl(addr))
        self.socket.textMessageReceived.connect(self.rcvTextMessage)
        self.socket.binaryMessageReceived.connect(self.rcvBinaryMessage)
        self.exevthread = ExevThread(EXEV, reg, bat, ckp_path, data_path, roomid)
        self.exevthread.start()
        self.exevthread.ready.connect(self.initexev)

    def initexev(self):
        self.showerpanel = ShowerPanel(self.exevthread.plotname, self.mainWindow)
        self.exevthread.train.connect(self.showerpanel.train_shower.update)
        self.exevthread.test.connect(self.showerpanel.test_shower.update)
        self.exevthread.grads.connect(self.sendBinaryMessage)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.evaluate)
        self.timer.start(tim * 1000)
        self.exevthread.wrapperstart()

    def close_socket(self):
        self.socket.close()

    def evaluate(self):
        self.exevthread.evaluating.emit()

    def rcvTextMessage(self, msg):
        self.textBR.insertHtml(msg)
        cursor = self.textBR.textCursor()
        pos = len(self.textBR.toPlainText())
        cursor.setPosition(pos)
        self.textBR.ensureCursorVisible()
        self.textBR.setTextCursor(cursor)

    def rcvBinaryMessage(self, buf):
        username, msgtype, msg, params, user_lr = req(buf)
        if msgtype == 'sync':
            self.exevthread.applying.emit(params)
        elif msgtype == 'roommemory':
            self.info.emit(msg)
        elif msgtype == 'roomerror':
            self.info.emit(msg)
            self.close_socket()

    def sendBinaryMessage(self, grads):
        nss_proto = res(
            self.username, 'gradient', '', grads, self.user_lr).SerializeToString()
        self.socket.sendBinaryMessage(nss_proto)

    def sendTextMessage(self, msg):
        self.socket.sendTextMessage(msg)

    def do_ping(self):
        self.socket.ping(b"fuck")

    def error(self, error_code):
        print("error code: {}".format(error_code))
        print(self.socket.errorString())
        self.socket.close()
        self.err.emit(self.socket.errorString())

    def getcodeviewinfo(self):
        r = self.mainWindow.session.post('http://%s/getnickbyroomid/' % self.mainWindow.ipport,
                                         data={'roomid': self.mainWindow.roomid})
        usernick = json.loads(r.content.decode('utf-8'))
        self.mbs = ''
        for key, val in usernick.items():
            self.mbs += '%s %s\n; ' % (key, val)

    def text(self):
        self.getcodeviewinfo()
        return self.mbs

    def initUI(self):
        QToolTip.setFont(QFont('微软雅黑', 12))
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.textBR = QTextBrowser(self)
        self.textBR.setFont(font)
        self.textBR.toPlainText()
        self.textBR.setStyleSheet('QTextBrowser{background-color:rgb(0,0,0)}')
        self.textEdit = QTextEdit("Talk sth", self)
        self.textEdit.setFont(font)
        self.textEdit.setStyleSheet('QTextEdit{background-color:rgb(0,0,0); color: white}')

        self.sendbtn = QPushButton('Send (Ctrl+Enter)', self)
        self.sendbtn.setFont(font)
        self.sendbtn.setStyleSheet(
            'QPushButton{padding-left: 10px; padding-right: 10px; padding-top: 5px; padding-bottom: 5px;}')
        self.refreshbtn = QPushButton('Refresh member status (Ctrl+R)', self)
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
        seq1 = QKeySequence(Qt.CTRL+Qt.Key_Return)
        self.sendbtn.setShortcut(seq1)
        seq2 = QKeySequence(Qt.CTRL+Qt.Key_R)
        self.refreshbtn.setShortcut(seq2)
        self.setLayout(vlayout)

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
        self.sendTextMessage(msg_final)
        self.textEdit.clear()
        self.textEdit.setFocus()

    def refreshbtn_clicked(self):
        r = self.mainWindow.session.post('http://%s/getrequestuser/' % self.mainWindow.ipport)
        res = json.loads(r.content.decode('utf-8'))
        self.sendername = res['username'] + " " + res['nickname']
        self.signal.emit()
