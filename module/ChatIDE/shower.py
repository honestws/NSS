import json
import sys
import pyqtgraph as pg
import numpy as np
from PyQt5 import QtWebSockets
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, QObject, QCoreApplication, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from pyqtgraph import GraphicsLayoutWidget
from nssproto import req, res
pg.setConfigOptions(antialias=True)


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


class Client(QObject):
    test = pyqtSignal(object)
    train = pyqtSignal(object)
    mem = pyqtSignal(str)
    err = pyqtSignal(str)

    def __init__(self, parent, session, ipport, roomid, exev, tim):
        QObject.__init__(self, parent)
        self.session = session
        self.ipport = ipport
        self.roomid = roomid
        self.exev = exev
        r = self.session.post('http://%s/getroomgradaddr/' % self.ipport,
                              data={'roomid': self.roomid})
        res = json.loads(r.content.decode('utf-8'))
        gradaddr = 'ws://' + res['gradaddr']
        self.gradsocket = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.gradsocket.error.connect(self.error)
        self.gradsocket.open(QUrl(gradaddr))
        self.gradsocket.binaryMessageReceived.connect(self.rcvBinaryMessage)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.evaluate)
        self.timer.start(tim * 1000)
        self.exev.extractor.send(None)

    def evaluate(self):
        test_record = self.exev.evaluate()
        self.test.emit(test_record)

    def rcvBinaryMessage(self, buf):
        username, msgtype, msg, params, user_lr = req(buf)
        if msgtype == 'sync':
            self.exev.apply(params)
            vec_grads, train_record = self.exev.extractor.send(None)
            self.train.emit(train_record)
            nss_proto = res(
                username, 'gradient', msg, vec_grads, user_lr).SerializeToString()
            self.gradsocket.sendBinaryMessage(nss_proto)
        elif msgtype == 'roommemory':
            self.mem.emit(msg)
        elif msgtype == 'roomerror':
            self.mem.emit(msg)
            self.close_socket()

    def error(self, error_code):
        print("error code: {}".format(error_code))
        print(self.gradsocket.errorString())
        self.gradsocket.close()
        self.err.emit(self.gradsocket.errorString())

    def close_socket(self):
        self.gradsocket.close()


class BackendThread(QThread):
    test = pyqtSignal(object)
    train = pyqtSignal(object)
    mem = pyqtSignal(str)
    err = pyqtSignal(str)

    def __init__(self, session, ipport, roomid, exev, tim):
        QThread.__init__(self)
        self.session = session
        self.ipport = ipport
        self.roomid = roomid
        self.exev = exev
        self.tim = tim

    def run(self):
        app = QCoreApplication(sys.argv)
        client = Client(app, self.session, self.ipport, self.roomid, self.exev, self.tim)
        client.test.connect(self.testtransfer)
        client.train.connect(self.traintransfer)
        client.mem.connect(self.memtransfer)
        client.err.connect(self.errtransfer)
        app.exec_()

    def testtransfer(self, o):
        self.test.emit(o)

    def traintransfer(self, o):
        self.train.emit(o)

    def memtransfer(self, s):
        self.mem.emit(s)

    def errtransfer(self, s):
        self.err.emit(s)


class ShowerPanel(QWidget):
    err = pyqtSignal(str)

    def __init__(self, parent, plotname, exev, tim, session, ipport, roomid):
        super().__init__(parent=parent)
        self.session = session
        self.ipport = ipport
        self.roomid = roomid
        self.exev = exev
        self.filename = 'Shower'
        self.mainWindow = parent
        self.info = QLabel()
        self.train_shower = Shower(plotname, 'train')
        self.test_shower = Shower(plotname, 'test')
        t = BackendThread(self.session, self.ipport, self.roomid, self.exev, tim)
        t.test.connect(self.testtransfer)
        t.train.connect(self.traintransfer)
        t.mem.connect(self.memtransfer)
        t.err.connect(self.errtransfer)
        t.start()
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

    def testtransfer(self, o):
        self.test_shower.update(o)

    def traintransfer(self, o):
        self.train_shower.update(o)

    def memtransfer(self, s):
        self.info.setText(s)

    def errtransfer(self, s):
        self.err.emit(s)
