import json
import os
import sys
import time
import zipfile
import math
from shutil import copy

import requests
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QDialog, QFileDialog, \
    QComboBox, QMessageBox
from requests_toolbelt import MultipartEncoderMonitor, MultipartEncoder


class BackendThread(QThread):
    signal = pyqtSignal(str)
    visible_signal = pyqtSignal()

    def __init__(self, session, ipport, src_path, dst_path, size, price, mbsize,
                 username, description, cbtype, filename):
        QThread.__init__(self)
        self.session = session
        self.ipport = ipport
        self.src_path = src_path
        self.dst_path = dst_path
        self.size = size
        self.price = price
        self.mbsize = mbsize
        self.username = username
        self.description = description
        self.cbtype = cbtype
        self.filename = filename

    def run(self):
        def callback(monitor):
            self.signal.emit('Upload percentage %.2f' % (monitor.bytes_read / self.size * 100) + '%')

        e = MultipartEncoder(
            fields={'price': self.price, 'size': str(self.mbsize), 'username': self.username,
                    'description': self.description, 'type': self.cbtype,
                    'data': (self.filename, open(self.src_path, 'rb'), 'application/octet-stream')}
        )
        m = MultipartEncoderMonitor(e, callback)
        r = self.session.get('http://%s/getdatasetserveripport/' % self.ipport)
        ipport = json.loads(r.content.decode('utf-8'))['ipport']
        r = requests.post(
            'http://%s/datasetrcv/' % ipport, data=m,
            headers={'Content-Type': m.content_type})
        copy(self.src_path, self.dst_path)
        filename = os.path.join(self.dst_path, os.path.basename(self.src_path))
        path = os.path.splitext(filename)[0]
        os.makedirs(path, mode=0o777, exist_ok=True)
        zf = zipfile.ZipFile(filename)
        uncompress_size = sum((file.file_size for file in zf.infolist()))
        extracted_size = 0

        for file in zf.infolist():
            extracted_size += file.file_size
            self.signal.emit('Extraction percentage %.2f' % (extracted_size * 100 / uncompress_size) + '%')
            zf.extract(file, path=path)
        self.visible_signal.emit()


class Upload(QDialog):
    signal = pyqtSignal(str)
    visible_signal = pyqtSignal()

    def __init__(self, parent, session, ipport, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)
        self.session = session
        self.ipport = ipport
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        dirname, _ = os.path.split(os.path.abspath(sys.argv[0]))
        self.path = os.path.join(dirname, 'downloads')
        os.makedirs(self.path, mode=0o777, exist_ok=True)
        self.setupUI()

    def setupUI(self):
        select = QPushButton()
        select.setText('Select')
        select.setToolTip('The dataset name is set as the upload filename by default')
        select.clicked.connect(self.select)
        cb = QLabel('Type selection')
        self.cbtype = QComboBox()
        r = self.session.get('http://%s/datasettype/' % self.ipport)
        datasettype = json.loads(r.content.decode('utf-8'))['datasettype']
        self.cbtype.addItems(datasettype)
        price = QLabel('Price (RMB)')
        price.setToolTip('0.00-99.99 RMB')
        description = QLabel('Description')

        self.dataset = QLineEdit()
        self.priceedit = QLineEdit()
        pDoubleValidator = QDoubleValidator()
        pDoubleValidator.setRange(0, 10)
        pDoubleValidator.setNotation(QDoubleValidator.StandardNotation)
        pDoubleValidator.setDecimals(2)
        self.priceedit.setValidator(pDoubleValidator)
        self.descriptionedit = QTextEdit()

        submitbtn = QPushButton()
        submitbtn.setText('Submit')
        submitbtn.clicked.connect(self.submit)

        grid = QGridLayout()
        grid.setSpacing(5)

        grid.addWidget(select, 0, 0, Qt.AlignRight)
        grid.addWidget(self.dataset, 0, 1)

        grid.addWidget(cb, 1, 0, Qt.AlignRight)
        grid.addWidget(self.cbtype, 1, 1)

        grid.addWidget(price, 2, 0, Qt.AlignRight)
        grid.addWidget(self.priceedit, 2, 1)

        grid.addWidget(description, 3, 0, Qt.AlignRight)
        grid.addWidget(self.descriptionedit, 3, 1, 40, 1)

        grid.addWidget(submitbtn, 4, 0, 40, 1)

        self.setLayout(grid)

    def submit(self):
        path = self.dataset.text()
        price = self.priceedit.text()
        description = self.descriptionedit.toPlainText()
        cbtype = self.cbtype.currentText()

        if path == '' or price == '' or description == '':
            QMessageBox.about(self, 'Message', 'Required fields are empty!')
            return None

        datasetname = os.path.basename(path).split('.')[0]
        filename = os.path.basename(path)
        size = os.path.getsize(path)
        mbsize = size/(1024 * 1024)
        m = math.ceil(mbsize)

        r = self.session.post(
            'http://%s/preupload/' % self.ipport, data={'datasetname': datasetname, 'money': m + float(price)},
            verify=False)
        status = json.loads(r.content.decode('utf-8'))['status']

        if r.status_code < 400 and status == 0:
            QMessageBox.about(self, 'Message', 'The dataset name is set as the upload filename by default, '
                                               'and the dataset name already exists! Please change the file name!')
            return None
        elif r.status_code < 400 and status == -1:
            QMessageBox.about(
                self, 'Message', 'Insufficient account balance, '
                                 'you need to pay %.0f + %.0f = %.0f RMB for the dataset storage (1 RMB/MB)!'
                                 'Please go to the account center to recharge! '
                                 'After the dataset review, we will deduct the storage fee!' %
                                 (m, float(price), m + float(price)))
            return None

        reply = QMessageBox.question(self, 'Provision',
                                     'The unique copyright of the dataset will be transferred to NSS for sale. '
                                     'Thereafter, the dataset author is not allowed to'
                                     ' transfer the copyright to other sellers. '
                                     'If you do not agree to this provision, please click Cancel.',
                                     QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

        if reply == QMessageBox.Cancel:
            return None
        else:
            r = self.session.post('http://%s/getrequestuser/' % self.ipport)
            username = str(json.loads(r.content.decode('utf-8'))['username'])
            t = BackendThread(self.session, self.ipport, path, self.path,
                              size, price, mbsize, username, description, cbtype, filename)
            t.signal.connect(self.signaltransfer)
            t.visible_signal.connect(self.visiblesignaltransfer)
            t.start()
            time.sleep(0.5)
        self.close()

    def signaltransfer(self, msg):
        self.signal.emit(msg)

    def visiblesignaltransfer(self):
        self.visible_signal.emit()

    def select(self):
        os.makedirs(self.path, mode=0o777, exist_ok=True)
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', self.path, 'zip file(*.zip)')
        self.dataset.setText(fname)


class FileUpload(QDialog):
    def __init__(self, parent, session, room_dict, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)
        self.session = session
        self.room_dict = room_dict
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.setupUI()

    def setupUI(self):
        select = QPushButton()
        select.setText('Select')
        select.setToolTip('Select config.py to upload to the room')
        select.clicked.connect(self.select)
        cb = QLabel('Room ID')
        self.room = QComboBox()
        self.room.addItems(list(self.room_dict.keys()))

        self.path = QLineEdit()

        submitbtn = QPushButton()
        submitbtn.setText('Submit')
        submitbtn.clicked.connect(self.submit)

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.addWidget(cb, 0, 0, Qt.AlignRight)
        grid.addWidget(self.room, 0, 1)
        grid.addWidget(select, 1, 0, Qt.AlignRight)
        grid.addWidget(self.path, 1, 1)
        grid.addWidget(submitbtn, 2, 0, 1, 2, Qt.AlignCenter)
        self.setLayout(grid)

    def submit(self):
        path = self.path.text()
        room = self.room.currentText()

        if path == '':
            QMessageBox.about(self, 'Message', 'Required fields are empty!')
            return None

        e = MultipartEncoder(
            fields={'room': room,
                    'data': (room + '.py', open(path, 'rb'), 'application/octet-stream')}
        )

        m = MultipartEncoderMonitor(e, lambda monitor: monitor)

        row_items = self.room_dict[room]
        gpuid = row_items['gpuid']
        r = self.session.post('http://127.0.0.1:8000/getgpuipportbygpuid/',
                              data={'gpuid': gpuid})
        res = json.loads(r.content.decode('utf-8'))
        gpuip = res['ip']
        port = res['port']

        r = self.session.post(
            'http://' + gpuip + ':' + port + '/filercv/', data=m, headers={'Content-Type': m.content_type})
        status = json.loads(r.content.decode('utf-8'))['status']
        if r.status_code < 400 and status:
            QMessageBox.about(self, 'Message', 'Upload success!')
        else:
            QMessageBox.about(self, 'Message', 'Upload failed! Please try again later!')
        self.close()

    def select(self):
        dirname, _ = os.path.split(os.path.abspath(sys.argv[0]))
        path = os.path.join(dirname, 'configs')
        room = self.room.currentText()
        path = os.path.join(path, room)
        os.makedirs(path, mode=0o777, exist_ok=True)
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', path, '.', 'python file(*.py)')
        self.path.setText(fname)
