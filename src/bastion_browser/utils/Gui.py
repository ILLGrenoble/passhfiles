from PyQt5 import QtWidgets

def mainWindow(widget):

    if widget is None:
        return None

    if isinstance(widget,QtWidgets.QMainWindow):
        return widget
    else:
        return mainWindow(widget.parent())