import numpy as np
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from pyqtgraph import GraphicsLayoutWidget


class Shower(GraphicsLayoutWidget):
    def __init__(self, name, mode):
        GraphicsLayoutWidget.__init__(self)
        self.name = name
        self.pcurve = dict()
        for n in self.name:
            p = self.addPlot(title='%s %s' % (n, mode))
            curve = p.plot(pen=(255, 255, 255, 200))
            self.pcurve.update({n: (p, curve)})
            self.nextRow()

    def update(self, data_dict):
        for key, val in data_dict.items():
            self.pcurve[key][1].setData(np.array(val))


class ShowerPanel(QWidget):
    def __init__(self, parent, plotname):
        super().__init__(parent=parent)
        self.filename = 'shower'
        self.mainWindow = parent
        self.info = QLabel()
        self.train_shower = Shower(plotname, 'train')
        self.test_shower = Shower(plotname, 'test')
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout()
        layout.addWidget(self.info)
        layout.addWidget(self.train_shower)
        layout.addWidget(self.test_shower)
        self.setLayout(layout)

    def train_shower_update(self, r):
        self.train_shower.update(r)

    def test_shower_update(self, r):
        self.test_shower.update(r)

    def settext(self, msg):
        self.info.setText(msg)

    @staticmethod
    def text():
        return ''
