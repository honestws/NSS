from PyQt5.QtWidgets import (QMessageBox, QLabel, QRadioButton,
                             QPushButton, QListWidget, QTabWidget,
                             QTextEdit)


class MessageBox(QMessageBox):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Label(QLabel):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WhiteLabel(QLabel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PushButton(QPushButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RadioButton(QRadioButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ListWidget(QListWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TabWidget(QTabWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
            

class TextEdit(QTextEdit):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
