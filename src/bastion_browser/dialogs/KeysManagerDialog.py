from PyQt5 import QtGui, QtWidgets

from bastion_browser.kernel.KeyStore import KEYSTORE
from bastion_browser.utils.Platform import iconsDirectory

class KeysManagerDialog(QtWidgets.QDialog):
    """Dialog for setting up a new SSH session.
    """

    def __init__(self, parent):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QWidget): the parent window
        """

        super(KeysManagerDialog,self).__init__(parent)

        self._initUi()

        self.setWindowTitle('Keys manager dialog')

    def fillLayout(self):
        """Fill the layout with the keys stored in the keys store.
        """

        for r, keyfile in enumerate(KEYSTORE.keys()):
            lineEdit = QtWidgets.QLineEdit()
            lineEdit.setText(str(keyfile))
            lineEdit.setReadOnly(True)
            deleteButton = QtWidgets.QPushButton()
            deleteButton.setIcon(QtGui.QIcon(str(iconsDirectory().joinpath('trash.png'))))
            deleteButton.clicked.connect(lambda state, key=keyfile: self.onDeleteKey(key))
            self._gridLayout.addWidget(lineEdit,r,0)
            self._gridLayout.addWidget(deleteButton,r,1)

    def _initUi(self):
        """Setup the dialog.
        """

        self._gridLayout = QtWidgets.QGridLayout()

        self.fillLayout()

        self._buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)

        self._mainLayout = QtWidgets.QVBoxLayout()

        self._gridLayout.setColumnStretch(1,0)

        self._mainLayout.addLayout(self._gridLayout)

        self._mainLayout.addWidget(self._buttonBox)

        self.setGeometry(0, 0, 600, 150)

        self.setLayout(self._mainLayout)

    def clearLayout(self):
        """Remove all widgets from the grid layout.
        """

        for i in reversed(range(self._gridLayout.rowCount())):
            for j in reversed(range(self._gridLayout.columnCount())):
                item = self._gridLayout.itemAtPosition(i,j)
                if item is None:
                    continue
                if item.widget():
                    item.widget().deleteLater()

    def onDeleteKey(self, keyfile):
        """Remove a given key from the store.

        Args:
            keyfile (pathlib.Path): the key file
        """

        KEYSTORE.delKey(keyfile)

        self.clearLayout()

        self.fillLayout()

