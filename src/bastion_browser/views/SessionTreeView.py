import io
import logging
import os
import socket

import paramiko

from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser.dialogs.SessionDialog import SessionDialog
from bastion_browser.utils.Platform import baseDirectory

class SessionTreeView(QtWidgets.QTreeView):

    openBrowsers = QtCore.pyqtSignal(paramiko.client.SSHClient,str)
    
    def __init__(self,*args,**kwargs):

        super(SessionTreeView,self).__init__(*args,**kwargs)

        model = QtGui.QStandardItemModel()

        model.invisibleRootItem()

        self.setModel(model)

        self.setHeaderHidden(True)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onShowContextualMenu)

        self.clicked.connect(self.onBrowseFiles)
    
    def addSession(self,data):

        sessionItem = QtGui.QStandardItem()
        sessionItem.setEditable(False)
        sessionItem.setText(data['name'])
        sessionItem.setData(data,QtCore.Qt.UserRole)
        sessionItem.setData(QtGui.QIcon(os.path.join(baseDirectory(),'icons','session.png')),QtCore.Qt.DecorationRole)
        sessionItem.setToolTip('\n'.join(['{}: {}'.format(k,v) for k,v in data.items()]))

        for server in data['servers']:
            serverItem = QtGui.QStandardItem()
            serverItem.setText(server)
            serverItem.setData(QtGui.QIcon(os.path.join(baseDirectory(),'icons','server.png')),QtCore.Qt.DecorationRole)
            sessionItem.appendRow(serverItem)

        self.model().appendRow(sessionItem)

    def keyPressEvent(self, event):
        
        key = event.key()

        if key == QtCore.Qt.Key_Delete:

            selectedIndex = self.currentIndex()
            self.model().removeRow(selectedIndex.row(),selectedIndex.parent())
            
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
            sessionItem = self.model().itemFromIndex(sessionIndex)

            serverName = text.strip()

            sessionData = sessionItem.data(QtCore.Qt.UserRole)
            if serverName in sessionData['servers']:
                logging.error('A server with name {} already exists'.format(serverName))
                return

            sessionData['servers'].append(serverName)
            sessionItem.setData(sessionData,QtCore.Qt.UserRole)
            sessionItem.setData('\n'.join(['{}: {}'.format(k,v) for k,v in sessionData.items()]),QtCore.Qt.ToolTipRole)

            serverItem = QtGui.QStandardItem()
            serverItem.setText(text.strip())
            serverItem.setData(QtGui.QIcon(os.path.join(baseDirectory(),'icons','server.png')),QtCore.Qt.DecorationRole)
            sessionItem.appendRow(serverItem)

    def onAddSession(self):

        sessionDialog = SessionDialog(self,True)

        if sessionDialog.exec_():
            sessionData = sessionDialog.data()
            self.addSession(sessionData)

    def onBrowseFiles(self):

        currentIndex = self.currentIndex()
        if currentIndex.parent().row() == -1:
            return

        sessionItem = self.model().itemFromIndex(currentIndex.parent())
        sshSession = sessionItem.data(QtCore.Qt.UserRole + 1)
        if sshSession is None:
            logging.error('The ssh connection is not established')
            return

        serverItem = self.model().itemFromIndex(currentIndex)

        self.openBrowsers.emit(sshSession,serverItem.text()) 
        
    def onConnect(self):

        sessionIndex = self.currentIndex()
        sessionItem = self.model().itemFromIndex(sessionIndex)

        data = sessionItem.data(QtCore.Qt.UserRole)

        if data['keytype'] == 'RSA':
            paramikoKeyModule = paramiko.RSAKey
        elif data['keytype'] == 'ECDSA':
            paramikoKeyModule = paramiko.ECDSAKey
        elif data['keytype'] == 'ED25519':
            paramikoKeyModule = paramiko.Ed25519Key
        else:
            logging.error('Unknown key type')
            return

        try:
            f = open(data['key'],'r')
            s = f.read()
            f.close()
            keyfile = io.StringIO(s)
            key = paramikoKeyModule.from_private_key(keyfile)
        except paramiko.ssh_exception.PasswordRequiredException:
            text, ok = QtWidgets.QInputDialog.getText(None, "Password", "Enter password", QtWidgets.QLineEdit.Password)
            if ok and text:
                keyfile.seek(0)
                try:
                    key = paramikoKeyModule.from_private_key(keyfile,password=text)
                except paramiko.ssh_exception.SSHException:
                    logging.error('Invalid password for {} key'.format(data['keytype']))
                    return

        sshSession = paramiko.SSHClient()
        sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            sshSession.connect(data['address'], username=data['user'], pkey=key, port=data['port'])
        except socket.gaierror:
            logging.error('Invalid address')
        except paramiko.ssh_exception.NoValidConnectionsError:
            logging.error('Invalid connection')
        except Exception as e:
            logging.error(str(e))
        else:
            logging.info('Successfully connected to {}'.format(data['address']))
            sessionItem.setData(sshSession,QtCore.Qt.UserRole+1)

    def onEditSession(self):

        selectedIndex = self.currentIndex()
        currentSessionData = self.model().data(selectedIndex,QtCore.Qt.UserRole)
        sessionDialog = SessionDialog(self,False, currentSessionData)

        if sessionDialog.exec_():
            newSessionData = sessionDialog.data()
            currentSessionData = self.model().data(selectedIndex,QtCore.Qt.UserRole)
            if currentSessionData['name'] == newSessionData['name']:
                self.model().setData(selectedIndex,newSessionData,QtCore.Qt.UserRole)
                self.model().setData(selectedIndex,'\n'.join(['{}: {}'.format(k,v) for k,v in newSessionData.items()]),QtCore.Qt.ToolTipRole)
            else:
                self.addSession(newSessionData)

    def onShowContextualMenu(self, point):

        menu = QtWidgets.QMenu()

        selectedItems = self.selectionModel().selectedRows()
        if not selectedItems:
            action = menu.addAction('Add ssh session')
            action.triggered.connect(self.onAddSession)
            menu.addAction(action)
            menu.exec_(QtGui.QCursor.pos())
        else:
            if selectedItems[0].parent().row() == -1:
                editAction = menu.addAction('Edit')
                editAction.triggered.connect(self.onEditSession)
                connectAction = menu.addAction('Connect')
                connectAction.triggered.connect(self.onConnect)
                menu.addAction(connectAction)
                addServerAction = menu.addAction('Add server')
                addServerAction.triggered.connect(self.onAddServer)
                menu.addAction(addServerAction)
                menu.exec_(QtGui.QCursor.pos())

