import logging
import os
import platform
import subprocess
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser.dialogs.AboutDialog import AboutDialog
from bastion_browser.models.LocalFileSystemModel import LocalFileSystemModel
from bastion_browser.models.RemoteFileSystemModel import RemoteFileSystemModel
from bastion_browser.utils.Platform import homeDirectory, iconsDirectory, sessionsDatabasePath
from bastion_browser.utils.ProgressBar import progressBar
from bastion_browser.views.FileSystemTableView import FileSystemTableView
from bastion_browser.views.SessionsTreeView import SessionsTreeView
from bastion_browser.widgets.LoggerWidget import LoggerWidget

class MainWindow(QtWidgets.QMainWindow):
    """Implements the main window.
    """

    def __init__(self, parent=None):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QWidget): the parent window
        """

        super(MainWindow, self).__init__(parent)

        self._initUi()

        self.loadSessions()

        self.checkSSHAgent()

    def _buildMenu(self):
        """Build the menu.
        """

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&Session')

        addSessionAction = QtWidgets.QAction('&Add Session', self)
        addSessionAction.setIcon(QtGui.QIcon(os.path.join(iconsDirectory(),'new_session.png')))
        addSessionAction.setStatusTip('Open ssh session dialog')
        addSessionAction.triggered.connect(self._sessionsTreeView.onAddSession)
        fileMenu.addAction(addSessionAction)

        fileMenu.addSeparator()

        exitAction = QtWidgets.QAction('&Exit', self)
        exitAction.setIcon(QtGui.QIcon(os.path.join(iconsDirectory(),'exit.png')))
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit')
        exitAction.triggered.connect(self.onQuitApplication)
        fileMenu.addAction(exitAction)

        helpMenu = menubar.addMenu('&Help')

        aboutAction = QtWidgets.QAction('About',self)
        aboutAction.setIcon(QtGui.QIcon(os.path.join(iconsDirectory(),'about.png')))
        aboutAction.triggered.connect(self.onLaunchAboutDialog)

        helpMenu.addAction(aboutAction)

    def checkSSHAgent(self):
        """Check for a running SSH agent (On Unix) and log some info in cas where one is found.
        """

        if platform.system() not in ['Linux','Darwin']:
            return

        p1 = subprocess.Popen(['ps','ax'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p2 = subprocess.Popen(['grep', '[s]sh-agent'],stdin=p1.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p3 = subprocess.Popen(['wc', '-l'],stdin=p2.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err = p3.communicate()

        err = err.decode().strip()
        if err:
            logging.error(err)
            return

        nAgents = int(out.decode().strip())
        if nAgents > 0:
            logging.info('A SSH agent is running. Please check that your keys are registered before opening a session.')

    def closeEvent(self, event):
        """Called when the user quit the application by closing the main window.

        Args:
            event (PyQt5.QtGui.QCloseEvent): the close event
        """

        self.disconnectAll()

        return super(MainWindow,self).closeEvent(event)

    def _createFileSystemWidget(self, layout):
        """Create a file system widget.

        Args:
            layout (QtWidgets.QLayout): the layout
        """

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        return widget

    def _createFileSystemLayout(self, label, tableView):
        """Create a file system layout.

        The layout is made of a Qlabel on top of a table view.

        Args:
            label (str): the label for the layout
            tableView (bastion_browser.views.FileSystemTableView): the table view
        """

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel(label))
        layout.addWidget(tableView)

        return layout

    def disconnectAll(self):
        """Disconnects all SSH session established so far.
        """

        sessionsModel = self._sessionsTreeView.model()

        for i in range(sessionsModel.rowCount()):
            index = sessionsModel.index(i,0)
            sessionsModel.disconnect(index)

    def _initUi(self):
        """Setup the main window.
        """

        self._mainFrame = QtWidgets.QFrame(self)
        
        self._sessionsTreeView = SessionsTreeView()
        self._progressBar = QtWidgets.QProgressBar()
        progressBar.setProgressWidget(self._progressBar)
        self.statusBar().addPermanentWidget(QtWidgets.QLabel('Progress'))
        self.statusBar().addPermanentWidget(self._progressBar)

        self._sourceFileSystem = FileSystemTableView()
        self._targetFileSystem = FileSystemTableView()
        
        sourceFileSystemWidget = self._createFileSystemWidget(self._createFileSystemLayout('Local filesystem',self._sourceFileSystem))
        targetFileSystemWidget = self._createFileSystemWidget(self._createFileSystemLayout('Remote filesystem',self._targetFileSystem))

        leftPanelWidget = QtWidgets.QWidget()
        leftPaneLayout = QtWidgets.QVBoxLayout()
        leftPaneLayout.addWidget(QtWidgets.QLabel('SSH sessions'))
        leftPaneLayout.addWidget(self._sessionsTreeView)
        leftPanelWidget.setLayout(leftPaneLayout)

        self._splitter = QtWidgets.QSplitter()
        self._splitter.addWidget(leftPanelWidget)
        self._splitter.addWidget(sourceFileSystemWidget)
        self._splitter.addWidget(targetFileSystemWidget)
        self._splitter.setStretchFactor(0,1)
        self._splitter.setStretchFactor(1,2)
        self._splitter.setStretchFactor(2,2)

        logger = LoggerWidget(self)
        logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logger)
        logging.getLogger().setLevel(logging.INFO)

        self.setCentralWidget(self._mainFrame)

        mainLayout = QtWidgets.QVBoxLayout()

        mainLayout.addWidget(self._splitter, stretch=4)
        mainLayout.addWidget(logger.widget, stretch=1)

        self.setGeometry(0, 0, 1400, 800)

        self._mainFrame.setLayout(mainLayout)

        self._buildMenu()

        iconPath = os.path.join(iconsDirectory(), 'bastion_browser.png')
        self.setWindowIcon(QtGui.QIcon(iconPath))

        self.show()

        self._sessionsTreeView.openBrowsersSignal.connect(self.onOpenBrowsers)

    def loadSessions(self):
        """Load the sessions.
        """

        sessionsPath = sessionsDatabasePath()

        sessionsModel = self._sessionsTreeView.model()
        sessionsModel.loadSessions(sessionsPath)

    def onAddToFavorites(self, fileSystemType, path):
        """Called when the user adds a path to the favorites on the local or remote file system.

        Args:
            fileSystemType (str): 'local' or 'remote'
            path (str): the path to add to the favorites
        """

        sessionsModel = self._sessionsTreeView.model()
        sessionsModel.addToFavorites(self._sessionsTreeView.currentIndex(),fileSystemType, path)

    def onClearSessions(self):
        """Removed all the loaded sessions.
        """

        sessionsModel = self._sessionsTreeView.model()
        sessionsModel.clear()

    def onLaunchAboutDialog(self):
        """Pops up the information dialog about the application.
        """

        dialog = AboutDialog(self)
        dialog.exec_()

    def onLoadSessions(self):
        """Load the sessions.
        """

        self.loadSessions()

    def onOpenBrowsers(self, serverIndex):
        """Opens the local and remote file system browsers for a given server.

        Args:
            serverIndex (PyQt5.QtCore.QModelIndex): the index of the server
        """

        localFileSystemModel = LocalFileSystemModel(serverIndex, homeDirectory())
        self._sourceFileSystem.setModel(localFileSystemModel)
        self._sourceFileSystem.horizontalHeader().setSectionResizeMode(3,QtWidgets.QHeaderView.ResizeToContents)

        remoteFileSystemModel = RemoteFileSystemModel(serverIndex, '/')
        self._targetFileSystem.setModel(remoteFileSystemModel)
        self._targetFileSystem.horizontalHeader().setSectionResizeMode(3,QtWidgets.QHeaderView.ResizeToContents)

        localFileSystemModel.addToFavoritesSignal.connect(lambda path : self.onAddToFavorites('local',path))
        remoteFileSystemModel.addToFavoritesSignal.connect(lambda path : self.onAddToFavorites('remote',path))

    def onQuitApplication(self):
        """Event called when the application is exited.
        """

        choice = QtWidgets.QMessageBox.question(
            self, 'Quit', "Do you really want to quit?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.disconnectAll()
            sys.exit()

    @property
    def sessionsTreeView(self):
        return self._sessionsTreeView
