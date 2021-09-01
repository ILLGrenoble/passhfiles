from PyQt5 import QtWidgets

def mainWindow(widget):
    """Returns the mainwindow from a given subwidget.

    Returns:
        PyQt5.QtWidgets.QMainWindow: the main window
    """

    if widget is None:
        return None

    if isinstance(widget,QtWidgets.QMainWindow):
        return widget
    else:
        return mainWindow(widget.parent())