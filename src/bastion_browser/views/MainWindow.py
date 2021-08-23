import collections
import io
import logging
import os
import paramiko
import socket
import sys
import yaml

from PyQt5 import QtCore, QtGui, QtWidgets

import bastion_browser
from bastion_browser.dialogs.PreferencesDialog import PreferencesDialog
from bastion_browser.kernel.Preferences import PREFERENCES, loadPreferences
from bastion_browser.models.LocalFileSystemModel import LocalFileSystemModel
from bastion_browser.models.RemoteFileSystemModel import RemoteFileSystemModel
from bastion_browser.utils.Platform import homeDirectory, iconsDirectory, preferencesPath, sessionsDatabasePath
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

        self.loadPreferencesFile()

    def _buildMenu(self):
        """Build the menu.
        """

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&Session')

        addSessionAction = QtWidgets.QAction('&Add Session', self)
        addSessionAction.setStatusTip('Open ssh session dialog')
        addSessionAction.triggered.connect(self._sessionsTreeView.onAddSession)
        fileMenu.addAction(addSessionAction)

        saveSessionsAction = QtWidgets.QAction('&Save Session(s)', self)
        saveSessionsAction.setStatusTip('Save current sessions')
        saveSessionsAction.triggered.connect(self.onSaveSessions)
        fileMenu.addAction(saveSessionsAction)

        clearSessionsAction = QtWidgets.QAction('&Clear Session(s)', self)
        clearSessionsAction.setStatusTip('Clear all sessions')
        clearSessionsAction.triggered.connect(self.onClearSessions)
        fileMenu.addAction(clearSessionsAction)

        restoreSessionsAction = QtWidgets.QAction('&Restore Session(s)', self)
        restoreSessionsAction.setStatusTip('Restore sessions')
        restoreSessionsAction.triggered.connect(self.onLoadSessions)
        fileMenu.addAction(restoreSessionsAction)

        fileMenu.addSeparator()

        preferencesAction = QtWidgets.QAction('&Preferences', self)
        preferencesAction.setStatusTip('Open preferences settings')
        preferencesAction.triggered.connect(self.onSetPreferences)
        fileMenu.addAction(preferencesAction)

        fileMenu.addSeparator()

        exitAction = QtWidgets.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit')
        exitAction.triggered.connect(self.onQuitApplication)
        fileMenu.addAction(exitAction)

    def _buildToolBars(self):
        """Build the toolbar.
        """

        newSessionAction = QtWidgets.QAction(QtGui.QIcon(os.path.join(iconsDirectory(),'new_session.png')), 'New session', self)
        newSessionAction.triggered.connect(self._sessionsTreeView.onAddSession)
        newSessionAction.setToolTip('Setup a new SSH session')

        saveSessionsAction = QtWidgets.QAction(QtGui.QIcon(os.path.join(iconsDirectory(),'save_sessions.png')), 'Save session(s)', self)
        saveSessionsAction.triggered.connect(self.onSaveSessions)
        saveSessionsAction.setToolTip('Save the current session(s)')

        clearSessionsAction = QtWidgets.QAction(QtGui.QIcon(os.path.join(iconsDirectory(),'clear_sessions.png')), 'Clear session(s)', self)
        clearSessionsAction.triggered.connect(self.onClearSessions)
        clearSessionsAction.setToolTip('Clear the current session(s)')

        restoreSessionsAction = QtWidgets.QAction(QtGui.QIcon(os.path.join(iconsDirectory(),'restore_sessions.png')), 'Restore session(s)', self)
        restoreSessionsAction.triggered.connect(self.onLoadSessions)
        restoreSessionsAction.setToolTip('Restore the session(s)')

        preferencesAction = QtWidgets.QAction(QtGui.QIcon(os.path.join(iconsDirectory(),'preferences.png')), 'Settings', self)
        preferencesAction.triggered.connect(self.onSetPreferences)
        preferencesAction.setToolTip('Setup the preferences')

        exitAction = QtWidgets.QAction(QtGui.QIcon(os.path.join(iconsDirectory(),'exit.png')), 'Exit application', self)
        exitAction.triggered.connect(self.onQuitApplication)
        exitAction.setToolTip('Exit')

        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(newSessionAction)
        self.toolbar.addAction(saveSessionsAction)
        self.toolbar.addAction(clearSessionsAction)
        self.toolbar.addAction(restoreSessionsAction)
        self.toolbar.addAction(preferencesAction)
        self.toolbar.addAction(exitAction)

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

        self._splitter = QtWidgets.QSplitter()
        self._splitter.addWidget(self._sourceFileSystem)
        self._splitter.addWidget(self._targetFileSystem)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self._sessionsTreeView)
        hlayout.addWidget(self._splitter, stretch=2)

        logger = LoggerWidget(self)
        logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logger)
        logging.getLogger().setLevel(logging.INFO)

        self.setCentralWidget(self._mainFrame)

        mainLayout = QtWidgets.QVBoxLayout()

        mainLayout.addLayout(hlayout, stretch=4)
        mainLayout.addWidget(logger.widget, stretch=1)

        self.setGeometry(0, 0, 1400, 800)

        self._mainFrame.setLayout(mainLayout)

        self._buildToolBars()
        self._buildMenu()

        iconPath = os.path.join(iconsDirectory(), 'bastion_browser.png')
        self.setWindowIcon(QtGui.QIcon(iconPath))

        self.show()

        self._sessionsTreeView.openBrowsersSignal.connect(self.onOpenBrowsers)

    def loadPreferencesFile(self):
        """Load the preferences settings.
        """

        if not os.path.exists(preferencesPath()):
            return

        loadPreferences(preferencesPath())

        if PREFERENCES['auto-connect']:
            sessionsModel = self._sessionsTreeView.model()
            sessionIndexes = [sessionsModel.index(i,0) for i in range(sessionsModel.rowCount())]
            for index in sessionIndexes:
                sessionsModel.connect(index)

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
            sys.exit()

    def onSaveSessions(self):
        """Save the sessions.
        """

        sessionsModel = self._sessionsTreeView.model()

        sessionsModel.saveSessions(sessionsDatabasePath())

    def onSetPreferences(self):
        """Sets the preferences.
        """

        dialog = PreferencesDialog(self)
        dialog.exec_()

    @property
    def sessionsTreeView(self):
        return self._sessionsTreeView
