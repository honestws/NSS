import os

from PyQt5.QtWidgets import (QTreeView, QFileSystemModel)
from PyQt5.Qt import (QDir, QSizePolicy, QPalette, QFont)
from PyQt5 import Qsci
from PyQt5.Qt import Qt
from .codeeditor import CodeEditor


class FileBrowser(QTreeView):
    def __init__(self, parent=None, textPad=None, notebook=None, codeView=None, filepath=None):
        super().__init__()
        self.path = self.checkPath(os.getcwd())
        self.filename = None
        
        self.text = None
        
        self.initItems()
        self.fileDir = False
        self.filePath = filepath
        self.textPad = textPad
        self.notebook = notebook
        self.codeView = codeView
        
        self.mainWindow = parent
        
        self.index = None
        
        self.copySourceFilePath = None      # copy / paste items
        self.copySourceFileName = None
        self.isCopyFileFolder = None

    def initItems(self):
        font = QFont()
        font.setPixelSize(16)
        
        self.prepareModel(os.getcwd())

        self.setToolTip(os.getcwd())
        
        # prepare drag and drop
        self.setDragEnabled(False)

        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setSizePolicy(sizePolicy)
        self.setAutoExpandDelay(2)
        self.setAlternatingRowColors(False)
        self.setAnimated(False)
        self.setIndentation(20)
        self.setSortingEnabled(False)
        self.setRootIsDecorated(False)
        self.setPalette(QPalette(Qt.black))
        self.setFont(font)
        
        # signals
        self.doubleClicked.connect(self.onDoubleClicked)
        self.clicked.connect(self.onClicked)
        self.pressed.connect(self.onClicked)
        #self.entered.connect(self.onEntered)
        self.columnMoved()
        
        # that hides the size, file type and last modified colomns
        self.setHeaderHidden(True)
        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)
        self.resize(400, 400)

    def autoreadroom(self):

        if self.fileDir:
            filePath = self.checkPath(self.filePath)
            try:
                os.chdir(filePath)
            except Exception as e:
                self.mainWindow.statusBar.showMessage(str(e), 3000)
            self.path = self.checkPath(os.getcwd())

            self.model.setRootPath(filePath)

            if self.rootIsDecorated:
                self.setRootIsDecorated(False)

        else:
            self.filename = self.filePath

            try:
                with open(self.filename, encoding='utf-8') as f:
                    self.text = f.read()
            except Exception as e:
                self.mainWindow.statusBar.showMessage(str(e), 3000)
                self.filename = None
                return

            if self.textPad:

                if not self.textPad.filename:
                    editor = CodeEditor(self.mainWindow)
                    editor.filename = self.filePath
                    self.notebook.newTab(editor)

                    x = self.notebook.count()  # number of tabs
                    index = x - 1
                    self.notebook.setCurrentIndex(index)

                    tabName = os.path.basename(editor.filename)

                    self.textPad = editor
                    self.textPad.setText(self.text)
                    self.notebook.setTabText(x, tabName)
                else:
                    editor = CodeEditor(self.mainWindow)
                    editor.filename = self.filePath
                    tabName = os.path.basename(editor.filename)
                    self.notebook.newTab(editor)

                    x = self.notebook.count()  # number of tabs
                    index = x - 1
                    self.notebook.setCurrentIndex(index)

                    self.textPad = editor
                    self.textPad.setText(self.text)
                    self.notebook.setTabText(x, tabName)

            if not self.textPad:
                editor = CodeEditor(self.mainWindow)
                editor.filename = None
                self.notebook.newTab(editor)
                x = self.notebook.count()
                index = x - 1
                self.notebook.setCurrentIndex(index)
                self.textPad = editor

            # make codeView
            codeViewList = self.codeView.makeDictForCodeView(self.text)
            self.codeView.updateCodeView(codeViewList)

            # update textPad Autocomplete
            autocomplete = Qsci.QsciAPIs(self.textPad.lexer)
            self.textPad.autocomplete = autocomplete
            self.textPad.setPythonAutocomplete()

        self.clearSelection()
        self.textPad.updateAutoComplete()

        # remove the '*' when opening new file ...
        self.removeStarAtOpen()

    def prepareModel(self, path):
        self.model = QFileSystemModel()
        self.model.setRootPath(path)
        #model.setFilter(QDir.AllDirs |QDir.NoDotAndDotDot | QDir.AllEntries)
        self.model.setFilter(QDir.Files | QDir.AllDirs | QDir.NoDot | QDir.Hidden)  
        #self.model.setNameFilters(self.filter)
        
        self.model.rootPathChanged.connect(self.onRootPathChanged)
                
        self.fsindex = self.model.setRootPath(path)
        
        self.setModel(self.model)
        self.setRootIndex(self.fsindex)


    def checkPath(self, path):
        if '\\' in path:
            path = path.replace('\\', '/')
        return path


    def getFileInformation(self):
        index = self.index
        indexItem = self.model.index(index.row(), 0, index.parent())

        fileName = self.model.fileName(indexItem)
        filePath = self.model.filePath(indexItem)
        fileDir = self.model.isDir(indexItem)
        fileInfo = self.model.fileInfo(indexItem)
            
        fileName = self.checkPath(fileName)
        filePath = self.checkPath(filePath)
        
        return(fileName, filePath, fileDir, fileInfo)


    def onClicked(self, index):
        self.index = index       #.... index des FileSystemModels
        indexItem = self.model.index(index.row(), 0, index.parent())
        
        fileName, filePath, fileDir, fileInfo = self.getFileInformation()
        self.setToolTip(filePath)
        
        if fileDir:
            self.path = self.checkPath(os.getcwd())
            self.filename = None
        else:
            self.filename = filePath
            self.path = self.checkPath(os.getcwd())
        
        #print('self.filename: ', self.filename)
        #print('self.path: ', self.path)


    def refresh(self, dir=None):
        if not dir:
            dir = self.checkPath(os.getcwd())
        else:
            dir = dir
        
        self.model.setRootPath(dir)
        
        if self.rootIsDecorated:
            self.setRootIsDecorated(False)
        
        self.clearSelection()

    
    def onDoubleClicked(self, index):
        self.index = index
        indexItem = self.model.index(index.row(), 0, index.parent())

        fileName, filePath, fileDir, fileInfo = self.getFileInformation()

        if fileDir:
            filePath = self.checkPath(filePath)
            try:
                os.chdir(filePath)
            except Exception as e:
                self.mainWindow.statusBar.showMessage(str(e), 3000)
            self.path = self.checkPath(os.getcwd())

            self.model.setRootPath(filePath)

            if self.rootIsDecorated:
                self.setRootIsDecorated(False)

        else:
            self.filename = filePath

            try:
                with open(self.filename, encoding='utf-8') as f:
                    self.text = f.read()
            except Exception as e:
                self.mainWindow.statusBar.showMessage(str(e), 3000)
                self.filename = None
                return

            if self.textPad:

                if not self.textPad.filename:
                    editor = CodeEditor(self.mainWindow)
                    editor.filename = filePath
                    self.notebook.newTab(editor)

                    x = self.notebook.count()   # number of tabs
                    index = x - 1
                    self.notebook.setCurrentIndex(index)
                    tabName = os.path.basename(editor.filename)

                    self.textPad = editor
                    self.textPad.setText(self.text)
                    self.notebook.setTabText(x, tabName)

                else:
                    editor = CodeEditor(self.mainWindow)
                    editor.filename = filePath
                    tabName = os.path.basename(editor.filename)
                    self.notebook.newTab(editor)

                    x = self.notebook.count()   # number of tabs
                    index = x - 1
                    self.notebook.setCurrentIndex(index)

                    self.textPad = editor
                    self.textPad.setText(self.text)
                    self.notebook.setTabText(x, tabName)

            if not self.textPad:
                    editor = CodeEditor(self.mainWindow)
                    editor.filename = None
                    self.notebook.newTab(editor)
                    x = self.notebook.count()
                    index = x - 1
                    self.notebook.setCurrentIndex(index)
                    self.textPad = editor

            # make codeView
            codeViewList = self.codeView.makeDictForCodeView(self.text)
            self.codeView.updateCodeView(codeViewList)

            # update textPad Autocomplete
            autocomplete = Qsci.QsciAPIs(self.textPad.lexer)
            self.textPad.autocomplete = autocomplete
            self.textPad.setPythonAutocomplete()

        self.clearSelection()
        self.textPad.updateAutoComplete()

        # remove the '*' when opening new file ...
        self.removeStarAtOpen()
    
    def removeStarAtOpen(self):
        notebook = self.mainWindow.notebook
        textPad = notebook.currentWidget()
        index = notebook.currentIndex()

        if textPad.filename:
            fname = os.path.basename(textPad.filename)
            notebook.setTabText(index, fname)
   
    def onRootPathChanged(self):
        self.setModel(None)
        self.setModel(self.model)
        self.fsindex = self.model.setRootPath(QDir.currentPath())
        self.setRootIndex(self.fsindex)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setSizePolicy(sizePolicy)
        self.setAutoExpandDelay(2)
        self.setAlternatingRowColors(False)
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(False)
        self.setRootIsDecorated(False)
        
        self.setHeaderHidden(True)
        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)
        self.setToolTip(QDir.currentPath())
        self.path = os.getcwd()
        self.path = self.checkPath(self.path)
