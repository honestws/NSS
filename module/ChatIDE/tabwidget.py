import json
import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QTabWidget, QMessageBox)

from chatter2 import Chatter
from codeeditor import CodeEditor
from widgets import MessageBox


class TabWidget(QTabWidget):
    signal = pyqtSignal()
    close_socket = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        
        self.mainWindow = parent
        self.setMovable(True)
        self.setTabsClosable(True)
        
        # signals
        self.tabCloseRequested.connect(self.closeTab)
        self.currentChanged.connect(self.changeTab)
        
        self.textPad = None 
        self.codeView = None

    def newTab(self, editor=None, codeView=None):
        if not editor:
            editor = CodeEditor(parent=self.mainWindow)
            self.addTab(editor, "noname")
            editor.filename = None
           
            if self.mainWindow:
                self.codeView = self.mainWindow.codeView
        else:
            if editor.filename is None:
                self.addTab(editor, "noname")
            
            else:
                self.addTab(editor, os.path.basename(editor.filename))
                x = self.count() - 1
                self.setTabToolTip(x, editor.filename)
                self.codeView = self.mainWindow.codeView

    def closeTab(self, index):
        x = self.currentIndex()
        if x != index:
            self.setCurrentIndex(index)
        
        tabText = self.tabText(index)
        
        if '*' in tabText:
            q = MessageBox(QMessageBox.Warning, 'Warning',
                           'File not saved\n\nSave now ?',
                           QMessageBox.Yes | QMessageBox.No)
            if (q.exec_() == QMessageBox.Yes):
                self.mainWindow.save()
                self.removeTab(index)
            else:
                self.removeTab(index)
        elif 'chatter' in tabText:
            QMessageBox.about(self, 'Message', 'The chatter tab can not be closed!')
        elif 'shower' in tabText:
            QMessageBox.about(self, 'Message', 'The chatter tab can not be closed!')
        else:
            self.removeTab(index)
        
        x = self.currentIndex()
        self.setCurrentIndex(x)
        if isinstance(self.currentWidget(), Chatter):
            self.mainWindow.toolbar.setEnabled(False)
        else:
            self.mainWindow.toolbar.setEnabled(True)

        if x == -1:
            self.refreshCodeView('')
            self.mainWindow.setWindowTitle('NSS - Python IDE')
    
    
    def changeTab(self, index):
        x = self.count()
        y = x - 1
        
        if y >= 0:
            self.setCurrentIndex(index)
            if isinstance(self.currentWidget(), Chatter):
                self.mainWindow.toolbar.setEnabled(False)
            else:
                self.mainWindow.toolbar.setEnabled(True)
            textPad = self.currentWidget()
            self.textPad = textPad
            text = self.textPad.text()
            
            if self.codeView:
                self.refreshCodeView(text)
            else:
                self.codeView = self.mainWindow.codeView
                self.refreshCodeView(text)
        
        if self.textPad:
            self.mainWindow.refresh(self.textPad)

    def refresh_sendername(self):
        r = self.mainWindow.session.post('http://%s/getrequestuser/' % self.mainWindow.ipport)
        res = json.loads(r.content.decode('utf-8'))
        self.chatter.sendername = res['username'] + " " + res['nickname']
   
    def refreshCodeView(self, text=None):
        codeViewDict = self.codeView.makeDictForCodeView(text)
        self.codeView.updateCodeView(codeViewDict)
    
    def getCurrentTextPad(self):
        textPad = self.currentWidget()
        return textPad
  