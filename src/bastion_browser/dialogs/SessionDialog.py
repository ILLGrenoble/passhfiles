import collections
import os

from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser import REFKEY
from bastion_browser.utils.Gui import mainWindow

class SessionDialog(QtWidgets.QDialog):

    defaultData = {'name':'my session',
                   'address':'bastion.ill.fr',
                   'user':'passhport',
                   'port':22,
                   'key':'',
                   'keytype': 'ECDSA',
                   'password':''}

    def __init__(self, parent, newSession, data=None):

        super(SessionDialog,self).__init__(parent)

        self._newSession = newSession

        self._data = SessionDialog.defaultData if data is None else data

        self._init_ui()

        self.setWindowTitle('Open SSH session')

    def _init_ui(self):

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
        self._key.setText(self._data['key'])
        self._browseKey = QtWidgets.QPushButton('Browse')
        keyHLayout.addWidget(self._key, stretch=2)
        keyHLayout.addWidget(self._browseKey,stretch=0)

        keyTypeLayout = QtWidgets.QHBoxLayout()
        self._radioButtonGroup = QtWidgets.QButtonGroup(self)
        r0 = QtWidgets.QRadioButton('RSA')
        self._radioButtonGroup.addButton(r0)
        r1 = QtWidgets.QRadioButton('ECDSA')
        self._radioButtonGroup.addButton(r1)
        r2 = QtWidgets.QRadioButton('ED25519')
        self._radioButtonGroup.addButton(r2)
        self._radioButtonGroup.setExclusive(True)
        for b in self._radioButtonGroup.buttons():
            if b.text() == self._data['keytype']:
                b.setChecked(True)
                break
        keyTypeLayout.addWidget(r0)
        keyTypeLayout.addWidget(r1)
        keyTypeLayout.addWidget(r2)

        self._password = QtWidgets.QLineEdit()
        self._password.setEchoMode(QtWidgets.QLineEdit.Password)

        password = REFKEY.decrypt(self._data['password']).decode() if self._data['password'] else ''
        self._password.setText(password)


        self._button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()

        form_layout = QtWidgets.QFormLayout()

        form_layout.addRow(QtWidgets.QLabel('Session Name'),self._name)
        form_layout.addRow(QtWidgets.QLabel('Address/IP'),self._address)
        form_layout.addRow(QtWidgets.QLabel('User'),self._user)
        form_layout.addRow(QtWidgets.QLabel('Port'),self._port)
        form_layout.addRow(QtWidgets.QLabel('Private key'),keyHLayout)
        form_layout.addRow(QtWidgets.QLabel('Key type'),keyTypeLayout)
        form_layout.addRow(QtWidgets.QLabel('Password'),self._password)

        main_layout.addLayout(form_layout)

        main_layout.addWidget(self._button_box)

        self.setGeometry(0, 0, 600, 250)

        self.setLayout(main_layout)

        self._browseKey.clicked.connect(self.onBrowsePrivateKey)

    def accept(self):

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

        return self._data

    def onBrowsePrivateKey(self):

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                            'Open SSH private file',
                                                            '',
                                                            'All files (*)',
                                                            options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if not filename:
            return

        self._key.setText(filename)

    def validate(self):

        name = self._name.text().strip()
        if not name:
            return False, 'No session name provided'
        mw = mainWindow(self)
        sessionModel = mw.sessionListView.model()
        sessionNames = [sessionModel.data(sessionModel.index(i,0),QtCore.Qt.DisplayRole) for i in range(sessionModel.rowCount())]
        if self._newSession and name in sessionNames:
            return False, 'A session with that name already exists'

        address = self._address.text().strip()
        if not address:
            return False, 'No address/ip provided'

        user = self._user.text().strip()
        if not user:
            return False, 'No user provided'

        port = self._port.value()

        key = self._key.text().strip()
        if not key:
            return False, 'No key provided'
        if not os.path.exists(key):
            return False, 'The path to private key does not exist'

        keyType = [b.text() for b in self._radioButtonGroup.buttons() if b.isChecked()][0]

        password = self._password.text().strip() if self._password.text().strip() else None
        if password is not None:
            password = REFKEY.encrypt(bytes(password,'utf-8'))

        self._data = collections.OrderedDict((('name',name),
                                              ('address',address),
                                              ('user',user),
                                              ('port',port),
                                              ('key',key),
                                              ('keytype',keyType),
                                              ('password',password)))

        return True, None



