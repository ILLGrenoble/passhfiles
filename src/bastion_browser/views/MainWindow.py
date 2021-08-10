import collections
import io
import logging
import os
import paramiko
import socket
import sys
import yaml

from PyQt5 import QtCore, QtWidgets

from bastion_browser.dialogs.PreferencesDialog import PreferencesDialog
from bastion_browser.kernel.Preferences import PREFERENCES, loadPreferences
from bastion_browser.models.LocalFileSystemModel import LocalFileSystemModel
from bastion_browser.models.RemoteFileSystemModel import RemoteFileSystemModel
from bastion_browser.utils.Platform import preferencesPath, sessionsDatabasePath
from bastion_browser.views.FileSystemTableView import FileSystemTableView
from bastion_browser.views.SessionTreeView import SessionTreeView
from bastion_browser.widgets.LoggerWidget import LoggerWidget

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)

        self._init_ui()

        self.loadSessions()

        self.loadPreferences()

    def _build_menu(self):
        """Build the menu.
        """

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&Session')

        addSessionAction = QtWidgets.QAction('&Add Session', self)
        addSessionAction.setStatusTip('Open ssh session dialog')
        addSessionAction.triggered.connect(self._sessionListView.onAddSession)
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
        restoreSessionsAction.setStatusTip('Clear all sessions')
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

    def _init_ui(self):

        self._mainFrame = QtWidgets.QFrame(self)
        
        self._sessionListView = SessionTreeView()

        self._sourceFileSystem = FileSystemTableView()

        self._targetFileSystem = FileSystemTableView()

        self._splitter = QtWidgets.QSplitter()
        self._splitter.addWidget(self._sourceFileSystem)
        self._splitter.addWidget(self._targetFileSystem)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self._sessionListView)
        hlayout.addWidget(self._splitter, stretch=2)

        logger = LoggerWidget(self)
        logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logger)

        self.setCentralWidget(self._mainFrame)

        mainLayout = QtWidgets.QVBoxLayout()

        mainLayout.addLayout(hlayout, stretch=4)
        mainLayout.addWidget(logger.widget, stretch=1)

        self.setGeometry(0, 0, 1400, 800)

        self._mainFrame.setLayout(mainLayout)

        self._sessionListView.openBrowsers.connect(self.onOpenBrowsers)

        self._build_menu()

        self.show()

        logging.getLogger().setLevel(logging.INFO)

    def loadPreferences(self):

        if not os.path.exists(preferencesPath()):
            return

        loadPreferences(preferencesPath())

        if PREFERENCES['auto-connect']:
            sessionsModel = self._sessionListView.model()
            sessionIndexes = [sessionsModel.index(i,0) for i in range(sessionsModel.rowCount())]
            for index in sessionIndexes:
                sessionsModel.connect(index)

    def loadSessions(self):

        sessionsPath = sessionsDatabasePath()

        sessionModel = self._sessionListView.model()
        sessionModel.loadSessions(sessionsPath)

    def onAddToFavorites(self, fileSystemType, currentDirectory):

        sessionModel = self._sessionListView.model()
        sessionModel.addToFavorites(self._sessionListView.currentIndex(),fileSystemType, currentDirectory)

    def onClearSessions(self):

        sessionModel = self._sessionListView.model()
        sessionModel.clear()

    def onLoadSessions(self):

        self.loadSessions()

    def onOpenBrowsers(self, sshSession, serverIndex):

        localFileSystemModel = LocalFileSystemModel(sshSession, serverIndex, '.')
        self._sourceFileSystem.setModel(localFileSystemModel)
        self._sourceFileSystem.horizontalHeader().setSectionResizeMode(3,QtWidgets.QHeaderView.ResizeToContents)

        remoteFileSystemModel = RemoteFileSystemModel(sshSession, serverIndex, '/')
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

        sessionsModel = self._sessionListView.model()

        sessionsModel.saveSessions(sessionsDatabasePath())

    def onSetPreferences(self):

        dialog = PreferencesDialog(self)
        dialog.exec_()

    @property
    def sessionListView(self):
        return self._sessionListView
