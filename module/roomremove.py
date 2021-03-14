import json

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QMessageBox


class RoomRemove(QDialog):
    signal = pyqtSignal()

    def __init__(self, parent, session, ipport, gpuid, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)
        self.session = session
        self.ipport = ipport
        self.gpuid = gpuid
        r = self.session.post('http://%s/getroomsbygpuid/' % self.ipport, data={'gpuid': self.gpuid})
        self.room_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        self.resize(520, 200)
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.setupUI()

    def setupUI(self):
        self.tablewidget_room = QTableWidget()
        num = len(self.room_dict)
        self.tablewidget_room.setRowCount(num)
        self.tablewidget_room.setColumnCount(4)
        self.tablewidget_room.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.tablewidget_room.itemClicked.connect(self.removeroom)
        self.tablewidget_room.setHorizontalHeaderLabels(
            ['Room ID', 'Max GPU memory', 'Number of members', 'Operation'])
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.tablewidget_room.setFont(font)
        self.tablewidget_room.setColumnWidth(0, 100)
        self.tablewidget_room.setColumnWidth(1, 130)
        self.tablewidget_room.setColumnWidth(2, 150)

        for idx, (key, val) in self.room_dict:

            item0 = QTableWidgetItem(key)
            item0.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
            item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            item1 = QTableWidgetItem('%.f MB' % val['max_memory'])
            item1.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
            item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            item2 = QTableWidgetItem('%d' % val['num_members'])
            item2.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
            item2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            item3 = QTableWidgetItem('Delete')
            item3.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
            item3.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            self.tablewidget_room.setItem(idx, 0, item0)
            self.tablewidget_room.setItem(idx, 1, item1)
            self.tablewidget_room.setItem(idx, 2, item2)
            self.tablewidget_room.setItem(idx, 3, item3)

        layout = QVBoxLayout()
        layout.addWidget(self.tablewidget_room)
        self.setLayout(layout)

    def removeroom(self, item):
        if item.column() != 3:
            return None

        row_items = self.room_dict[item.row()]
        roomid = row_items[1][1]['roomid']
        gpuid = row_items[1][1]['gpuid']
        reply = QMessageBox.question(self, 'Room destroy',
                                     'You are removing the room on the GPU device, and this operation is irrevocable! '
                                     'Do you really want to delete the room?',
                                     QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes)
        if reply == QMessageBox.Cancel:
            self.close()
        else:
            r = self.session.post(
                'http://%s/getgpuipportbygpuid/' % self.ipport, data={
                    'gpuid': self.gpuid
                }
            )
            res = json.loads(r.content.decode('utf-8'))
            gpuipport = res['ipport']
            r = self.session.post('http://' + gpuipport + '/roomremove/',
                                  data={'roomid': int(roomid)})
            if r.status_code >= 400:
                QMessageBox.about(self, 'Message', 'Room removed failed. Can not connect to the work station!')
                return None

            status = json.loads(r.content.decode('utf-8'))['status']
            if status == 1:
                QMessageBox.about(self, 'Message', 'Room removed successfully!')
                self.signal.emit()
            else:
                QMessageBox.about(self, 'Message', 'The room is running, so you can not edit it now!')
                return None
            r = self.session.post('http://%s/roomremove/' % self.ipport, data={'roomid': roomid, 'gpuid': gpuid})
            self.refresh_room_list()
            QMessageBox.about(self, 'Message', 'Room destroy successfully!')
            self.signal.emit()

    def refresh_room_list(self):
        r = self.session.post('http://%s/getroomsbygpuid/' % self.ipport, data={'gpuid': self.gpuid})
        self.room_dict = list(enumerate(json.loads(r.content.decode('utf-8')).items()))
        num = len(self.room_dict)
        self.tablewidget_room.setRowCount(num)

        for idx, (key, val) in self.room_dict:

            item0 = QTableWidgetItem(key)
            item0.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
            item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            item1 = QTableWidgetItem('%.f MB' % val['max_memory'])
            item1.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
            item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            item2 = QTableWidgetItem('%d' % val['num_members'])
            item2.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
            item2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            item3 = QTableWidgetItem('Delete')
            item3.setTextAlignment(Qt.AlignCenter | Qt.AlignBottom)
            item3.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            self.tablewidget_room.setItem(idx, 0, item0)
            self.tablewidget_room.setItem(idx, 1, item1)
            self.tablewidget_room.setItem(idx, 2, item2)
            self.tablewidget_room.setItem(idx, 3, item3)

