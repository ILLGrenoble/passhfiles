import collections
import os

from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser.kernel.Preferences import PREFERENCES, savePreferences, setPreferences
from bastion_browser.utils.Platform import preferencesPath

class PreferencesDialog(QtWidgets.QDialog):

    def __init__(self, parent):

        super(PreferencesDialog,self).__init__(parent)

        self._init_ui()

        self.setWindowTitle('Preferences settings dialog')

    def _init_ui(self):

        keyHLayout = QtWidgets.QHBoxLayout()
        self._editor = QtWidgets.QLineEdit()
        self._editor.setText(PREFERENCES['editor'])
        self._browseEditor = QtWidgets.QPushButton('Browse')
        keyHLayout.addWidget(self._editor, stretch=2)
        keyHLayout.addWidget(self._browseEditor,stretch=0)

        self._autoConnect = QtWidgets.QCheckBox()
        self._autoConnect.setChecked(PREFERENCES['auto-connect'])

        self._button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()

        form_layout = QtWidgets.QFormLayout()

        form_layout.addRow(QtWidgets.QLabel('Text editor'),keyHLayout)
        form_layout.addRow(QtWidgets.QLabel('Auto connect at start up'),self._autoConnect)

        main_layout.addLayout(form_layout)

        main_layout.addWidget(self._button_box)

        self.setGeometry(0, 0, 600, 250)

        self.setLayout(main_layout)

        self._browseEditor.clicked.connect(self.onBrowseEditor)

    def accept(self):

        isValidated, msg = self.validate()

        if not isValidated:
            errorMessageDialog = QtWidgets.QMessageBox(self)
            errorMessageDialog.setIcon(QtWidgets.QMessageBox.Critical)
            errorMessageDialog.setText(msg)
            errorMessageDialog.setWindowTitle('Error')
            errorMessageDialog.exec_()
            return

        setPreferences(self._data)

        savePreferences(preferencesPath())

        super(PreferencesDialog,self).accept()

    def data(self):

        return self._data

    def onBrowseEditor(self):

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                            'Browse path for txt editor',
                                                            '',
                                                            'All files (*)',
                                                            options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if not filename:
            return

        self._editor.setText(filename)

    def validate(self):


        editor = self._editor.text().strip()
        if editor and not os.path.exists(editor):
            return False, 'The path to text editor does not exist'

        self._data = collections.OrderedDict((('editor',editor),
                                              ('auto-connect',self._autoConnect.isChecked())))

        return True, None



