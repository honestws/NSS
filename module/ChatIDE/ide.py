#!/usr/local/bin/python3
import json
import os
import sys
from multiprocessing import Queue
from time import sleep

import psutil
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QMainWindow, QWidget,
                             QHBoxLayout,
                             QToolBar, QAction, QSplitter,
                             QFileDialog, QStatusBar, QDialog,
                             QSizePolicy, QPushButton,
                             QLineEdit, QDesktopWidget, QShortcut, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.Qt import Qt
from PyQt5.QtPrintSupport import QPrintDialog
from PyQt5.Qsci import QsciPrinter
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from .chatter2 import Chatter
from .codeeditor import CodeEditor
from .extroctor2 import ExtractorProcess
from .filebrowser import FileBrowser
from .paraset import ParameterSetting
from .shower2 import ShowerPanel
from .socket2 import NssGradSocket, NssChatSocket
from .tabwidget import TabWidget
from .codeview import CodeView
from .thread2 import GradMinitorThread, RecordMinitorThread, ErrorMinitorThread


class NSSChatIDE(QMainWindow):
    signal = pyqtSignal()

    def __init__(self, session, ipport, roomid, gpuid, master):
        super().__init__()
        path = os.path.abspath(__file__)
        self.HOME = os.path.dirname(path) + '/'
        self.setWindowIcon(QIcon(self.HOME + 'images/n.png'))
        self.roomid = roomid
        self.gpuid = gpuid
        self.session = session
        self.ipport = ipport
        self.master = master
        self.exev = None
        self.nss_grad_socket = None

        # change to Home Path
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.path = os.path.join(BASE_DIR, 'configs')
        os.makedirs(self.path, mode=0o777, exist_ok=True)
        os.chdir(self.path)

        self.fileBrowser = None
        
        self.centerOnScreen()
        r = self.session.post('http://%s/getrequestuser/' % self.ipport)
        res = json.loads(r.content.decode('utf-8'))
        self.worker = res['username']
        self.nss_chat_socket = NssChatSocket(self, self.session, self.ipport, self.roomid)
        self.nss_chat_socket.setVisible(False)
        self.queue_list = [Queue()]
        self.nss_grad_socket = NssGradSocket(self, self.session, self.ipport, self.roomid, [self.queue_list[0]])
        self.nss_grad_socket.setVisible(False)
        self.chatter = Chatter(self.session, self.ipport, self.roomid, self)
        self.extractor = None
        self.showerpanel = None
        self.train_record_minitor = None
        self.test_record_minitor = None
        self.grad_minitor = None
        self.error_minitor = None

        self.initUI()
        self.updateroomstatus()

    def initUI(self):        
        self.setGeometry(300, 300, 1200, 600)
        self.setWindowTitle('NSS IDE - R%010d' % self.roomid)
        
        # splitters
        self.splitter1 = QSplitter(Qt.Vertical)
        splitter2 = QSplitter(Qt.Horizontal)

        # actions
        self.newAction = QAction(QIcon(self.HOME + 'images/new.png'), 'New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.triggered.connect(self.new)

        self.openAction = QAction(QIcon(self.HOME + 'images/open.png'), 'Open', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.triggered.connect(self.open)

        self.saveAction = QAction(QIcon(self.HOME + 'images/save.png'), 'Save', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.triggered.connect(self.save)

        self.saveAsAction = QAction(QIcon(self.HOME + 'images/saveAs.png'), 'Save As', self)
        self.saveAsAction.setShortcut('Ctrl+Shift+S')
        self.saveAsAction.triggered.connect(self.saveAs)

        self.printAction = QAction(QIcon(self.HOME + 'images/print.png'), 'Print', self)
        self.printAction.setShortcut('Ctrl+P')
        self.printAction.triggered.connect(self.onPrint)

        self.undoAction = QAction(QIcon(self.HOME + 'images/undo.png'), 'Undo', self)
        self.undoAction.setShortcut('Ctrl+Z')
        self.undoAction.triggered.connect(self.undo)

        self.redoAction = QAction(QIcon(self.HOME + 'images/redo.png'), 'Redo', self)
        self.redoAction.setShortcut('Ctrl+Shift+Z')
        self.redoAction.triggered.connect(self.redo)

        self.zoomInAction = QAction(QIcon(self.HOME + 'images/zoomIn.png'), 'ZoomIn', self)
        self.zoomInAction.setShortcut('Ctrl++')
        self.zoomInAction.triggered.connect(self.zoomIn)

        self.zoomOutAction = QAction(QIcon(self.HOME + 'images/zoomOut.png'), 'ZoomOut', self)
        self.zoomOutAction.setShortcut('Ctrl+-')
        self.zoomOutAction.triggered.connect(self.zoomOut)

        self.runAction = QAction(QIcon(self.HOME + 'images/run.png'), 'Run', self)
        self.runAction.triggered.connect(self.run)

        self.stopAction = QAction(QIcon(self.HOME + 'images/stop.png'), 'Stop', self)
        self.stopAction.triggered.connect(self.terminate)

        self.closedoorAction = QAction(QIcon(self.HOME + 'images/door-close.png'), 'Close door', self)
        self.closedoorAction.triggered.connect(self.doorclose)

        self.opendoorAction = QAction(QIcon(self.HOME + 'images/door-open.png'), 'Open door', self)
        self.opendoorAction.triggered.connect(self.dooropen)

        self.restartAction = QAction(QIcon(self.HOME + 'images/restart.png'), 'Restart', self)
        self.restartAction.triggered.connect(self.restart)

        self.runAction.setEnabled(True)
        self.stopAction.setEnabled(False)

        searchShortcut = QShortcut(self)
        searchShortcut.setKey('Ctrl+F')
        searchShortcut.activated.connect(self.onSearch)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # make toolbar
        self.toolbar = QToolBar()
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.newAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.openAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.saveAsAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.printAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.redoAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.zoomInAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.zoomOutAction)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(spacer)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.runAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.stopAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.closedoorAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.opendoorAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.restartAction)
        self.toolbar.addSeparator()
        
        # widgets
        self.notebook = TabWidget(self)
        self.codeView = CodeView(self, self.notebook)
        self.notebook.newTab()
        self.notebook.newTab(self.chatter)
        self.chatter.to_socket.connect(self.nss_chat_socket.sendTextMessage)
        self.chatter.signal.connect(self.codeView.refresh_codeView)
        self.nss_chat_socket.to_chatter.connect(self.chatter.msg_rcv)
        self.textPad = self.notebook.textPad
        self.fileBrowser = FileBrowser(self, self.textPad, self.notebook, self.codeView,
                                       os.path.join(self.path, 'R%010d' % self.roomid + '.py'))
        self.textPad.fileBrowser = self.fileBrowser

        # add widgets to splitters
        self.splitter1.addWidget(self.fileBrowser)
        self.splitter1.addWidget(self.nss_chat_socket)
        self.splitter1.addWidget(self.nss_grad_socket)
        self.splitter1.addWidget(self.codeView)
        w = self.splitter1.width()
        self.splitter1.setSizes([w//2, 0, 0, w//2])
        splitter2.addWidget(self.splitter1)
        splitter2.addWidget(self.notebook)

        hbox = QHBoxLayout()
        hbox.addWidget(splitter2)
        
        self.splitter1.setStretchFactor(1, 1)
        splitter2.setStretchFactor(1, 10)
        self.setCentralWidget(splitter2)
      
        # make statusbar
        self.statusBar = QStatusBar()
        self.searchEdit = QLineEdit()
        spacer2 = QWidget()
        self.searchEdit.returnPressed.connect(self.onSearch)
        self.searchButton = QPushButton(QIcon(self.HOME + 'images/search.png'), 'Search', self)
        self.searchButton.clicked.connect(self.onSearch)
        self.statusBar.addPermanentWidget(spacer2)
        self.statusBar.addPermanentWidget(self.searchEdit)
        self.statusBar.addPermanentWidget(self.searchButton)
        self.setStatusBar(self.statusBar)
        # show all
        self.textPad.setFocus()
        self.show()

    def syncfile(self):
        r = self.session.post('http://%s/getgpuipportbygpuid/' % self.ipport,
                              data={'gpuid': self.gpuid})
        res = json.loads(r.content.decode('utf-8'))
        gpuipport = res['ipport']

        os.makedirs(self.path, mode=0o777, exist_ok=True)
        filename = os.path.join(self.path, 'R%010d' % self.roomid + '.py')

        r = self.session.get(
            'http://' + gpuipport + '/downloadfile/?roomid=%s' % self.roomid)
        try:
            json.loads(r.content.decode('utf-8'))
            self.statusBar.showMessage('There exists no configuration file in the room! '
                                       'New ' + 'R%010d' % self.roomid + '.py' + ' created', 3000)
            with open(filename, "wb") as _:
                pass
        except:
            self.statusBar.showMessage('Automatic synchronization success!', 3000)
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

    def updateroomstatus(self):
        r = self.session.post('http://%s/getroomstatus/' % self.ipport,
                              data={'roomid': self.roomid})
        room_status_dict = json.loads(r.content.decode('utf-8'))
        closed = room_status_dict['closed']
        if closed == 0:
            self.closedoorAction.setEnabled(True)
            self.opendoorAction.setEnabled(False)
        else:
            self.closedoorAction.setEnabled(False)
            self.opendoorAction.setEnabled(True)

    def new(self):
        editor = CodeEditor(parent=self)
        editor.filename = None
        
        self.notebook.newTab(editor)
        
        x = self.notebook.count()
        index = x - 1
        
        self.notebook.setCurrentIndex(index)
        self.textPad = editor
        self.notebook.textPad = editor
        self.mainWindow = self.textPad.mainWindow

    def open(self):
        dialog = QFileDialog(self)
        dialog.setViewMode(QFileDialog.List)
        dialog.setDirectory(os.getcwd())

        filename = dialog.getOpenFileName(self, "Save")
        
        if filename[0]:
            filePath = filename[0]
            
            try:
                with open(filePath, 'r') as f:
                    text = f.read()
                
                editor = CodeEditor(self)
                editor.setText(text) 
                editor.filename = filePath
                
                self.notebook.newTab(editor)
                x = self.notebook.count()   # number of tabs
                index = x - 1
                self.notebook.setCurrentIndex(index)
                
                tabName = os.path.basename(editor.filename)    
                self.notebook.setTabText(x, tabName)
                self.textPad = editor    
            
            except Exception as e:
                self.statusBar.showMessage(str(e), 3000)

    def save(self):
        filename = self.textPad.filename
        index = self.notebook.currentIndex()
        tabText = self.notebook.tabText(index)
        
        if not filename:
            self.saveAs()
        
        else:
            text = self.textPad.text().replace('\r\n', '\n')
            if self.worker == self.master and os.path.basename(filename) == 'R%010d' % self.roomid + '.py':
                try:
                    with open(filename, 'w', encoding='utf-8') as file:
                        file.write(text)
                        self.statusBar.showMessage(filename + " saved", 3000)

                    # remove '*' in tabText
                    fname = os.path.basename(filename)
                    self.notebook.setTabText(index, fname)
                    room = 'R%010d' % self.roomid
                    e = MultipartEncoder(
                        fields={'roomid': str(self.roomid),
                                'data': (room + '.py', open(
                                    os.path.join(self.path, 'R%010d' % self.roomid + '.py'), 'rb'),
                                         'application/octet-stream')}
                    )

                    m = MultipartEncoderMonitor(e, lambda monitor: monitor)
                    r = self.session.post('http://%s/getgpuipportbygpuid/' % self.ipport,
                                          data={'gpuid': self.gpuid})
                    res = json.loads(r.content.decode('utf-8'))
                    gpuipport = res['ipport']

                    r = self.session.post(
                        'http://' + gpuipport + '/filercv/', data=m,
                        headers={'Content-Type': m.content_type})
                    if r.status_code < 400:
                        self.statusBar.showMessage('Synchronization success!', 3000)
                    else:
                        self.statusBar.showMessage('Synchronization failed! Please try again later!', 3000)
                except Exception as e:
                    self.statusBar.showMessage(str(e), 3000)
                    self.saveAs()
            else:
                try:
                    with open(filename, 'w', encoding='utf-8') as file:
                        file.write(text)
                        self.statusBar.showMessage(filename + " saved", 3000)
                    fname = os.path.basename(filename)
                    self.notebook.setTabText(index, fname)
                except Exception as e:
                    self.statusBar.showMessage(str(e), 3000)
                    self.saveAs()
    
    def saveAs(self):
        dialog = QFileDialog(self)
        dialog.setViewMode(QFileDialog.List)

        filename = dialog.getSaveFileName(self, 'save',
                                          os.getcwd() + "/" + 'R%010d' % self.roomid + '.py', 'Python file(*.py)')
        
        if filename[0]:
            fullpath = filename[0]
            text = self.textPad.text().replace('\r\n', '\n')
            if self.worker == self.master and os.path.basename(fullpath) == 'R%010d' % self.roomid + '.py':
                try:
                    with open(fullpath, 'w', encoding='utf-8') as file:
                        file.write(text)
                        self.statusBar.showMessage(fullpath + " saved", 3000)

                        # update all widgets

                        self.textPad.filename = fullpath
                        self.refresh(self.textPad)
                        self.fileBrowser.refresh()
                        fname = os.path.basename(fullpath)
                        index = self.notebook.currentIndex()
                        self.notebook.setTabText(index, fname)
                        room = 'R%010d' % self.roomid
                        e = MultipartEncoder(
                            fields={'roomid': str(self.roomid),
                                    'data': (room + '.py', open(fullpath, 'rb'), 'application/octet-stream')}
                        )

                        m = MultipartEncoderMonitor(e, lambda monitor: monitor)
                        r = self.session.post('http://%s/getgpuipportbygpuid/' % self.ipport,
                                              data={'gpuid': self.gpuid})
                        res = json.loads(r.content.decode('utf-8'))
                        gpuipport = res['ipport']

                        r = self.session.post(
                            'http://' + gpuipport + '/filercv/', data=m,
                            headers={'Content-Type': m.content_type})
                        # status = json.loads(r.content.decode('utf-8'))['status']
                        if r.status_code < 400:
                            self.statusBar.showMessage('Upload success!', 3000)
                        else:
                            self.statusBar.showMessage('Upload failed! Please try again later!', 3000)

                except Exception as e:
                    self.statusBar.showMessage(str(e), 3000)
            elif self.worker != self.master and os.path.basename(fullpath) == 'R%010d' % self.roomid + '.py':
                self.statusBar.showMessage('This file is read-only for workers!', 3000)
            else:
                with open(fullpath, 'w', encoding='utf-8') as file:
                    file.write(text)
                    self.statusBar.showMessage(fullpath + " saved", 3000)

                    # update all widgets

                    self.textPad.filename = fullpath
                    self.refresh(self.textPad)
                    self.fileBrowser.refresh()
                    fname = os.path.basename(fullpath)
                    index = self.notebook.currentIndex()
                    self.notebook.setTabText(index, fname)
        else:
            self.statusBar.showMessage('File not saved !', 3000)

    def onPrint(self):
        doc = QsciPrinter()
        dialog = QPrintDialog(doc, self)
        dialog.setWindowTitle('Print')
        if dialog.exec_() == QDialog.Accepted:
            self.textPad.setPythonPrintStyle()
            try:
                doc.printRange(self.textPad)
            except Exception as e:
                print(str(e))
                
        else:
            return
        
        self.textPad.setPythonStyle()

    def undo(self):
        self.textPad.undo()

    def redo(self):
        self.textPad.redo()
    
    def zoomIn(self):
        self.textPad.zoomIn()
    
    def zoomOut(self):
        self.textPad.zoomOut()

    def run(self):
        r = self.session.post(
            'http://%s/getroomstatus/' % self.ipport, data={'roomid': self.roomid})
        closed = json.loads(r.content.decode('utf-8'))['closed']
        if closed:
            QMessageBox.about(self, 'Message', "The room has been closed by its master! You can not enter the room now!")
            self.runAction.setEnabled(True)
            self.stopAction.setEnabled(False)
            return None
        r = self.session.post(
            'http://%s/getaccessdata/' % self.ipport)
        datasetlist = json.loads(r.content.decode('utf-8'))['datasetlist']
        r = self.session.post(
            'http://%s/getroomdata/' % self.ipport, data={'roomid': self.roomid})
        roomdata = json.loads(r.content.decode('utf-8'))['roomdataset']
        if roomdata in datasetlist:
            dirname, _ = os.path.split(os.path.abspath(sys.argv[0]))
            path = os.path.join(dirname, 'downloads')
            filename = os.path.join(path, roomdata)
            if not os.path.exists(filename):
                QMessageBox.about(self, 'Message', 'Uncompressed file: %s not found!' % filename)
                return None

            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(BASE_DIR, 'configs')
            config_path = os.path.join(config_path, 'R%010d' % self.roomid + '.py')
            ckp_path = os.path.join(BASE_DIR, 'ckps')
            os.makedirs(ckp_path, mode=0o777, exist_ok=True)
            data_path = os.path.join(BASE_DIR, 'downloads')
            data_path = os.path.join(data_path, roomdata)

            file = open(config_path).read()
            config = {}
            exec(file, config)
            EXEV = config.get('ExtractorEvaluator')
            NET = config.get('DeepNet')
            METRIC = config.get('Metric')
            LOSS = config.get('loss')
            DATALOADER = config.get('Dataloader')
            if EXEV is None:
                QMessageBox.about(self, 'Message', "'ExtractorEvaluator' class not found in the configuration file!")
                self.runAction.setEnabled(True)
                self.stopAction.setEnabled(False)
                return None
            if NET is None:
                QMessageBox.about(self, 'Message', "'DeepNet' module not found in the configuration file!")
                self.runAction.setEnabled(True)
                self.stopAction.setEnabled(False)
                return None
            if METRIC is None:
                QMessageBox.about(self, 'Message', "'Metric' class not found in the configuration file!")
                self.runAction.setEnabled(True)
                self.stopAction.setEnabled(False)
                return None
            if LOSS is None:
                QMessageBox.about(self, 'Message', "Loss function not found in the configuration file!")
                self.runAction.setEnabled(True)
                self.stopAction.setEnabled(False)
                return None
            if DATALOADER is None:
                QMessageBox.about(self, 'Message', "'Dataloader' class not found in the configuration file!")
                self.runAction.setEnabled(True)
                self.stopAction.setEnabled(False)
                return None

            self.runAction.setEnabled(False)
            self.stopAction.setEnabled(False)
            self.restartAction.setEnabled(False)

            ps = ParameterSetting(self)
            ps.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            ps.setWindowTitle('Parameter setting')
            ps.setWindowModality(Qt.ApplicationModal)
            ps.show()
            ps.exec_()

            for _ in range(5):
                self.queue_list.append(Queue())
            self.train_record_minitor = RecordMinitorThread([self.queue_list[1]], self)
            self.test_record_minitor = RecordMinitorThread([self.queue_list[2]], self)
            self.grad_minitor = GradMinitorThread([self.queue_list[3]], self)
            self.error_minitor = ErrorMinitorThread([self.queue_list[4]], self)
            self.extractor = ExtractorProcess(config_path, ps.reg, ps.bat, ckp_path, data_path,
                                              self.roomid, ps.tim, self.queue_list,
                                              self.session, self.ipport, self.gpuid)
            self.grad_minitor.start()
            self.test_record_minitor.start()
            self.train_record_minitor.start()
            self.error_minitor.start()
            self.extractor.start()
            self.grad_minitor.to_socket.connect(self.nss_grad_socket.sendBinaryMessage)
            self.error_minitor.to_main_thread.connect(self.error_hint)
            self.statusBar.showMessage('Trying to catch exceptions!', 60000)

    def error_hint(self, e):
        if e is None:
            self.statusBar.showMessage('No exceptions! Creating signal connections to slots', 3000)
            plotname = self.queue_list[5].get(block=True)
            self.showerpanel = ShowerPanel(self, plotname)
            self.train_record_minitor.to_shower.connect(self.showerpanel.train_shower.update)
            self.test_record_minitor.to_shower.connect(self.showerpanel.test_shower.update)
            self.nss_grad_socket.to_shower_panel.connect(self.showerpanel.settext)

            self.notebook.newTab(self.showerpanel)
            x = self.notebook.count()
            index = x - 1
            self.notebook.setCurrentIndex(index)
            self.textPad = self.showerpanel
            self.notebook.textPad = self.showerpanel
            self.mainWindow = self.textPad.mainWindow
            self.runAction.setEnabled(False)
            self.stopAction.setEnabled(True)
            self.restartAction.setEnabled(False)
        else:
            p = psutil.Process(self.extractor.pid)
            p.terminate()
            self.train_record_minitor.quit()
            self.test_record_minitor.quit()
            self.grad_minitor.quit()
            self.error_minitor.quit()
            self.queue_list = []
            self.statusBar.showMessage('Caught exceptions!', 3000)
            QMessageBox.about(self, 'Message', e)
            self.runAction.setEnabled(True)
            self.stopAction.setEnabled(False)

    def terminate(self):
        self.runAction.setEnabled(True)
        self.stopAction.setEnabled(False)
        self.restartAction.setEnabled(True)

        p = psutil.Process(self.extractor.pid)
        p.terminate()
        self.extractor = None
        self.train_record_minitor.quit()
        self.test_record_minitor.quit()
        self.grad_minitor.quit()
        self.error_minitor.quit()
        self.queue_list = []
        self.nss_grad_socket.close_socket()

        ind = self.splitter1.indexOf(self.nss_grad_socket)
        self.queue_list = [Queue()]
        self.nss_grad_socket = NssGradSocket(self, self.session, self.ipport, self.roomid, [self.queue_list[0]])
        self.nss_grad_socket.setVisible(False)
        self.splitter1.replaceWidget(ind, self.nss_grad_socket)

    def restart(self):
        if self.worker == self.master:
            reply = QMessageBox.question(self, 'Message', 'You are trying to restart the room, '
                                                          'which will release all source of the process, '
                                                          'and disconnect the all worker connections.',
                                         QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Cancel:
                return None
            else:
                r = self.session.post('http://%s/getroomgradaddr/' % self.ipport, data={'roomid': self.roomid})
                re = json.loads(r.content.decode('utf-8'))
                addr = re['addr']

                r = self.session.post(
                    'http://%s/getgpuipportbygpuid/' % self.ipport, data={
                        'gpuid': self.gpuid
                    }
                )
                res = json.loads(r.content.decode('utf-8'))
                gpuipport = res['ipport']
                r = self.session.post('http://' + gpuipport + '/roomrestart/',
                                      data={'roomid': self.roomid})
                if r.status_code >= 400:
                    QMessageBox.about(self, 'Message', 'Restart failed. Can not connect to the work station!')
                    return None
                while True:
                    sleep(0.3)
                    r = self.session.post('http://%s/getroomgradaddr/' % self.ipport, data={'roomid': self.roomid})
                    re = json.loads(r.content.decode('utf-8'))
                    if addr != re['addr']:
                        break

                ind = self.splitter1.indexOf(self.nss_grad_socket)
                self.queue_list = [Queue()]
                self.nss_grad_socket = NssGradSocket(self, self.session, self.ipport, self.roomid, [self.queue_list[0]])
                self.nss_grad_socket.setVisible(False)
                self.splitter1.replaceWidget(ind, self.nss_grad_socket)
        else:
            QMessageBox.about(self, 'Message', 'You are not the room master. The worker has not the privilege to '
                                               'restart the room!')

    def doorclose(self):
        if self.worker == self.master:
            r = self.session.post(
                'http://%s/getgpuipportbygpuid/' % self.ipport, data={
                    'gpuid': self.gpuid
                }
            )
            res = json.loads(r.content.decode('utf-8'))
            gpuipport = res['ipport']
            r = self.session.post('http://' + gpuipport + '/doorreverse/',
                                  data={'roomid': self.roomid})
            if r.status_code >= 400:
                QMessageBox.about(self, 'Message', 'Door closing failed. Can not connect to the work station!')
                return None
            self.updateroomstatus()
        else:
            QMessageBox.about(self, 'Message', 'You are not the room master. The worker has not the privilege to '
                                               'close the door of the room!')

    def dooropen(self):
        if self.worker == self.master:
            r = self.session.post(
                'http://%s/getgpuipportbygpuid/' % self.ipport, data={
                    'gpuid': self.gpuid
                }
            )
            res = json.loads(r.content.decode('utf-8'))
            gpuipport = res['ipport']
            r = self.session.post('http://' + gpuipport + '/doorreverse/',
                                  data={'roomid': self.roomid})
            if r.status_code >= 400:
                QMessageBox.about(self, 'Message', 'Door open failed. Can not connect to the work station!')
                return None
            self.updateroomstatus()
        else:
            QMessageBox.about(self, 'Message', 'You are not the room master. The worker has not the privilege to '
                                               'open the door of the room!')

    def closeEvent(self, event):
        if self.extractor is not None:
            p = psutil.Process(self.extractor.pid)
            p.terminate()
            self.train_record_minitor.quit()
            self.test_record_minitor.quit()
            self.grad_minitor.quit()
            self.error_minitor.quit()
            self.queue_list = []

        self.session.get('http://%s/clearlocation/' % self.ipport)
        self.nss_grad_socket.close_socket()
        self.nss_chat_socket.close_socket()
        self.signal.emit()
        event.accept()
    
    def onSearch(self):
        text = self.searchEdit.text()
        if text == '':
            self.statusBar.showMessage("can't start search without word", 3000) 
            return
        else:
            if hasattr(self.textPad, 'filename'):
                x = self.textPad.findFirst(text, False, True, False, True, True) # case sensitive

                if x == False:
                    l = len(self.searchEdit.text())
                    self.searchEdit.setSelection(0, l)
                    self.searchEdit.setFocus()
                    self.statusBar.showMessage('<' + text + '> not found', 3000)

    def refresh(self, textPad=None):
        if not textPad:
            return
                 
        self.textPad = textPad

        if hasattr(self.textPad, 'filename'):

            if not self.textPad.filename:
                self.setWindowTitle('NSS IDE - R%010d' % self.roomid)
                return

            dir = os.path.dirname(self.textPad.filename)
            if dir != '':
                try:
                    os.chdir(dir)
                    self.setWindowTitle(self.textPad.filename)

                except Exception as e:
                    self.statusBar.showMessage(str(e), 3000)

                self.fileBrowser.refresh(dir)
                self.codeView.refresh()
        else:
            self.setWindowTitle('Chat Room - R%010d' % self.roomid)

    def centerOnScreen(self):
        res = QDesktopWidget().screenGeometry()
        self.move((res.width() // 2) - (self.frameSize().width() // 2),
                  (res.height() // 2) - (self.frameSize().height() // 2))
