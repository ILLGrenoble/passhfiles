import io
import logging
import os
import socket

import paramiko

from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser.dialogs.SessionDialog import SessionDialog
from bastion_browser.models.SessionModel import ServerNode, SessionModel, SessionNode
from bastion_browser.utils.Platform import baseDirectory

class SessionTreeView(QtWidgets.QTreeView):

    openBrowsers = QtCore.pyqtSignal(paramiko.client.SSHClient,str)
    
    def __init__(self,*args,**kwargs):

        super(SessionTreeView,self).__init__(*args,**kwargs)

        model = SessionModel()

        # model.invisibleRootItem()

        self.setModel(model)

        self.setHeaderHidden(True)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onShowContextualMenu)

        self.clicked.connect(self.onBrowseFiles)
    
    def keyPressEvent(self, event):
        
        key = event.key()

        if key == QtCore.Qt.Key_Delete:

            selectedIndex = self.currentIndex()
            sessionsModel = self.model()
            sessionsModel.removeRow(selectedIndex,selectedIndex.parent())
            
        return super(SessionTreeView,self).keyPressEvent(event)

    def mousePressEvent(self, event):

        if (event.button() == QtCore.Qt.RightButton):
            return

        index = self.indexAt(event.pos())

        selected = self.selectionModel().isSelected(index)

        super(SessionTreeView,self).mousePressEvent(event)

        if ((index.row() == -1 and index.column() == -1) or selected):
            self.clearSelection()

    def onAddServer(self):

        text, ok = QtWidgets.QInputDialog.getText(self, 'Add Server', 'Enter server name:')
        if ok and text.strip():
            sessionIndex = self.currentIndex()
            sessionModel = self.model()
            sessionModel.addServer(text.strip(),sessionIndex.internalPointer())

    def onAddSession(self):

        sessionDialog = SessionDialog(self,True)

        if sessionDialog.exec_():
            sessionData = sessionDialog.data()
            sessionsModel = self.model()
            sessionsModel.addSession(sessionData)

    def onBrowseFiles(self):

        currentIndex = self.currentIndex()
        node = currentIndex.internalPointer()
        if not isinstance(node,ServerNode):
            return

        sessionModel = self.model()
        sshSession = sessionModel.data(currentIndex.parent(), SessionModel.SSHSession)
        if sshSession is None:
            logging.error('The ssh connection is not established')
            return

        serverName = node.data(0)

        self.openBrowsers.emit(sshSession,serverName) 
        
    def onConnect(self):

        sessionIndex = self.currentIndex()
        sessionModel = self.model()
        sessionModel.connect(sessionIndex)

    def onEditSession(self):

        sessionModel = self.model()

        selectedIndex = self.currentIndex()
        currentSessionData = sessionModel.data(selectedIndex,QtCore.Qt.UserRole)
        sessionDialog = SessionDialog(self,False, currentSessionData)

        if sessionDialog.exec_():
            newSessionData = sessionDialog.data()
            if currentSessionData['name'] == newSessionData['name']:
                sessionModel.updateSession(selectedIndex, newSessionData)
            else:
                sessionModel.moveSession(selectedIndex, newSessionData)

    def onShowContextualMenu(self, point):

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
                connectAction = menu.addAction('Connect')
                connectAction.triggered.connect(self.onConnect)
                menu.addAction(connectAction)
                addServerAction = menu.addAction('Add server')
                addServerAction.triggered.connect(self.onAddServer)
                menu.addAction(addServerAction)
                menu.exec_(QtGui.QCursor.pos())

