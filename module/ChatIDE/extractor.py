import json
from PyQt5 import QtWebSockets
from PyQt5.QtCore import pyqtSignal, QUrl, QObject, QTimer
from nssproto import req, res


class Extractor(QObject):
    trainrecord = pyqtSignal(object)
    testrecord = pyqtSignal(object)
    err = pyqtSignal(str)
    roommemory = pyqtSignal(str)

    def __init__(self, parent, exev, tim, session, ipport, roomid):
        QObject.__init__(self, parent)
        self.exev = exev
        self.session = session
        self.ipport = ipport
        self.roomid = roomid
        r = self.session.post('http://%s/getroomgradaddr/' % self.ipport,
                              data={'roomid': self.roomid})
        res = json.loads(r.content.decode('utf-8'))
        gradaddr = 'ws://' + res['gradaddr']
        self.gradsocket = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.gradsocket.error.connect(self.error)
        self.gradsocket.binaryMessageReceived.connect(self.rcvBinaryMessage)
        self.gradsocket.open(QUrl(gradaddr))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.evaluate)
        self.timer.start(tim*1000)

    def evaluate(self):
        test_record = self.exev.evaluate()
        self.testrecord.emit(test_record)

    def rcvBinaryMessage(self, buf):
        username, msgtype, msg, params, user_lr = req(buf)
        if msgtype == 'sync':
            self.exev.apply(params)
            vec_grads, train_record = self.exev.extractor.send(None)
            self.trainrecord.emit(train_record)
            nss_proto = res(
                username, 'gradient', msg, vec_grads, user_lr).SerializeToString()
            self.gradsocket.sendBinaryMessage(nss_proto)
        elif msgtype == 'roommemory':
            self.roommemory.emit(msg)
        elif msgtype == 'roomerror':
            self.err.emit(msg)
            self.close_socket()

    def error(self, error_code):
        print("error code: {}".format(error_code))
        print(self.gradsocket.errorString())
        self.err.emit(self.gradsocket.errorString())

    def close_socket(self):
        self.gradsocket.close()
