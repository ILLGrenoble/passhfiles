import io
import logging
import paramiko
import socket

from PyQt5 import QtWidgets

from bastion_browser.models.LocalFileSystemModel import LocalFileSystemModel
from bastion_browser.models.RemoteFileSystemModel import RemoteFileSystemModel
from bastion_browser.views.FileSystemTableView import FileSystemTableView
from bastion_browser.widgets.LoggerWidget import LoggerWidget

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def init_ui(self):

        self._mainFrame = QtWidgets.QFrame(self)

        self._sourceFileSystem = FileSystemTableView()

        self._targetFileSystem = FileSystemTableView()

        self._splitter = QtWidgets.QSplitter()
        self._splitter.addWidget(self._sourceFileSystem)
        self._splitter.addWidget(self._targetFileSystem)

        logger = LoggerWidget(self)
        logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logger)

        self.setCentralWidget(self._mainFrame)

        mainLayout = QtWidgets.QVBoxLayout()

        mainLayout.addWidget(self._splitter, stretch=4)
        mainLayout.addWidget(logger.widget, stretch=1)

        self.setGeometry(0, 0, 1000, 800)

        self._mainFrame.setLayout(mainLayout)

        f = open('/home/pellegrini/.ssh/id_rsa','r')
        s = f.read()
        f.close()
        keyfile = io.StringIO(s)

        k = paramiko.RSAKey.from_private_key(keyfile)
        sshSession = paramiko.SSHClient()
        sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            sshSession.connect('192.168.122.245', username='passhport', pkey=k, port=22)
        except socket.gaierror:
            logging.error('Invalid address')
        except paramiko.ssh_exception.NoValidConnectionsError:
            logging.error('Invalid connection')
        except Exception as e:
            logging.error(str(e))

        fileSystemModel = LocalFileSystemModel(sshSession, '.')
        self._sourceFileSystem.setModel(fileSystemModel)

        remoteFileSystemModel = RemoteFileSystemModel(sshSession, '/')
        self._targetFileSystem.setModel(remoteFileSystemModel)

        logging.getLogger().setLevel(logging.INFO)

        self.show()