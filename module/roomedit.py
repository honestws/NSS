import json

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import QDialog, QWidget, QMessageBox, QComboBox, QTextEdit, QLabel, QLineEdit, QPushButton, \
    QGridLayout, QCompleter


class RoomEdit(QDialog):
    signal = pyqtSignal()

    def __init__(self, parent, session, ipport, room_dict, maximum, *args, **kwargs):
        QWidget.__init__(self, parent, *args, **kwargs)
        self.session = session
        self.ipport = ipport
        self.original_dict = room_dict
        self.maximum = maximum
        self.room_dict = list(enumerate(room_dict.items()))
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.setupUI()
        self.init()

    def setupUI(self):
        roomid = QLabel('Room ID')
        room_names = []
        for idx, (key, val) in self.room_dict:
            room_names.append(key)
        self.cbroom = QComboBox()
        self.cbroom.addItems(room_names)
        self.cbroom.currentIndexChanged.connect(self.select_room)
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
        memory = QLabel('Max memory (MB)')
        self.memory = QLineEdit()
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

        grid.addWidget(roomid, 0, 0, Qt.AlignRight)
        grid.addWidget(self.cbroom, 0, 1)

        grid.addWidget(dataset_label, 1, 0, Qt.AlignRight)
        grid.addWidget(self.cbdata, 1, 1)

        grid.addWidget(memory, 2, 0, Qt.AlignRight)
        grid.addWidget(self.memory, 2, 1)

        grid.addWidget(members, 3, 0, Qt.AlignRight | Qt.AlignTop)
        grid.addWidget(self.members, 3, 1)

        grid.addWidget(submitbtn, 4, 0, Qt.AlignCenter | Qt.AlignBottom)

        self.setLayout(grid)

    def init(self):
        text = self.cbroom.currentText()
        row_items = self.original_dict[text]
        roomid = row_items['roomid']
        r = self.session.post('http://%s/getroombyroomid/' % self.ipport, data={'roomid': roomid})
        room_info = json.loads(r.content.decode('utf-8'))
        self.memory.setText(str(int(room_info['memory'])))
        pIntValidator = QIntValidator()
        pIntValidator.setRange(5120, int(room_info['memory'] + self.maximum))
        self.memory.setValidator(pIntValidator)
        self.members.setText(room_info['memberlist'])
        self.memory.setPlaceholderText('5120' + '-' + str(int(room_info['memory'] + self.maximum)))
        current_dataset = room_info['current_dataset']
        if current_dataset in self.dataset_list:
            idx = self.dataset_list.index(current_dataset)
        else:
            idx = 0
        self.cbdata.setCurrentIndex(idx)

    def select_room(self, idx):
        row_items = self.original_dict[self.room_dict[idx][1][0]]
        roomid = row_items['roomid']
        r = self.session.post('http://%s/getroombyroomid/' % self.ipport, data={'roomid': roomid})
        room_info = json.loads(r.content.decode('utf-8'))
        self.memory.setText(str(int(room_info['memory'])))
        pIntValidator = QIntValidator()
        pIntValidator.setRange(5120, int(room_info['memory'] + self.maximum))
        self.memory.setValidator(pIntValidator)
        self.members.setText(room_info['memberlist'])
        self.memory.setPlaceholderText('5120' + '-' + str(int(room_info['memory'] + self.maximum)))
        current_dataset = room_info['current_dataset']
        if current_dataset in self.dataset_list:
            idx = self.dataset_list.index(current_dataset)
        else:
            idx = 0
        self.cbdata.setCurrentIndex(idx)

    def submit(self):
        text = self.cbroom.currentText()
        row_items = self.original_dict[text]
        roomid = row_items['roomid']
        gpuid = row_items['gpuid']
        memory = self.memory.text()
        members = self.members.toPlainText()
        dataset = self.cbdata.currentText()

        if memory == '' or members == '':
            QMessageBox.about(self, 'Message', 'Required fields are empty!')
            return None

        r = self.session.post(
            'http://%s/roomedit/' % self.ipport, data={'roomid': roomid, 'memory': memory, 'gpuid': gpuid,
                                                       'members': members, 'datasetname': dataset}, verify=False)
        status = json.loads(r.content.decode('utf-8'))['status']
        if status == 1:
            QMessageBox.about(self, 'Message', 'Room revised successfully!')
            self.signal.emit()
        elif status == 0:
            username = json.loads(r.content.decode('utf-8'))['username']
            QMessageBox.about(self, 'Message', 'Room edit failed! Unknown user accounts: %s '
                                               'or incorrect input format!'
                                               ' Please check the correctness of the input format '
                                               'and user account!' % username)
            return None
        r = self.session.post(
            'http://%s/getgpuipportbygpuid/' % self.ipport, data={
                'gpuid': gpuid
            }
        )
        res = json.loads(r.content.decode('utf-8'))
        gpuipport = res['ipport']
        r = self.session.post('http://' + gpuipport + '/roomedit/',
                              data={'roomid': int(roomid),
                                    'max_memory': int(memory),
                                    'members': members.replace('\n', '').split(';')[:-1]})
        if r.status_code >= 400:
            QMessageBox.about(self, 'Message', 'Room edit failed. Can not connect to the work station!')
            return None
        self.close()
