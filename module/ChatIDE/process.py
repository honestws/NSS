import sys
from PyQt5.QtCore import QCoreApplication, pyqtSignal, QThread

from extractor import Extractor


class SocketBackendProcess(QThread):
    trainrecord = pyqtSignal(object)
    testrecord = pyqtSignal(object)
    err = pyqtSignal(str)
    roommemory = pyqtSignal(str)

    def __init__(self, file, reg, bat, tim, ckp_path, data_path, session, ipport, roomid):
        QThread.__init__(self)
        self.file = file
        self.config = {}
        self.reg = reg
        self.bat = bat
        self.ckp_path = ckp_path
        self.data_path = data_path
        self.tim = tim
        self.session = session
        self.ipport = ipport
        self.roomid = roomid
        self.extractor = None
        self._plotname = None

    def run(self):
        app = QCoreApplication(sys.argv)
        exec(self.file, self.config)
        Exev = self.config.get('ExtractorEvaluator')
        exev = Exev(self.reg, self.bat, self.ckp_path, self.data_path, self.roomid)
        self._plotname = exev.getname()
        self.extractor = Extractor(app, exev, self.tim, self.session, self.ipport, self.roomid)
        self.extractor.trainrecord.connect(self.trainrecordtransfer)
        self.extractor.testrecord.connect(self.testrecordtransfer)
        self.extractor.err.connect(self.errexittransfer)
        self.extractor.roommemory.connect(self.roommemorytransfer)
        app.exec_()

    def trainrecordtransfer(self, record):
        self.trainrecord.emit(record)

    def testrecordtransfer(self, record):
        self.testrecord.emit(record)

    def errexittransfer(self, msg):
        self.err.emit(msg)

    def roommemorytransfer(self, msg):
        self.roommemory.emit(msg)

    @property
    def plotname(self):
        return self._plotname
