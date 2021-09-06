import collections
import logging
import pathlib
import platform
import re
import subprocess

from PyQt5 import QtCore, QtWidgets

from passhfiles.utils.Gui import mainWindow

class SessionDialog(QtWidgets.QDialog):
    """Dialog for setting up a new SSH session.
    """

    defaultData = {'name':'my session',
                   'address':'bastion.ill.fr',
                   'user':'passhport',
                   'port':22,
                   'key':'',
                   'keytype': 'ED25519'}

    def __init__(self, parent, newSession, data=None):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QWidget): the parent window
            newSession (bool): indicates whether the dialog will be used to set a brand new session
            data (dict): the session data
        """

        super(SessionDialog,self).__init__(parent)

        self._newSession = newSession

        self._data = SessionDialog.defaultData if data is None else data

        self._initUi()

        self.setWindowTitle('Open SSH session')

    def _initUi(self):
        """Setup the dialog.
        """

        self._name = QtWidgets.QLineEdit()
        self._name.setText(self._data['name'])

        self._address = QtWidgets.QLineEdit()
        self._address.setText(self._data['address'])

        self._user = QtWidgets.QLineEdit()
        self._user.setText(self._data['user'])

        self._port = QtWidgets.QSpinBox()
        self._port.setValue(self._data['port'])
        self._port.setMinimum(1)
        self._port.setMaximum(65535)

        keyHLayout = QtWidgets.QHBoxLayout()
        self._key = QtWidgets.QLineEdit()
        if self._data['key'] is not None:
            self._key.setText(str(self._data['key']))
        self._browseKey = QtWidgets.QPushButton('Browse')
        keyHLayout.addWidget(self._key, stretch=2)
        keyHLayout.addWidget(self._browseKey,stretch=0)

        keyTypeLayout = QtWidgets.QHBoxLayout()
        self._radioButtonGroup = QtWidgets.QButtonGroup(self)
        self._keytypesRadioBUttons = {}
        self._keytypesRadioBUttons['RSA'] = QtWidgets.QRadioButton('RSA')
        self._radioButtonGroup.addButton(self._keytypesRadioBUttons['RSA'])
        self._keytypesRadioBUttons['ECDSA'] = QtWidgets.QRadioButton('ECDSA')
        self._radioButtonGroup.addButton(self._keytypesRadioBUttons['ECDSA'])
        self._keytypesRadioBUttons['ED25519'] = QtWidgets.QRadioButton('ED25519')
        self._radioButtonGroup.addButton(self._keytypesRadioBUttons['ED25519'])
        self._radioButtonGroup.setExclusive(True)
        if self._data['keytype'] in self._keytypesRadioBUttons:
            self._keytypesRadioBUttons[self._data['keytype']].setChecked(True)
        keyTypeLayout.addWidget(self._keytypesRadioBUttons['RSA'])
        keyTypeLayout.addWidget(self._keytypesRadioBUttons['ECDSA'])
        keyTypeLayout.addWidget(self._keytypesRadioBUttons['ED25519'])

        self._buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()

        formLayout = QtWidgets.QFormLayout()

        formLayout.addRow(QtWidgets.QLabel('Session Name'),self._name)
        formLayout.addRow(QtWidgets.QLabel('Address/IP'),self._address)
        formLayout.addRow(QtWidgets.QLabel('User'),self._user)
        formLayout.addRow(QtWidgets.QLabel('Port'),self._port)
        formLayout.addRow(QtWidgets.QLabel('Private key'),keyHLayout)
        formLayout.addRow(QtWidgets.QLabel('Key type'),keyTypeLayout)

        mainLayout.addLayout(formLayout)

        mainLayout.addWidget(self._buttonBox)

        self.setGeometry(0, 0, 600, 250)

        self.setLayout(mainLayout)

        self._key.editingFinished.connect(self.onGuessKeyType)
        self._browseKey.clicked.connect(self.onBrowsePrivateKey)

    def accept(self):
        """Called when the user clicks on Accept button.

        It validates the settings prior setting the SSH session.
        """

        isValidated, msg = self.validate()

        if not isValidated:
            errorMessageDialog = QtWidgets.QMessageBox(self)
            errorMessageDialog.setIcon(QtWidgets.QMessageBox.Critical)
            errorMessageDialog.setText(msg)
            errorMessageDialog.setWindowTitle('Error')
            errorMessageDialog.exec_()
            return

        super(SessionDialog,self).accept()

    def data(self):
        """Returns the dialog's data.

        Returns:
            dict: the dialog's data
        """

        return self._data

    def onBrowsePrivateKey(self):
        """Called when the user browses for a private key.
        """

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                            'Open SSH private file',
                                                            '',
                                                            'All files (*)',
                                                            options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if not filename:
            return

        self._key.setText(filename)

        self.onGuessKeyType()

    def onGuessKeyType(self):
        """Guess the key type from the key file.

        Unix only.
        """

        if platform.system() == 'Windows':
            return

        keyfile = self._key.text().strip()
        if not keyfile:
            return
        
        try:
            p = subprocess.Popen(['ssh-keygen', '-l', '-f',keyfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = p.communicate()
            rc = p.returncode
            if rc != 0:
                raise IOError(err.decode())
            keytype = re.search('\((.*)\)',output.decode()).group(1)
            if keytype not in self._keytypesRadioBUttons:
                raise KeyError('Unknown key type')
            self._keytypesRadioBUttons[keytype].setChecked(True)
        except Exception as e:
            logging.error(str(e))
            return

    def validate(self):
        """Validate the settings.

        Returns:
            tuple: a tuple whose 1st element is a boolean indicating whether the validation succeeded or not and 2nd 
            element is a message storing the reasons of a failure in case of a failing validation.
        """

        name = self._name.text().strip()
        if not name:
            return False, 'No session name provided'
        mw = mainWindow(self)
        sessionsModel = mw.sessionsTreeView.model()
        sessionNames = [sessionsModel.data(sessionsModel.index(i,0),QtCore.Qt.DisplayRole) for i in range(sessionsModel.rowCount())]
        if self._newSession and name in sessionNames:
            return False, 'A session with that name already exists'

        address = self._address.text().strip()
        if not address:
            return False, 'No address/ip provided'

        user = self._user.text().strip()
        if not user:
            return False, 'No user provided'

        port = self._port.value()

        key = None
        if self._key.text().strip():
            key = pathlib.Path(self._key.text().strip()).resolve()
            if not key.exists():
                return False, 'The path to private key does not exist'

        keyType = [b.text() for b in self._radioButtonGroup.buttons() if b.isChecked()][0]

        self._data = collections.OrderedDict((('name',name),
                                              ('address',address),
                                              ('user',user),
                                              ('port',port),
                                              ('key',key),
                                              ('keytype',keyType)))

        return True, None
