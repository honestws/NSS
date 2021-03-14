import json
import os
import platform
import re
import sys
import time
import zipfile
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QBrush, QColor
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, \
    QMessageBox, QLabel, QMenu

from ide import NSSChatIDE
from module import upload, reserve
from module.download import FileDownload
from module.roomadd import RoomAdd
from module.roomedit import RoomEdit
from module.roomremove import RoomRemove
from module.upload import FileUpload


class DownloadThread(QThread):
    def __init__(self, datasetname, session, ipport, filename, pay):
        QThread.__init__(self)
        self.datasetname = datasetname
        self.session = session
        self.ipport = ipport
        r = self.session.get('http://%s/datasetsize/?datasetname=%s' % (self.ipport, self.datasetname))
        self.file_total = json.loads(r.content.decode('utf-8'))['size']
        self.filename = filename
        self.pay = pay

    def run(self):
        r = self.session.get('http://%s/getdatasetserveripport/' % self.ipport)
        ipport = json.loads(r.content.decode('utf-8'))['ipport']
        r = self.session.post('http://%s/getrequestuser/' % self.ipport)
        username = json.loads(r.content.decode('utf-8'))['username']
        r = self.session.get('http://%s/downloaddataset/?datasetname=%s&pay=%f&username=%s' % (
            ipport, self.datasetname, self.pay, username),
                             stream=True)
        with open(self.filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)


class DownloadMinitorThread(QThread):
    signal = pyqtSignal(str)
    visible_signal = pyqtSignal()

    def __init__(self, filename, file_total):
        QThread.__init__(self)
        self.filename = filename
        self.file_total = file_total

    def run(self):
        file_size = 0
        # self.percent.setText('Download percentage 0.00%')
        while file_size < self.file_total:
            time.sleep(1)
            if os.path.exists(self.filename):
                file_size = os.path.getsize(self.filename)
            self.signal.emit('Download percentage %.2f' % (file_size/self.file_total*100) + '%')
        path = os.path.splitext(self.filename)[0]
        os.makedirs(path, mode=0o777, exist_ok=True)
        zf = zipfile.ZipFile(self.filename)
        uncompress_size = sum((file.file_size for file in zf.infolist()))
        extracted_size = 0

        for file in zf.infolist():
            extracted_size += file.file_size
            self.signal.emit('Extraction percentage %.2f' % (extracted_size * 100 / uncompress_size) + '%')
            zf.extract(file, path=path)
        self.visible_signal.emit()


class TabWidgetStore(QtWidgets.QTabWidget):
    def __init__(self, session, ipport, *args, **kwargs):
        QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
        self.session = session
        self.chat_IDE = None
        self.ipport = ipport
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.percent = QLabel()
        self.percent.setVisible(False)

        self.history_items = None
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        self.addTab(self.tab1, '选项卡1')
        self.addTab(self.tab2, '选项卡2')
        self.addTab(self.tab3, '选项卡3')

        self.tab1UI()
        self.tab2UI()
        self.tab3UI()

    def tab1UI(self):
        r = self.session.get('http://%s/getdatasets/' % self.ipport)
        self.data_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        num = len(self.data_dict)
        self.tablewidget_data = QTableWidget()
        self.tablewidget_data.setRowCount(num)
        self.tablewidget_data.setColumnCount(7)
        self.tablewidget_data.setColumnWidth(0, 120)
        self.tablewidget_data.setColumnWidth(3, 140)
        self.tablewidget_data.setColumnWidth(5, 140)
        self.tablewidget_data.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.tablewidget_data.setHorizontalHeaderLabels(
            ['Dataset name', 'Status', 'Size', 'Type', 'Price', 'Download count', 'Operation'])
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.tablewidget_data.setFont(font)
        self.tablewidget_data.doubleClicked.connect(self.select_data)
        self.tablewidget_data.itemClicked.connect(self.download)

        if r.status_code < 400:
            for idx, (key, val) in self.data_dict:

                item0 = QTableWidgetItem(key.split('.')[0])
                item0.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['verified'] == 0:
                    item1 = QTableWidgetItem('In review')
                elif val['verified'] == 1:
                    item1 = QTableWidgetItem('Available')
                elif val['varified'] == -1:
                    item1 = QTableWidgetItem('Unavailable')

                item1.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item2 = QTableWidgetItem('%.2f MB' % val['size'])
                item2.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item3 = QTableWidgetItem(str(val['cbtype']))
                item3.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item3.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item4 = QTableWidgetItem('%.2f RMB' % val['price'])
                item4.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item4.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item5 = QTableWidgetItem(str(val['times']))
                item5.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item5.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['verified'] == 1:
                    item6 = QTableWidgetItem('Download')
                else:
                    item6 = QTableWidgetItem('---')

                item6.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item6.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                self.tablewidget_data.setItem(idx, 0, item0)
                self.tablewidget_data.setItem(idx, 1, item1)
                self.tablewidget_data.setItem(idx, 2, item2)
                self.tablewidget_data.setItem(idx, 3, item3)
                self.tablewidget_data.setItem(idx, 4, item4)
                self.tablewidget_data.setItem(idx, 5, item5)
                self.tablewidget_data.setItem(idx, 6, item6)

        self.edit_data = QLineEdit()
        searchbtn = QPushButton()
        searchbtn.clicked.connect(self.search_data)
        searchbtn.setIcon(QIcon("images/search.png"))
        uploadbtn = QPushButton()
        uploadbtn.clicked.connect(self.upload)
        uploadbtn.setIcon(QIcon("images/upload.png"))
        uploadbtn.setToolTip('Upload a dataset')
        refreshbtn = QPushButton()
        refreshbtn.clicked.connect(self.refresh_data_list)
        refreshbtn.setIcon(QIcon("images/refresh.png"))
        refreshbtn.setToolTip('Refresh data list')
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.edit_data, 0, Qt.AlignLeft)
        hlayout.addWidget(searchbtn, 1, Qt.AlignLeft)
        hlayout.addWidget(uploadbtn, 0, Qt.AlignLeft)
        hlayout.addWidget(refreshbtn, 0, Qt.AlignLeft)

        layout = QVBoxLayout()
        layout.addLayout(hlayout)
        layout.addWidget(self.tablewidget_data)
        layout.addWidget(self.percent, 0, Qt.AlignLeft)
        self.setTabText(0, 'Data')
        self.setTabIcon(0, QIcon('images/data.png'))
        self.tab1.setLayout(layout)
        self.tab1.show()

    def tab2UI(self):
        r = self.session.get('http://%s/getgpus/' % self.ipport)
        self.gpu_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        num = len(self.gpu_dict)
        self.tablewidget_gpu = QTableWidget()
        self.tablewidget_gpu.setRowCount(num)
        self.tablewidget_gpu.setColumnCount(9)
        self.tablewidget_gpu.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.tablewidget_gpu.setHorizontalHeaderLabels(
            ['GPU ID', 'GPU type', 'Memory', 'Price', 'Master', 'Status', 'Location',
             'Creation date', 'expiration date'])
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.tablewidget_gpu.setFont(font)
        self.tablewidget_gpu.setColumnWidth(1, 120)
        self.tablewidget_gpu.setColumnWidth(3, 120)
        self.tablewidget_gpu.setColumnWidth(4, 120)
        self.tablewidget_gpu.setColumnWidth(7, 140)
        self.tablewidget_gpu.setColumnWidth(8, 140)
        self.tablewidget_gpu.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tablewidget_gpu.customContextMenuRequested.connect(self.menu_gpu)

        if r.status_code < 400:
            for idx, (key, val) in self.gpu_dict:
                item0 = QTableWidgetItem(key)
                item0.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item1 = QTableWidgetItem(val['gputype'])
                item1.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item2 = QTableWidgetItem('%.f MB' % val['memory'])
                item2.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item3 = QTableWidgetItem('%.2f RMB' % val['price'])
                item3.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item3.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item4 = QTableWidgetItem(val['master'])
                item4.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item4.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['status'] == 0:
                    item5 = QTableWidgetItem('Reserved')
                else:
                    item5 = QTableWidgetItem('Available')

                item5.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item5.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['location'] == ', , , ':
                    item6 = QTableWidgetItem('---')
                else:
                    item6 = QTableWidgetItem(re.sub('^,', '', val['location']))
                item6.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item6.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item7 = QTableWidgetItem(val['ctime'])
                item7.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item7.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item8 = QTableWidgetItem(val['etime'])
                item8.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item8.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                self.tablewidget_gpu.setItem(idx, 0, item0)
                self.tablewidget_gpu.setItem(idx, 1, item1)
                self.tablewidget_gpu.setItem(idx, 2, item2)
                self.tablewidget_gpu.setItem(idx, 3, item3)
                self.tablewidget_gpu.setItem(idx, 4, item4)
                self.tablewidget_gpu.setItem(idx, 5, item5)
                self.tablewidget_gpu.setItem(idx, 6, item6)
                self.tablewidget_gpu.setItem(idx, 7, item7)
                self.tablewidget_gpu.setItem(idx, 8, item8)

        title = QLabel()
        title.setText('GPU work station list')
        reservebtn = QPushButton()
        reservebtn.clicked.connect(self.reserve)
        reservebtn.setIcon(QIcon("images/reserve.png"))
        reservebtn.setToolTip('Reserve a work station')
        refreshbtn = QPushButton()
        refreshbtn.clicked.connect(self.refresh_gpu_list)
        refreshbtn.setIcon(QIcon("images/refresh.png"))
        refreshbtn.setToolTip('Refresh work station list')
        hlayout = QHBoxLayout()
        hlayout.addWidget(title, Qt.AlignLeft)
        hlayout.addWidget(reservebtn, 0, Qt.AlignRight)
        hlayout.addWidget(refreshbtn, 0, Qt.AlignRight)

        layout = QVBoxLayout()
        layout.addLayout(hlayout)
        layout.addWidget(self.tablewidget_gpu)
        self.setTabText(1, 'GPU')
        self.setTabIcon(1, QIcon('images/GPU.png'))
        self.tab2.setLayout(layout)

    def tab3UI(self):
        r = self.session.get('http://%s/getroomsbymember/' % self.ipport)
        self.room_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))

        num = len(self.room_dict)
        self.tablewidget_room = QTableWidget()
        self.tablewidget_room.setRowCount(num)
        self.tablewidget_room.setColumnCount(7)
        self.tablewidget_room.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.tablewidget_room.setHorizontalHeaderLabels(
            ['Room ID', 'Max memory', 'Number of members', 'GPU ID', 'Status', 'Dataset name', 'Your location'])
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.tablewidget_room.setFont(font)
        self.tablewidget_room.setColumnWidth(0, 150)
        self.tablewidget_room.setColumnWidth(1, 150)
        self.tablewidget_room.setColumnWidth(2, 150)
        self.tablewidget_room.setColumnWidth(3, 150)
        self.tablewidget_room.doubleClicked.connect(self.enter_room)

        if r.status_code < 400:
            for idx, (key, val) in self.room_dict:
                item0 = QTableWidgetItem(key)
                item0.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item1 = QTableWidgetItem('%.f MB' % val['max_memory'])
                item1.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item2 = QTableWidgetItem(str(val['num_members']))
                item2.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item3 = QTableWidgetItem('G%010d' % val['gpuid'])
                item3.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item3.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['status']:
                    item4 = QTableWidgetItem('Running')
                else:
                    item4 = QTableWidgetItem('Suspending')

                item4.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item4.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item5 = QTableWidgetItem(val['datasetname'])
                item5.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item5.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item6 = QTableWidgetItem()
                item6.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item6.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if key == val['location']:
                    item6.setIcon(QIcon('./images/location.png'))

                self.tablewidget_room.setItem(idx, 0, item0)
                self.tablewidget_room.setItem(idx, 1, item1)
                self.tablewidget_room.setItem(idx, 2, item2)
                self.tablewidget_room.setItem(idx, 3, item3)
                self.tablewidget_room.setItem(idx, 4, item4)
                self.tablewidget_room.setItem(idx, 5, item5)
                self.tablewidget_room.setItem(idx, 6, item6)

        title = QLabel()
        title.setText('Room list')
        refreshbtn = QPushButton()
        refreshbtn.clicked.connect(self.refresh_room_list)
        refreshbtn.setIcon(QIcon("images/refresh.png"))
        refreshbtn.setToolTip('Refresh room list')
        hlayout = QHBoxLayout()
        hlayout.addWidget(title, Qt.AlignLeft)
        hlayout.addWidget(refreshbtn, 0, Qt.AlignRight)

        layout = QVBoxLayout()
        layout.addLayout(hlayout)
        layout.addWidget(self.tablewidget_room)

        self.setTabText(2, 'Room')
        self.setTabIcon(2, QIcon('images/room.png'))
        self.tab3.setLayout(layout)

    def refresh_data_list(self):
        r = self.session.get('http://%s/getdatasets/' % self.ipport)
        self.data_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        num = len(self.data_dict)
        self.tablewidget_data.setRowCount(num)
        if r.status_code < 400:
            for idx, (key, val) in self.data_dict:

                item0 = QTableWidgetItem(key.split('.')[0])
                item0.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['verified'] == 0:
                    item1 = QTableWidgetItem('In review')
                elif val['verified'] == 1:
                    item1 = QTableWidgetItem('Available')
                elif val['varified'] == -1:
                    item1 = QTableWidgetItem('Unavailable')

                item1.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item2 = QTableWidgetItem('%.2f MB' % val['size'])
                item2.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item3 = QTableWidgetItem(str(val['cbtype']))
                item3.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item3.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item4 = QTableWidgetItem('%.2f RMB' % val['price'])
                item4.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item4.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item5 = QTableWidgetItem(str(val['times']))
                item5.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item5.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['verified'] == 1:
                    item6 = QTableWidgetItem('Download')
                else:
                    item6 = QTableWidgetItem('---')

                item6.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item6.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                self.tablewidget_data.setItem(idx, 0, item0)
                self.tablewidget_data.setItem(idx, 1, item1)
                self.tablewidget_data.setItem(idx, 2, item2)
                self.tablewidget_data.setItem(idx, 3, item3)
                self.tablewidget_data.setItem(idx, 4, item4)
                self.tablewidget_data.setItem(idx, 5, item5)
                self.tablewidget_data.setItem(idx, 6, item6)

    def refresh_gpu_list(self):
        r = self.session.get('http://%s/getgpus/' % self.ipport)
        self.gpu_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        num = len(self.gpu_dict)
        self.tablewidget_gpu.setRowCount(num)

        if r.status_code < 400:
            for idx, (key, val) in self.gpu_dict:
                item0 = QTableWidgetItem(key)
                item0.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item1 = QTableWidgetItem(val['gputype'])
                item1.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item2 = QTableWidgetItem('%.f MB' % val['memory'])
                item2.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item3 = QTableWidgetItem('%.2f RMB' % val['price'])
                item3.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item3.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item4 = QTableWidgetItem(val['master'])
                item4.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item4.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['status'] == 0:
                    item5 = QTableWidgetItem('Reserved')
                else:
                    item5 = QTableWidgetItem('Available')

                item5.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item5.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['location'] == ', , , ':
                    item6 = QTableWidgetItem('---')
                else:
                    item6 = QTableWidgetItem(re.sub('^,', '', val['location']))
                item6.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item6.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item7 = QTableWidgetItem(val['ctime'])
                item7.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item7.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item8 = QTableWidgetItem(val['etime'])
                item8.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item8.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                self.tablewidget_gpu.setItem(idx, 0, item0)
                self.tablewidget_gpu.setItem(idx, 1, item1)
                self.tablewidget_gpu.setItem(idx, 2, item2)
                self.tablewidget_gpu.setItem(idx, 3, item3)
                self.tablewidget_gpu.setItem(idx, 4, item4)
                self.tablewidget_gpu.setItem(idx, 5, item5)
                self.tablewidget_gpu.setItem(idx, 6, item6)
                self.tablewidget_gpu.setItem(idx, 7, item7)
                self.tablewidget_gpu.setItem(idx, 8, item8)

    def refresh_room_list(self):
        r = self.session.get('http://%s/getroomsbymember/' % self.ipport)
        self.room_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        num = len(self.room_dict)
        self.tablewidget_room.setRowCount(num)
        if r.status_code < 400:
            for idx, (key, val) in self.room_dict:
                item0 = QTableWidgetItem(key)
                item0.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item1 = QTableWidgetItem('%.f MB' % val['max_memory'])
                item1.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item2 = QTableWidgetItem(str(val['num_members']))
                item2.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item3 = QTableWidgetItem('G%010d' % val['gpuid'])
                item3.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item3.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                if val['status']:
                    item4 = QTableWidgetItem('Running')
                else:
                    item4 = QTableWidgetItem('Suspending')

                item4.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item4.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item5 = QTableWidgetItem(val['datasetname'])
                item5.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item5.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                item6 = QTableWidgetItem()
                item6.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
                item6.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                path = os.path.dirname(os.path.dirname(__file__))
                if key == val['location']:
                    item6.setIcon(QIcon(os.path.join(path, 'images/location.png')))

                self.tablewidget_room.setItem(idx, 0, item0)
                self.tablewidget_room.setItem(idx, 1, item1)
                self.tablewidget_room.setItem(idx, 2, item2)
                self.tablewidget_room.setItem(idx, 3, item3)
                self.tablewidget_room.setItem(idx, 4, item4)
                self.tablewidget_room.setItem(idx, 5, item5)
                self.tablewidget_room.setItem(idx, 6, item6)
                self.tablewidget_room.show()

    def select_data(self, item):
        r = self.session.get('http://%s/getdatasets/' % self.ipport)
        self.data_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        row_items = self.data_dict[item.row()]
        assert row_items[0] == item.row()
        QMessageBox.about(self, row_items[1][0].split('.')[0], row_items[1][1]['description'])

    def menu_gpu(self, pos):
        r = self.session.get('http://%s/getgpus/' % self.ipport)
        self.gpu_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        row = self.tablewidget_gpu.indexAt(pos).row()
        row_items = self.gpu_dict[row]
        assert row_items[0] == row
        if row_items[1][1]['status'] == 0:
            QMessageBox.about(self, 'Message', 'We will locally build a new GPU work station for you according to this '
                                               'configuration within seven days. If the work station exceeds '
                                               'its expiration '
                                               'time, it will be suspended automatically! The suspend will be resolved '
                                               'if you agree to the service renewal!')
        else:
            menu = QMenu()
            item1 = menu.addAction("Build a room")
            item2 = menu.addAction("Remove a room")
            item3 = menu.addAction("Edit a room")
            screenpos = self.tablewidget_gpu.mapToGlobal(pos)
            action = menu.exec(screenpos)
            if action == item1:
                self.addroom(row)
            elif action == item2:
                self.removeroom(row)
            elif action == item3:
                self.editroom(row)

    def addroom(self, row):
        row_items = self.gpu_dict[row]
        r = self.session.post(
            'http://%s/getmaxmemory/' % self.ipport, data={
                'gpuid': row_items[1][1]['gpuid']
            }, verify=False)
        maximum = json.loads(r.content.decode('utf-8'))['maxmemory']
        if maximum < 5120:
            QMessageBox.about(self, 'Message', 'The rest GPU memory must be greater than 5120MB to build a room!')
            return None
        else:
            roomaddpanel = RoomAdd(self, self.session, self.ipport, maximum,
                                   row_items[1][1]['gpuid'], row_items[1][1]['master'])
            roomaddpanel.signal.connect(self.refresh_room_list)
            roomaddpanel.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            roomaddpanel.setWindowTitle('Build a room')
            font = QFont()
            font.setFamily("微软雅黑")
            font.setPointSize(10)
            roomaddpanel.setFont(font)
            roomaddpanel.setWindowModality(Qt.ApplicationModal)
            roomaddpanel.show()

    def removeroom(self, row):
        row_items = self.gpu_dict[row]
        assert row_items[0] == row
        gpuid = row_items[1][1]['gpuid']
        r = self.session.post('http://%s/getroomsbygpuid/' % self.ipport, data={'gpuid': gpuid})
        room_dict = json.loads(r.content.decode('utf-8'))
        if len(room_dict) == 0:
            QMessageBox.about(self, 'Message', 'Room not found on this GPU device!')
            return None
        else:
            roomremovepanel = RoomRemove(self, self.session, self.ipport, gpuid)
            roomremovepanel.signal.connect(self.refresh_room_list)
            roomremovepanel.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            roomremovepanel.setWindowTitle('Remove a room')
            font = QFont()
            font.setFamily("微软雅黑")
            font.setPointSize(10)
            roomremovepanel.setFont(font)
            roomremovepanel.setWindowModality(Qt.ApplicationModal)
            roomremovepanel.show()

    def editroom(self, row):
        row_items = self.gpu_dict[row]
        assert row_items[0] == row
        r = self.session.post(
            'http://%s/getmaxmemory/' % self.ipport, data={
                'gpuid': row_items[1][1]['gpuid']
            }, verify=False)
        maximum = json.loads(r.content.decode('utf-8'))['maxmemory']
        gpuid = row_items[1][1]['gpuid']
        r = self.session.post('http://%s/getroomsbygpuid/' % self.ipport, data={'gpuid': gpuid})
        room_dict = json.loads(r.content.decode('utf-8'))
        if len(room_dict) == 0:
            QMessageBox.about(self, 'Message', 'Room not found on this GPU device!')
            return None
        else:
            roomeditpanel = RoomEdit(self, self.session, self.ipport, room_dict, maximum)
            roomeditpanel.signal.connect(self.refresh_room_list)
            roomeditpanel.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            roomeditpanel.setWindowTitle('Edit a room')
            font = QFont()
            font.setFamily("微软雅黑")
            font.setPointSize(10)
            roomeditpanel.setFont(font)
            roomeditpanel.setWindowModality(Qt.ApplicationModal)
            roomeditpanel.show()

    def enter_room(self, item):
        r = self.session.post('http://%s/getlocation/' % self.ipport)
        location = json.loads(r.content.decode('utf-8'))['location']
        r = self.session.get('http://%s/getroomsbymember/' % self.ipport)
        self.room_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        row = item.row()
        row_items = self.room_dict[row]
        assert row_items[0] == row
        roomid = row_items[1][1]['roomid']
        gpuid = row_items[1][1]['gpuid']
        gpuaddr = row_items[1][1]['gpuaddr'].split(':')[0]
        response = os.system("ping " + ("-n 1 " if platform.system().lower() == "windows" else "-c 1 ") + gpuaddr)
        if response != 0:
            QMessageBox.about(self, 'Message', 'Can not connect to the GPU work station!')
            return None
        master = row_items[1][1]['master']
        if location == 'None':
            self.session.post('http://%s/setlocation/' % self.ipport, data={'roomid': roomid})
            self.refresh_room_list()
            self.chat_IDE = NSSChatIDE(self.session, self.ipport, roomid, gpuid, master)
            self.chat_IDE.signal.connect(self.refresh_room_list)
            self.chat_IDE.show()
            self.chat_IDE.syncfile()
            self.chat_IDE.fileBrowser.autoreadroom()
        elif location == 'R%010d' % roomid:
            if self.chat_IDE:
                self.chat_IDE.show()
                self.chat_IDE.syncfile()
                self.chat_IDE.fileBrowser.autoreadroom()
            else:
                self.chat_IDE = NSSChatIDE(self.session, self.ipport, roomid, gpuid, master)
                self.chat_IDE.signal.connect(self.refresh_room_list)
                self.chat_IDE.show()
                self.chat_IDE.syncfile()
                self.chat_IDE.fileBrowser.autoreadroom()
        else:
            QMessageBox.about(self, 'Message', 'You have entered a room, and you can not'
                                               ' enter other rooms simultaneously!')

    def fileedit(self, row):
        pass

    def download(self, item):
        if item.column() != 6 or item.text() == '---':
            return None
        r = self.session.get('http://%s/accesseddataset/' % self.ipport)
        accessed_dataset = json.loads(r.content.decode('utf-8'))
        row_items = self.data_dict[item.row()]
        datasetname = row_items[1][0]
        # verified = row_items[1][1]['verified']
        if accessed_dataset.get(datasetname):
            pay = row_items[1][1]['price'] + 10
        else:
            pay = row_items[1][1]['price']
        reply = QMessageBox.question(self, row_items[1][0].split('.')[0] + ' ' + 'download',
                                     "You need to pay %.2f RMB to download this dataset! "
                                     "This dataset will be downloaded to the 'downloads' folder under "
                                     "the NSS main directory. The download will be charged according "
                                     "to the dataset author's pricing. In order to avoid repeated downloads that may "
                                     "occupy network resources, additional fees (10 RMB) will be charged for repeated "
                                     "downloads, so please save the dataset properly! You do not have the "
                                     "copyright of the dataset, so distribution or sale for this dataset "
                                     "is not allowed!" % pay,
                                     QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Cancel:
            return None
        else:
            dirname, _ = os.path.split(os.path.abspath(sys.argv[0]))
            path = os.path.join(dirname, 'downloads')
            os.makedirs(path, mode=0o777, exist_ok=True)
            filename = os.path.join(path, datasetname)
            if os.path.exists(filename):
                QMessageBox.about(self, 'Message', 'Dataset %s already exists in %s' % (datasetname, filename))
                return None
            t1 = DownloadThread(datasetname, self.session, self.ipport, filename, pay)
            t1.start()
            t2 = DownloadMinitorThread(filename, t1.file_total)
            t2.signal.connect(self.percentage)
            t2.visible_signal.connect(self.disable_visible)
            t2.start()
            time.sleep(0.5)

    def upload(self):
        uploadpanel = upload.Upload(self, self.session, self.ipport)
        uploadpanel.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        uploadpanel.setWindowTitle('Dataset upload')
        uploadpanel.signal.connect(self.percentage)
        uploadpanel.visible_signal.connect(self.disable_visible)
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        uploadpanel.setFont(font)
        uploadpanel.setWindowModality(Qt.ApplicationModal)
        uploadpanel.show()

    def percentage(self, s):
        self.percent.setVisible(True)
        self.percent.setText(s)

    def disable_visible(self):
        self.percent.setVisible(False)

    def fileupload(self, row):
        row_items = self.gpu_dict[row]
        assert row_items[0] == row
        gpuid = row_items[1][1]['gpuid']
        r = self.session.post('http://%s/getroomsbygpuid/' % self.ipport, data={'gpuid': gpuid})
        room_dict = json.loads(r.content.decode('utf-8'))
        if len(room_dict) == 0:
            QMessageBox.about(self, 'Message', 'Room not found on this GPU device!')
            return None
        else:
            uploadpanel = FileUpload(self, self.session, room_dict)
            uploadpanel.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            uploadpanel.setWindowTitle('Config.py upload')
            font = QFont()
            font.setFamily("微软雅黑")
            font.setPointSize(10)
            uploadpanel.setFont(font)
            uploadpanel.setWindowModality(Qt.ApplicationModal)
            uploadpanel.show()

    def filedownload(self, row):
        row_items = self.gpu_dict[row]
        assert row_items[0] == row
        gpuid = row_items[1][1]['gpuid']
        r = self.session.post('http://%s/getroomsbygpuid/' % self.ipport, data={'gpuid': gpuid})
        room_dict = json.loads(r.content.decode('utf-8'))
        if len(room_dict) == 0:
            QMessageBox.about(self, 'Message', 'Room not found on this GPU device!')
            return None
        else:
            downloadpanel = FileDownload(self, self.session, room_dict)
            downloadpanel.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            downloadpanel.setWindowTitle('Config.py download')
            font = QFont()
            font.setFamily("微软雅黑")
            font.setPointSize(10)
            downloadpanel.setFont(font)
            downloadpanel.setWindowModality(Qt.ApplicationModal)
            downloadpanel.show()

    def reserve(self):
        r = self.session.get('http://%s/prereserve/' % self.ipport)
        response = json.loads(r.content.decode('utf-8'))
        wallet = bool(response['wallet'])
        if not wallet:
            QMessageBox.about(self, 'Message', 'The account balance (less than %.2f RMB) is inefficient for the '
                                               'GPU reservation! Each reservation needs '
                                               '500.00 RMB credits!' % response['pay'])
            return None

        reservepanel = reserve.Reserve(self, self.session, self.ipport)
        reservepanel.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        reservepanel.setWindowTitle('Work station configuration')
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        reservepanel.setFont(font)
        reservepanel.setWindowModality(Qt.ApplicationModal)
        reservepanel.show()

    def search_data(self):
        text = self.edit_data.text()
        items = self.tablewidget_data.findItems(text, QtCore.Qt.MatchContains)
        if self.history_items:
            item = self.history_items[0]
            item.setBackground(QBrush(QColor(255, 255, 255)))
            item.setForeground(QBrush(QColor(0, 0, 0)))

        if len(items) > 0:
            item = items[0]
            item.setBackground(QBrush(QColor(0, 255, 0)))
            item.setForeground(QBrush(QColor(255, 0, 0)))
            row = item.row()
            self.tablewidget_data.verticalScrollBar().setSliderPosition(row)
            self.history_items = items
