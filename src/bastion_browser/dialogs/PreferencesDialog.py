import collections
import os

from PyQt5 import QtWidgets

from bastion_browser.kernel.Preferences import PREFERENCES, savePreferences, setPreferences
from bastion_browser.utils.Platform import preferencesPath

class PreferencesDialog(QtWidgets.QDialog):
    """Dialog used for settings the preferences of the application.
    """

    def __init__(self, parent):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QWidget): the parent widget
        """

        super(PreferencesDialog,self).__init__(parent)

        self._initUi()

        self.setWindowTitle('Preferences settings dialog')

    def _initUi(self):
        """Setup the dialog.
        """

        keyHLayout = QtWidgets.QHBoxLayout()
        self._editor = QtWidgets.QLineEdit()
        self._editor.setText(PREFERENCES['editor'])
        self._browseEditor = QtWidgets.QPushButton('Browse')
        keyHLayout.addWidget(self._editor, stretch=2)
        keyHLayout.addWidget(self._browseEditor,stretch=0)

        self._button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()

        formLayout = QtWidgets.QFormLayout()

        formLayout.addRow(QtWidgets.QLabel('Text editor'),keyHLayout)

        mainLayout.addLayout(formLayout)

        mainLayout.addWidget(self._button_box)

        self.setGeometry(0, 0, 600, 150)

        self.setLayout(mainLayout)

        self._browseEditor.clicked.connect(self.onBrowseEditor)

    def accept(self):
        """Called when the user clicks on Accept button.

        It validates the settings prior setting the preferences.
        """

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
        """Returns the dialog data.

        Returns:
            dict: the data
        """

        return self._data

    def onBrowseEditor(self):
        """Called when the user browse for a text editor.
        """

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                            'Browse path for txt editor',
                                                            '',
                                                            'All files (*)',
                                                            options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if not filename:
            return

        self._editor.setText(filename)

    def validate(self):
        """Validate the settings.

        Returns:

            tuple: a tuple whose 1st element is a boolean indicating whether the validation succeeded or not and 2nd 
            element is a message storing the reasons of a failure in case of a failing validation.
        """

        # If set, the path to the text editor must exist
        editor = self._editor.text().strip()
        if editor and not os.path.exists(editor):
            return False, 'The path to text editor does not exist'

        self._data = collections.OrderedDict((('editor',editor)))

        return True, None
