import pathlib

from PyQt5 import QtCore, QtGui, QtWidgets

class FileEditorDialog(QtWidgets.QDialog):

    fileSaved = QtCore.pyqtSignal(pathlib.Path,pathlib.PurePath)

    def __init__(self, tempFile, actualFile):

        super(FileEditorDialog,self).__init__()

        self._tempFile = tempFile

        self._actualFile = actualFile

        self._saveCurrentFileShortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+S'), self)
        self._saveCurrentFileShortcut.activated.connect(self.saveCurrentFile)

        vbox = QtWidgets.QVBoxLayout()
        self._title = QtWidgets.QLabel(str(self._actualFile))
        self._title.setWordWrap(True)
        self._title.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(self._title)

        self._scrollableTextArea = QtWidgets.QTextEdit()
        self._scrollableTextArea.setText(open(str(self._tempFile),'r').read())
        vbox.addWidget(self._scrollableTextArea)

        self._buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self._buttonBox)

        self.setLayout(vbox)

        self.setGeometry(0, 0, 800, 400)

    def accept(self):
        """Called when the user accepts the changes made in the file.
        """

        self.saveCurrentFile()

        super(FileEditorDialog,self).accept()

    def closeEvent(self, event):
        messageBox = QtWidgets.QMessageBox()
        title = "Quit Editor?"
        message = "WARNING !!\n\nIf you quit without saving, any changes made to the file will be lost.\n\nSave file before quitting?"
       
        reply = messageBox.question(self, title, message, messageBox.Yes | messageBox.No |
                messageBox.Cancel, messageBox.Cancel)
        if reply == messageBox.Yes:
            returnValue = self.saveCurrentFile()
            if returnValue == False:
                event.ignore()
        elif reply == messageBox.No:
            event.accept()
        else:
            event.ignore()

    def saveCurrentFile(self):
        """Save the file.
        """
        
        contents = self._scrollableTextArea.toPlainText()

        with open(str(self._tempFile),'w') as fout:
            fout.write(contents)

        self.fileSaved.emit(self._tempFile,self._actualFile)
