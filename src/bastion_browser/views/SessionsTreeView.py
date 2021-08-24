import io
import logging
import os
import socket

import paramiko

from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser.dialogs.SessionDialog import SessionDialog
from bastion_browser.models.SessionsModel import ServerNode, SessionNode, SessionsModel
from bastion_browser.utils.Platform import sessionsDatabasePath

class SessionsTreeView(QtWidgets.QTreeView):
    """Implements a view for the loaded SSH sessions. The view is implemented a tree view.
    """

    openBrowsersSignal = QtCore.pyqtSignal(QtCore.QModelIndex)
    
    def __init__(self,*args,**kwargs):
        """Constructor.
        """

        super(SessionsTreeView,self).__init__(*args,**kwargs)

        model = SessionsModel()

        self.setModel(model)

        self.setHeaderHidden(True)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onShowContextualMenu)

        self.clicked.connect(self.onBrowseFiles)
    
    def keyPressEvent(self, event):
        """Event triggered when user press a key of the keyboard.

        Args:
            PyQt5.QtGui.QKeyEvent: the key press event
        """
        
        key = event.key()

        if key == QtCore.Qt.Key_Delete:

            selectedIndex = self.currentIndex()
            sessionsModel = self.model()
            sessionsModel.removeRow(selectedIndex,selectedIndex.parent())
            sessionsModel.saveSessions(sessionsDatabasePath())
            
        return super(SessionsTreeView,self).keyPressEvent(event)

    def mousePressEvent(self, event):
        """Event triggered when user clicks on the view.

        Args:
            PyQt5.QtGui.QMouseEvent: the mouse event
        """

        if (event.button() == QtCore.Qt.RightButton):
            return

        index = self.indexAt(event.pos())

        selected = self.selectionModel().isSelected(index)

        super(SessionsTreeView,self).mousePressEvent(event)

        if ((index.row() == -1 and index.column() == -1) or selected):
            self.clearSelection()

    def onAddServer(self):
        """Called when the user click on 'Add server' contextual menu item. Adds a new server to the underlying model.
        """

        text, ok = QtWidgets.QInputDialog.getText(self, 'Add Server', 'Enter server name:')
        if ok and text.strip():
            sessionIndex = self.currentIndex()
            sessionsModel = self.model()
            sessionsModel.addServer(text.strip(),sessionIndex.internalPointer())
            sessionsModel.saveSessions(sessionsDatabasePath())

    def onAddSession(self):
        """Called when the user clicks on 'Add session' contextual menu item. Adds a new session to the underlying model.
        """

        sessionDialog = SessionDialog(self,True)

        if sessionDialog.exec_():
            sessionData = sessionDialog.data()
            sessionsModel = self.model()
            sessionsModel.addSession(sessionData)
            sessionsModel.saveSessions(sessionsDatabasePath())
            lastIndex = sessionsModel.index(sessionsModel.rowCount()-1,0)
            sessionsModel.connect(lastIndex)
            sessionsModel.findServers(lastIndex)

    def onBrowseFiles(self):
        """Caled when the left-clicks on a server node. Opens the local and remote file browsers.
        """

        currentIndex = self.currentIndex()
        node = currentIndex.internalPointer()
        if not isinstance(node,ServerNode):
            return

        sessionsModel = self.model()
        sshSession = sessionsModel.data(currentIndex.parent(), SessionsModel.SSHSession)
        if sshSession is None:
            logging.error('The ssh connection is not established')
            return

        self.openBrowsersSignal.emit(currentIndex) 
        
    def onConnect(self):
        """Called when the user click on 'Connect' contextual menu item. 
        Establishes the SSH connection for the selected session.
        """

        sessionIndex = self.currentIndex()
        sessionsModel = self.model()
        sessionsModel.connect(sessionIndex)

    def onDeleteSession(self):
        """Called when the user clicks on 'Delete' contextual menu item.
        Delete the selected session.
        """

        sessionsModel = self.model()

        selectedIndex = self.currentIndex()

        sessionsModel.removeRow(selectedIndex,selectedIndex.parent())

        sessionsModel.saveSessions(sessionsDatabasePath())

    def onEditSession(self):
        """Called when the user clicks on 'Edit' contextual menu item. 
        Edit the selected session.
        """

        sessionsModel = self.model()

        selectedIndex = self.currentIndex()
        currentSessionData = sessionsModel.data(selectedIndex,QtCore.Qt.UserRole)
        sessionDialog = SessionDialog(self,False, currentSessionData)

        if sessionDialog.exec_():
            newSessionData = sessionDialog.data()
            if currentSessionData['name'] == newSessionData['name']:
                sessionsModel.updateSession(selectedIndex, newSessionData)
            else:
                sessionsModel.moveSession(selectedIndex, newSessionData)

            sessionsModel.saveSessions(sessionsDatabasePath())

    def onFindServers(self):
        """Called when the user clicks on 'Find servers' contextual menu item. This will find automatically 
        all the servers behind the bastion for a given user.
        """

        sessionsModel = self.model()
        sessionIndex = self.currentIndex()

        for i in range(sessionsModel.rowCount(sessionIndex))[::-1]:
            serverIndex = sessionsModel.index(i,0,sessionIndex)
            sessionsModel.removeRow(serverIndex,sessionIndex)
        sessionsModel.findServers(sessionIndex)

    def onShowContextualMenu(self, point):
        """Pops up a contextual menu when the user right-clicks on the sessions view.

        Args:
            point (PyQt5.QtCore.QPoint): the point where the user right-clicked
        """

        menu = QtWidgets.QMenu()

        selectedItems = self.selectionModel().selectedRows()
        if not selectedItems:
            action = menu.addAction('Add ssh session')
            action.triggered.connect(self.onAddSession)
            menu.addAction(action)
            menu.exec_(QtGui.QCursor.pos())
        else:
            if isinstance(selectedItems[0].internalPointer(),SessionNode):
                editAction = menu.addAction('Edit')
                editAction.triggered.connect(self.onEditSession)
                deleteAction = menu.addAction('Delete')
                deleteAction.triggered.connect(self.onDeleteSession)
                connectAction = menu.addAction('Connect')
                connectAction.triggered.connect(self.onConnect)
                menu.addAction(connectAction)
                addServerAction = menu.addAction('Add server')
                addServerAction.triggered.connect(self.onAddServer)
                menu.addAction(addServerAction)
                findServersAction = menu.addAction('Find servers')
                findServersAction.triggered.connect(self.onFindServers)
                menu.addAction(findServersAction)
                menu.exec_(QtGui.QCursor.pos())
