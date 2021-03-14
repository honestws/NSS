from PyQt5.QtCore import QThread, pyqtSignal


class GradMinitorThread(QThread):
    to_socket = pyqtSignal(object)

    def __init__(self, queue, parent=None):
        QThread.__init__(self, parent)
        self.queue = queue[0]

    def run(self):
        while True:
            g = self.queue.get(block=True)
            self.to_socket.emit(g)


class RecordMinitorThread(QThread):
    to_shower = pyqtSignal(object)

    def __init__(self, queue, parent=None):
        QThread.__init__(self, parent)
        self.queue = queue[0]

    def run(self):
        while True:
            r = self.queue.get(block=True)
            self.to_shower.emit(r)


class ErrorMinitorThread(QThread):
    to_main_thread = pyqtSignal(object)

    def __init__(self, queue, parent=None):
        QThread.__init__(self, parent)
        self.queue = queue[0]

    def run(self):
        while True:
            e = self.queue.get(block=True)
            self.to_main_thread.emit(e)
