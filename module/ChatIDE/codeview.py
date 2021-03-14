import json
import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow,
                             QVBoxLayout, QListWidget, QListWidgetItem, QMessageBox)

from nickname import NickName


class CodeView(QListWidget):
    signal = pyqtSignal()
    ''' ListWidget to view elements in the code '''
    def __init__(self, parent=None, notebook=None):
        ''' init CodeView '''
        super().__init__()
        self.notebook = notebook
        self.mainWindow = parent

        # signals
        self.itemDoubleClicked.connect(self.gotoPos)

    def makeDictForCodeView(self, text=''):
        codeViewDict = {}
        textList = text.splitlines()
        
        i = 1
        for x in textList:
            if x.strip().startswith('class ') or x.strip().startswith('def ') or x.strip().startswith('P'):
                codeViewDict[i] = x.strip().replace(';', '')
            
            i += 1

        return codeViewDict

    def updateCodeView(self, codeViewDict):
        self.clear()
        self.code = list(codeViewDict.values())
        self.linenumbers = list(codeViewDict.keys())
        
        for line in self.code:
            
            if line.strip().startswith('class'):
                item = QListWidgetItem()
                text = line.strip()
                text = text.strip(':')
                item.setText(text)
                self.addItem(item)
            
            elif line.strip().startswith('def'):
                item = QListWidgetItem()
                text = line.strip()
                text = text.strip(':')
                item.setText('->   ' + text)
                self.addItem(item)
            elif line.strip().startswith('P'):
                item = QListWidgetItem()
                item.setText(line)
                self.addItem(item)
    
    def gotoPos(self):
        row = self.currentRow()
        username = self.currentItem().text()
        if username.strip().startswith('P'):
            if username.split(' ')[0] == self.mainWindow.worker:
                nicknamepanel = NickName(self.mainWindow, self.mainWindow.session, self.mainWindow.ipport, username)
                nicknamepanel.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
                nicknamepanel.setWindowTitle('Nickname revision')
                nicknamepanel.signal.connect(self.refresh_codeView)
                nicknamepanel.show()
            else:
                QMessageBox.about(self, 'Message', 'You can not revise the nickname of other workers')
        else:
            linenumber = self.linenumbers[row] - 1
            textPad = self.notebook.textPad
            if linenumber >= 0:
                y = textPad.lineLength(linenumber) - 1
                textPad.setCursorPosition(linenumber, y)
                textPad.setFocus()
        
        self.clearSelection()

    def refresh_codeView(self):
        r = self.mainWindow.session.post('http://%s/getnickbyroomid/' % self.mainWindow.ipport,
                                         data={'roomid': self.mainWindow.roomid})
        usernick = json.loads(r.content.decode('utf-8'))
        mbs = ''
        for key, val in usernick.items():
            mbs += '%s %s\n; ' % (key, val)
        codeViewDict = self.makeDictForCodeView(mbs)
        self.updateCodeView(codeViewDict)
        self.signal.emit()

    def refresh(self):
        self.clearSelection()
        

class Main(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.view = CodeView()
        widget = QWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setCentralWidget(widget)
        widget.setLayout(layout)
        self.show()


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
