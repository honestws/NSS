import json
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QDialog, \
    QComboBox, QMessageBox, QVBoxLayout, QHBoxLayout


class FileDownload(QDialog):
    def __init__(self, parent, session, room_dict, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)
        self.session = session
        self.room_dict = room_dict
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.resize(200, 100)
        self.setupUI()

    def setupUI(self):
        cb = QLabel('Room ID')
        self.room = QComboBox()
        self.room.addItems(list(self.room_dict.keys()))

        submitbtn = QPushButton()
        submitbtn.setText('Download')
        submitbtn.clicked.connect(self.download)

        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addWidget(cb, Qt.AlignRight)
        hlayout.addWidget(self.room, Qt.AlignLeft)
        vlayout.addLayout(hlayout)
        vlayout.addWidget(submitbtn, 2, Qt.AlignCenter)
        self.setLayout(vlayout)

    def download(self):
        room = self.room.currentText()
        row_items = self.room_dict[room]
        roomid = row_items['roomid']
        gpuid = row_items['gpuid']
        r = self.session.post('http://127.0.0.1:8000/getgpuipportbygpuid/',
                              data={'gpuid': gpuid})
        res = json.loads(r.content.decode('utf-8'))
        gpuip = res['ip']
        port = res['port']

        dirname, _ = os.path.split(os.path.abspath(sys.argv[0]))
        path = os.path.join(dirname, 'configs')
        room = self.room.currentText()
        path = os.path.join(path, room)
        os.makedirs(path, mode=0o777, exist_ok=True)
        filename = os.path.join(path, room + '.py')

        r = self.session.get(
            'http://' + gpuip + ':' + port + '/downloadfile/?roomid=%s' % roomid)
        res = json.loads(r.content.decode('utf-8'))
        if r.status_code < 400 and res.get('status'):
            QMessageBox.about(self, 'Message', "Download success! This python file"
                                               " will be downloaded to the 'configs' folder under "
                                               "the NSS main directory.")
        else:
            QMessageBox.about(self, 'Message', 'Download failed! Please try again later!')
            self.close()
            return None
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        self.close()
