import json

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QDialog, QMessageBox, \
    QComboBox, QCompleter


class RoomAdd(QDialog):
    signal = pyqtSignal()

    def __init__(self, parent, session, ipport, maximum, gpuid, master, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)
        self.session = session
        self.ipport = ipport
        self.maximum = maximum
        self.gpuid = gpuid
        self.master = master
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.setupUI()

    def setupUI(self):
        memory = QLabel('Max memory (MB)')
        self.memory = QLineEdit()
        self.memory.setPlaceholderText('5120' + '-' + str(int(self.maximum)))
        self.cbdata = QComboBox()
        dataset_label = QLabel('Dataset')
        r = self.session.post('http://%s/getaccessdata/' % self.ipport)
        room_info = json.loads(r.content.decode('utf-8'))
        self.dataset_list = room_info['datasetlist']
        self.cbdata.addItems(self.dataset_list)
        self.cbdata.setEditable(True)
        completer = QCompleter(self.dataset_list)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.cbdata.setCompleter(completer)
        members = QLabel('Member list')
        self.members = QTextEdit()
        self.members.setPlaceholderText('P0000000001;\nP0000000002;\n')

        pIntValidator = QIntValidator()
        pIntValidator.setRange(5120, self.maximum)
        self.memory.setValidator(pIntValidator)

        submitbtn = QPushButton()
        submitbtn.setText('Submit')
        submitbtn.clicked.connect(self.submit)

        grid = QGridLayout()
        grid.setSpacing(5)

        grid.addWidget(dataset_label, 0, 0, Qt.AlignRight)
        grid.addWidget(self.cbdata, 0, 1)

        grid.addWidget(memory, 1, 0, Qt.AlignRight)
        grid.addWidget(self.memory, 1, 1)

        grid.addWidget(members, 2, 0, Qt.AlignRight | Qt.AlignTop)
        grid.addWidget(self.members, 2, 1)

        grid.addWidget(submitbtn, 3, 0, Qt.AlignCenter | Qt.AlignBottom)

        self.setLayout(grid)

    def submit(self):
        memory = self.memory.text()
        members = self.members.toPlainText()
        dataset = self.cbdata.currentText()

        if memory == '' or members == '':
            QMessageBox.about(self, 'Message', 'Required fields are empty!')
            return None

        r = self.session.post(
            'http://%s/roomadd/' % self.ipport, data={
                'memory': memory, 'members': members, 'gpuid': self.gpuid, 'datasetname': dataset}, verify=False)
        roomid = json.loads(r.content.decode('utf-8'))['roomid']
        if roomid >= 1:
            r = self.session.post(
                'http://%s/getgpuipportbygpuid/' % self.ipport, data={
                    'gpuid': self.gpuid
                }
            )
            res = json.loads(r.content.decode('utf-8'))
            gpuipport = res['ipport']
            r = self.session.post('http://' + gpuipport + '/roomadd/',
                                  data={'roomid': roomid, 'max_memory': memory, 'master': self.master,
                                        'members': members.replace('\n', '').split(';')[:-1]})
            if r.status_code < 400:
                QMessageBox.about(self, 'Message', 'Room added successfully!')
            else:
                r = self.session.post(
                    'http://%s/deleteroom/' % self.ipport, data={
                        'roomid': roomid
                    }
                )
                QMessageBox.about(self, 'Message', 'Room added failed. Can not connect to the work station!')
            self.signal.emit()

        elif roomid == 0:
            username = json.loads(r.content.decode('utf-8'))['username']
            QMessageBox.about(self, 'Message', 'Add room failed! Unknown user accounts: %s '
                                               'or incorrect input format!'
                                               ' Please check the correctness of the input format '
                                               'and user account!' % username)
        elif roomid == -1:
            QMessageBox.about(self, 'Message', 'Only four rooms are allowed to build!')
        self.close()
