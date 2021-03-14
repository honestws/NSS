import json
import re

import requests
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QFormLayout, QLineEdit, QHBoxLayout, QLabel, QCheckBox, QApplication, \
    QVBoxLayout, QDialog, QGridLayout, QPushButton, QTabWidget, QMessageBox
import sys
from module.store import TabWidgetStore
from module.tabwest import TabWidget as TabWidgetWest


class TabWidgetMainWindow(TabWidgetWest):
    def __init__(self, session, ipport, parent=None):
        super(TabWidgetMainWindow, self).__init__(parent)
        self.session = session
        self.ipport = ipport
        self.setWindowTitle("NSS")
        self.setTabPosition(TabWidgetWest.West)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()
        self.tab6 = QWidget()

        self.addTab(self.tab2, '选项卡2')
        self.addTab(self.tab3, '选项卡3')
        self.addTab(self.tab4, '选项卡4')
        self.addTab(self.tab5, '选项卡5')
        self.addTab(self.tab6, '选项卡6')

        self.tab2UI()
        self.tab3UI()
        self.tab4UI()
        self.tab5UI()
        self.tab6UI()

    def tab2UI(self):
        layout = QFormLayout()
        layout.addRow('姓名', QLineEdit())
        layout.addRow('地址', QLineEdit())
        self.setTabText(0, 'Vision')
        self.setTabIcon(0, QIcon('images/camera.png'))
        self.tab2.setLayout(layout)

    def tab3UI(self):
        layout = QFormLayout()
        layout.addRow('姓名', QLineEdit())
        layout.addRow('地址', QLineEdit())
        self.setTabText(1, 'ADAS')
        self.setTabIcon(1, QIcon('images/car.png'))
        self.tab2.setLayout(layout)

    def tab4UI(self):
        layout = QFormLayout()
        tabwidgetstore = TabWidgetStore(self.session, self.ipport)
        layout.addWidget(tabwidgetstore)
        self.setTabText(2, 'Panel')
        self.setTabIcon(2, QIcon('images/manage.png'))
        self.tab4.setLayout(layout)

    def tab5UI(self):
        layout = QFormLayout()
        layout.addRow('姓名', QLineEdit())
        layout.addRow('地址', QLineEdit())
        self.setTabText(3, 'Notice')
        self.setTabIcon(3, QIcon('images/notice.png'))

        self.tab5.setLayout(layout)

    def tab6UI(self):
        layout = QFormLayout()
        layout.addRow('姓名', QLineEdit())
        layout.addRow('地址', QLineEdit())
        self.setTabText(4, 'Account')
        self.setTabIcon(4, QIcon('images/account.png'))

        self.tab6.setLayout(layout)


class NSS(QWidget):
    def __init__(self, ipport,  parent=None):
        super(NSS, self).__init__(parent)
        self.account = ''
        self.ipport = ipport
        self.session = None
        self.resize(1000, 600)
        self.setWindowIcon(QIcon('images/n.png'))
        self.setWindowTitle('NSS')

    def setupUI(self):
        tabwidgetUI = TabWidgetMainWindow(self.session, self.ipport)
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        tabwidgetUI.setFont(font)

        hlayout = QHBoxLayout()
        label1 = QLabel(self)
        label1.setAlignment(Qt.AlignLeft)
        label1.setPixmap(QPixmap("images/person.png"))

        label2 = QLabel(self)
        label2.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        label2.setText(self.account)
        label2.setFont(font)
        label3 = QLabel(self)
        label3.setFont(font)
        label3.setText("Learning Edge AI Models in Null Spaces")
        label3.setAlignment(Qt.AlignLeft)

        hlayout.addWidget(label1, 0, Qt.AlignLeft)
        hlayout.addWidget(label2, 0, Qt.AlignLeft)
        hlayout.addWidget(label3, 3, Qt.AlignCenter)

        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addWidget(tabwidgetUI)

        self.setLayout(vlayout)


class Login(QDialog):
    def __init__(self, ipport, parent=None):
        super(Login, self).__init__(parent)
        self.session = None
        self.ipport = ipport
        self.setWindowIcon(QIcon('images/n.png'))
        self.setWindowTitle('NSS')
        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.setFont(font)
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        tabwidget = QTabWidget()
        tabwidget.setTabPosition(QTabWidget.South)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        tabwidget.addTab(self.tab1, 'Login')
        tabwidget.addTab(self.tab2, "Don't have an account? Sign up!")
        tabwidget.addTab(self.tab3, 'Forget the password? Reset!')

        self.tab1UI()
        self.tab2UI()
        self.tab3UI()

        vlayout = QVBoxLayout()
        vlayout.addWidget(tabwidget)

        self.setLayout(vlayout)

    def tab1UI(self):
        account = QLabel()
        account.setText('Account')
        self.accountedit = QLineEdit()

        pwd = QLabel()
        pwd.setText('Password')
        self.pwdedit = QLineEdit()
        self.pwdedit.setEchoMode(QLineEdit.Password)

        loginbtn = QPushButton()
        loginbtn.setText('Login')
        loginbtn.clicked.connect(self.login)

        self.remeberpassword = QCheckBox()
        self.remeberpassword.setText('Remember your password')
        self.init_login_info()

        img = QLabel()
        pixmap = QPixmap('images/login.jpg')
        img.setPixmap(pixmap)
        glayout = QGridLayout()
        glayout.setAlignment(Qt.AlignCenter)
        glayout.addWidget(img, 0, 0, 1, 3, Qt.AlignTop)

        glayout.addWidget(account, 1, 0, Qt.AlignRight)
        glayout.addWidget(self.accountedit, 1, 1, 1, 2)
        glayout.addWidget(pwd, 2, 0, Qt.AlignRight)
        glayout.addWidget(self.pwdedit, 2, 1, 1, 2)
        glayout.addWidget(self.remeberpassword, 3, 0, Qt.AlignRight)
        glayout.addWidget(loginbtn, 3, 1, 1, 2)

        self.tab1.setLayout(glayout)

    def tab2UI(self):
        email = QLabel()
        email.setText('Email')
        self.emailedit = QLineEdit()

        authcode = QLabel()
        authcode.setText('Authentication code')
        self.authcodeedit1 = QLineEdit()

        signupbtn = QPushButton()
        signupbtn.setText('Sign up')
        signupbtn.clicked.connect(self.signup)

        authcodebtn = QPushButton()
        authcodebtn.setText('Get authentication code')
        authcodebtn.clicked.connect(self.getauthcodebyemail)

        self.remeberemail = QCheckBox()
        self.remeberemail.setText('Remember your email')
        self.init_signup_info()

        img = QLabel()
        pixmap = QPixmap('images/login.jpg')
        img.setPixmap(pixmap)
        glayout = QGridLayout()
        glayout.setAlignment(Qt.AlignCenter)
        glayout.addWidget(img, 0, 0, 1, 3, Qt.AlignTop)

        glayout.addWidget(email, 1, 0, Qt.AlignRight)
        glayout.addWidget(self.emailedit, 1, 1, 1, 2)
        glayout.addWidget(authcode, 2, 0, Qt.AlignRight)
        glayout.addWidget(self.authcodeedit1, 2, 1, 1, 2)
        glayout.addWidget(self.remeberemail, 3, 0, Qt.AlignRight)
        glayout.addWidget(signupbtn, 3, 2)
        glayout.addWidget(authcodebtn, 3, 1)

        self.tab2.setLayout(glayout)

    def tab3UI(self):
        account = QLabel()
        account.setText('Account')
        self.accountedit2 = QLineEdit()

        authcode = QLabel()
        authcode.setText('Authentication code')
        self.authcodeedit2 = QLineEdit()

        resetbtn = QPushButton()
        resetbtn.setText('Reset')
        resetbtn.clicked.connect(self.reset)

        authcodebtn = QPushButton()
        authcodebtn.setText('Get authentication code')
        authcodebtn.clicked.connect(self.getauthcodebyaccount)

        self.remeberaccount= QCheckBox()
        self.remeberaccount.setText('Remember your account')
        self.init_reset_info()

        img = QLabel()
        pixmap = QPixmap('images/login.jpg')
        img.setPixmap(pixmap)
        glayout = QGridLayout()
        glayout.setAlignment(Qt.AlignCenter)
        glayout.addWidget(img, 0, 0, 1, 3, Qt.AlignTop)

        glayout.addWidget(account, 1, 0, Qt.AlignRight)
        glayout.addWidget(self.accountedit2, 1, 1, 1, 2)
        glayout.addWidget(authcode, 2, 0, Qt.AlignRight)
        glayout.addWidget(self.authcodeedit2, 2, 1, 1, 2)
        glayout.addWidget(self.remeberaccount, 3, 0, Qt.AlignRight)
        glayout.addWidget(resetbtn, 3, 2)
        glayout.addWidget(authcodebtn, 3, 1)

        self.tab3.setLayout(glayout)

    def login(self):
        if self.accountedit.text().replace(' ', '') == '' or self.pwdedit.text().replace(' ', '') == '':
            QMessageBox.about(self, 'Message', 'Required fields are empty!')
            return None
        if self.remeberpassword.isChecked() is True:
            self.save_login_info()
        self.session = requests.Session()

        data = {'username': self.accountedit.text(), 'password': self.pwdedit.text()}
        url = 'http://%s/login/' % self.ipport
        r = self.session.post(url, data=data, verify=False)
        status = json.loads(r.content.decode('utf-8'))['status']
        if r.status_code < 400 and status:
            QMessageBox.about(self, 'Message', 'Login success!')
            nss.account = self.accountedit.text()
            nss.session = self.session
            nss.show()
            nss.setupUI()
            self.close()
        else:
            QMessageBox.about(self, 'Message', 'Login failed, please check the account and password!')

    def signup(self):
        email = self.emailedit.text()
        authcode = self.authcodeedit1.text()
        if email.replace(' ', '') == '' or authcode.replace(' ', '') == '':
            QMessageBox.about(self, 'Message', 'Required fields are empty!')
            return None
        if self.remeberemail.isChecked() is True:
            self.save_signup_info()
        with requests.Session() as session:
            data = {'email': email, 'authcode': authcode}
            url = 'http://%s/signup/' % self.ipport
            r = session.post(url, data=data, verify=False)
            status = json.loads(r.content.decode('utf-8'))['status']

            if r.status_code < 400 and status:
                QMessageBox.about(
                    self, 'Message', 'Register success! Your account information has been sent to your email!')
            else:
                QMessageBox.about(self, 'Message', 'Please try again later')

    def reset(self):
        account = self.accountedit2.text()
        authcode = self.authcodeedit2.text()
        if account.replace(' ', '') == '' or authcode.replace(' ', '') == '':
            QMessageBox.about(self, 'Message', 'Required fields are empty!')
            return None
        if self.remeberaccount.isChecked() is True:
            self.save_reset_info()
        with requests.Session() as session:
            data = {'account': account, 'authcode': authcode}
            url = 'http://%s/reset/' % self.ipport
            r = session.post(url, data=data, verify=False)
            status = json.loads(r.content.decode('utf-8'))['status']

            if r.status_code < 400 and status:
                QMessageBox.about(
                    self, 'Message', 'Reset success! Your account information has been sent to your email!')
            else:
                QMessageBox.about(self, 'Message', 'Please try again later')

    def getauthcodebyemail(self):
        reg = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'
        email = self.emailedit.text()
        if re.match(reg, email):
            with requests.Session() as session:
                data = {'email': email}
                url = 'http://%s/authcode_send/' % self.ipport
                r = session.post(url, data=data, verify=False)
                status = json.loads(r.content.decode('utf-8'))['status']
                if r.status_code < 400 and status:
                    QMessageBox.about(self, 'Message', 'The authentication code has been sent to your email!')
                else:
                    QMessageBox.about(self, 'Message', 'Please try again later!')
        else:
            QMessageBox.about(self, 'Message', 'Incorrect E-mail format!')

    def getauthcodebyaccount(self):
        account = self.accountedit2.text()
        with requests.Session() as session:
            data = {'account': account}
            url = 'http://%s/authcode_send/' % self.ipport
            r = session.post(url, data=data, verify=False)
            status = json.loads(r.content.decode('utf-8'))['status']
            if r.status_code < 400 and status:
                QMessageBox.about(self, 'Message', 'The authentication code has been sent to your email!')
            else:
                QMessageBox.about(self, 'Message', 'Please try again later!')

    def save_login_info(self):
        settings = QSettings("login.ini", QSettings.IniFormat)
        settings.setValue("account", self.accountedit.text())
        settings.setValue("password", self.pwdedit.text())
        settings.setValue("remeberpassword", self.remeberpassword.isChecked())

    def save_signup_info(self):
        settings = QSettings("signup.ini", QSettings.IniFormat)
        settings.setValue("email", self.emailedit.text())
        settings.setValue("remeberemail", self.remeberemail.isChecked())

    def save_reset_info(self):
        settings = QSettings("reset.ini", QSettings.IniFormat)
        settings.setValue("account", self.accountedit2.text())
        settings.setValue("remeberaccount", self.remeberaccount.isChecked())

    def init_login_info(self):
        settings = QSettings("login.ini", QSettings.IniFormat)
        the_account = settings.value("account")
        the_password = settings.value("password")
        the_remeberpassword = settings.value("remeberpassword")
        self.accountedit.setText(the_account)
        if the_remeberpassword == "true" or the_remeberpassword is True:
            self.remeberpassword.setChecked(True)
            self.pwdedit.setText(the_password)

    def init_signup_info(self):
        settings = QSettings("signup.ini", QSettings.IniFormat)
        the_email = settings.value("email")
        the_remeberemail = settings.value("remeberemail")
        self.emailedit.setText(the_email)
        if the_remeberemail == "true" or the_remeberemail is True:
            self.remeberemail.setChecked(True)

    def init_reset_info(self):
        settings = QSettings("reset.ini", QSettings.IniFormat)
        the_account = settings.value("account")
        the_remeberaccount = settings.value("remeberaccount")
        self.accountedit2.setText(the_account)
        if the_remeberaccount == "true" or the_remeberaccount is True:
            self.remeberemail2.setChecked(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ip_port = '172.18.112.66:23333'
    login = Login(ip_port)
    nss = NSS(ip_port)
    login.show()
    sys.exit(app.exec_())
