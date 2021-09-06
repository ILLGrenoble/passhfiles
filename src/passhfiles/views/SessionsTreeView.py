import logging

from PyQt5 import QtCore, QtGui, QtWidgets

from passhfiles.dialogs.SessionDialog import SessionDialog
from passhfiles.kernel.KeyStore import KEYSTORE
from passhfiles.models.SessionsModel import ServerNode, SessionNode, SessionsModel
from passhfiles.utils.Platform import sessionsDatabasePath
from passhfiles.utils.Security import checkAndGetSSHKey

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

        # Case where the user clicks in the view but not on an item or if the user clicks on a selected item --> deselect the currently selected item
        if ((index.row() == -1 and index.column() == -1) or selected):
            self.clearSelection()
            return

        node = index.internalPointer()
        if isinstance(node,SessionNode):
            sessionsModel = self.model()
            sessionsModel.registerSSHKey(index,True)

    def onAddSession(self):
        """Called when the user clicks on 'Add session' contextual menu item. Adds a new session to the underlying model.
        """

        sessionDialog = SessionDialog(self,True)

        if sessionDialog.exec_():
            sessionData = sessionDialog.data()
            sessionsModel = self.model()
            sessionsModel.addSession(sessionData)
            sessionIndex = sessionsModel.index(sessionsModel.rowCount()-1,0)
            sessionsModel.registerSSHKey(sessionIndex,True)
            sessionsModel.findServers(sessionIndex)
            sessionsModel.saveSessions(sessionsDatabasePath())

    def onBrowseFiles(self):
        """Called when the user left-clicks on a server node. Opens the local and remote file browsers.
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
        sessionDialog = SessionDialog(self,False,currentSessionData)

        if sessionDialog.exec_():
            newSessionData = sessionDialog.data()
            if currentSessionData['name'] == newSessionData['name']:
                sessionsModel.updateSession(selectedIndex, newSessionData)
            else:
                sessionsModel.moveSession(selectedIndex, newSessionData)

            sessionsModel.registerSSHKey(selectedIndex,True)
            sessionsModel.findServers(selectedIndex)
            sessionsModel.saveSessions(sessionsDatabasePath())

    def onFindServers(self):
        """Called when the user clicks on 'Find servers' contextual menu item. This will find automatically 
        all the servers behind the bastion for a given user.
        """

        sessionsModel = self.model()
        sessionIndex = self.currentIndex()

        sessionsModel.findServers(sessionIndex)
        sessionsModel.saveSessions(sessionsDatabasePath())

    def onOpenTerminal(self):
        """Called when the user clicks on 'Open terminal' contextual menu item. It opens a 
        terminal on the remote location. 
        """

        sessionsModel = self.model()
        serverIndex = self.currentIndex()
        sessionsModel.openTerminal(serverIndex)

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
                connectAction = menu.addAction('(Re)connect')
                connectAction.triggered.connect(self.onConnect)
                findServersAction = menu.addAction('Refresh servers list')
                findServersAction.triggered.connect(self.onFindServers)
                menu.addAction(findServersAction)
                menu.exec_(QtGui.QCursor.pos())
            elif isinstance(selectedItems[0].internalPointer(),ServerNode):
                openTerminalAction = menu.addAction('Open terminal')
                openTerminalAction.triggered.connect(self.onOpenTerminal)
                menu.addAction(openTerminalAction)
                menu.exec_(QtGui.QCursor.pos())
