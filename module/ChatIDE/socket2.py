import json

import numpy as np
from PyQt5 import QtWebSockets
from PyQt5.QtCore import QUrl, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox

from nssproto import res, req


class NssGradSocket(QWidget):
    to_shower_panel = pyqtSignal(str)

    def __init__(self, parent, session, ipport, roomid, para_queue):
        QWidget.__init__(self, parent)
        self.para_queue = para_queue[0]
        self.p = parent
        r = session.post('http://%s/getrequestuser/' % ipport)
        re = json.loads(r.content.decode('utf-8'))
        self.username = re['username']
        self.msg = 'ini'
        self.user_lr = np.array([[-1.]])
        r = session.post('http://%s/getroomgradaddr/' % ipport, data={'roomid': roomid})
        re = json.loads(r.content.decode('utf-8'))
        addr = 'ws://' + re['addr']
        self.socket = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.socket.error.connect(self.error)
        self.socket.open(QUrl(addr))
        self.socket.binaryMessageReceived.connect(self.rcvBinaryMessage)

    def rcvBinaryMessage(self, buf):
        username, msgtype, msg, params, user_lr = req(buf)
        if msgtype == 'sync':
            self.para_queue.put(params)
        elif msgtype == 'roomstatus':
            self.to_shower_panel.emit(msg)
        elif msgtype == 'roomclosed':
            QMessageBox.about(self.p, 'Message', msg)
        elif msgtype == 'roomerror':
            QMessageBox.about(self.p, 'Message', msg)

    def sendBinaryMessage(self, g):
        nss_proto = res(
            self.username, 'gradient', self.msg, g[0], g[1]).SerializeToString()
        self.socket.sendBinaryMessage(nss_proto)
        self.msg = ''

    def do_ping(self):
        self.socket.ping(b"fuck")

    def error(self, error_code):
        QMessageBox.about(self.p, 'Message', self.socket.errorString())
        self.socket.close()

    def close_socket(self):
        self.socket.close()


class NssChatSocket(QWidget):
    to_chatter = pyqtSignal(str)

    def __init__(self, parent, session, ipport, roomid):
        QWidget.__init__(self, parent)
        self.p = parent
        r = session.post('http://%s/getroomchataddr/' % ipport, data={'roomid': roomid})
        re = json.loads(r.content.decode('utf-8'))
        addr = 'ws://' + re['addr']
        self.socket = QtWebSockets.QWebSocket("", QtWebSockets.QWebSocketProtocol.Version13, None)
        self.socket.error.connect(self.error)
        self.socket.open(QUrl(addr))
        self.socket.textMessageReceived.connect(self.rcvTextMessage)

    def rcvTextMessage(self, msg):
        self.to_chatter.emit(msg)
        # self.textBR.insertHtml(msg)
        # cursor = self.textBR.textCursor()
        # pos = len(self.textBR.toPlainText())
        # cursor.setPosition(pos)
        # self.textBR.ensureCursorVisible()
        # self.textBR.setTextCursor(cursor)

    def sendTextMessage(self, msg):
        self.socket.sendTextMessage(msg)

    def do_ping(self):
        self.socket.ping(b"fuck")

    def error(self, error_code):
        print("error code: {}".format(error_code))
        # print(self.socket.errorString())
        self.socket.close()

    def close_socket(self):
        self.socket.close()