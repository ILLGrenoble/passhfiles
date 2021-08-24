import collections
import io
import logging
import os
import paramiko
import socket
import time

import yaml

from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser import REFKEY
from bastion_browser.utils.Platform import iconsDirectory, sessionsDatabasePath

class RootNode:
    """Implements the root object of the SessionsModel.
    """
    
    def __init__(self):
        """Constructor.
        """

        self._children = []

    def addChild(self, child):
        """Add a child.
        
        The child must be a SessionNode.
        """
        
        if not isinstance(child,SessionNode):
            return

        child._parent = self
        self._children.append(child)

    def child(self, row):
        """Return the child for a given row.

        Args:
            row (int): the row

        Returns:
            SessionNode: the child
        """

        if row >= 0 and row < self.childCount():
            return self._children[row]

    def childCount(self):
        """Return the number of children of the root node.

        Returns:
            int: the number of children
        """

        return len(self._children)

    def clear(self):
        """Clear the root node.
        """

        self._children = []

    def columnCount(self):
        """Returns the number of columns of the root node.

        Returns:
            int: the number of columns
        """
        
        return 1

    def data(self, column):
        """Returns the data stored in the node.

        Returns:
            None: the data
        """
        
        return None

    def parent(self):
        """Return the parent of the root node.

            None: the parent
        """
        
        return None

    def removeChild(self, child):
        """Remove a child from the children list.

        Args:
            SessionNode: the child to be removed
        """

        if child in self._children:
            del self._children[self._children.index(child)]

    def row(self):
        """Returns the row of this node regarding its parent.

        Returns:
            int: the row
        """

        return 0

class SessionNode:
    """Implements a session node of the SessionsModel.
    """
    
    def __init__(self, data, parent):
        """Constructor.

        Args:
            data (dict): the session data
            parent (RootNode): the root node
        """
        
        self._data = data

        self._children = []
        self._parent = parent
        self._sshSession = None

    def addChild(self, child):
        """Add a child.
        
        The child must be a ServerNode.
        """
        
        if not isinstance(child,ServerNode):
            return

        child._parent = self
        self._children.append(child)

    def child(self, row):
        """Return the child for a given row.

        Args:
            row (int): the row

        Returns:
            ServerNode: the child
        """

        if row >= 0 and row < self.childCount():
            return self._children[row]

    def childCount(self):
        """Return the number of children of the root node.

        Returns:
            int: the number of children
        """

        return len(self._children)

    def columnCount(self):
        """Returns the number of columns of the root node.

        Returns:
            int: the number of columns
        """

        return 1

    def data(self, column):
        """Returns the data stored in the node.

        Returns:
            dict: the data
        """

        return self._data

    def parent(self):
        """Return the parent of the session node.

            RootNode: the parent
        """

        return self._parent

    def removeChild(self, child):
        """Remove a child from the children list.

        Args:
            SessionNode: the child to be removed
        """

        if child in self._children:
            del self._children[self._children.index(child)]

    def row(self):
        """Returns the row of this node regarding its parent.

        Returns:
            int: the row
        """

        return self._parent._children.index(self)

    def setData(self, data):
        """Sets the data for this session node.

        Args:
            data (dict): the data
        """

        self._data = data

    def setSSHSession(self, sshSession):
        """Set the SSH session.

        Args:
            sshSession (paramiko.client.SSHClient): the SSH session
        """

        self._sshSession = sshSession

    def sshSession(self):
        """Returns the SSH session.

        Returns:
            paramiko.client.SSHClient: the SSH session. None if not connected.
        """

        return self._sshSession

class ServerNode:
    """Implements a server node of the SessionsModel.
    """

    def __init__(self, name, parent):
        """Constructor.

        Args:
            name: the name of the server.
            parent (SessionNode): the parent
        """

        self._name = name

        self._parent = parent

        self._favorites = {'local': [], 'remote': []}

    def addChild(self, child):
        """Add a child.
        """

        pass

    def addFavorite(self, fileSystemType, path):
        """Add a favorite path to the favorites.

        Args:
            fileSystemType: either 'local' or 'remote'
            path (str): the path to be added to favorites
        """

        if not fileSystemType in ('local','remote'):
            return

        if not path in self._favorites[fileSystemType]:
            self._favorites[fileSystemType].append(path)

    def child(self, row):
        """Return the child for a given row.

        Args:
            row (int): the row

        Returns:
            None
        """

        return None

    def childCount(self):
        """Return the number of children of the root node.

        Returns:
            int: the number of children
        """

        return 0

    def columnCount(self):
        return 1

    def data(self, column):
        """Returns the data stored in the node.

        Returns:
            dict: the data
        """

        return self._favorites

    def name(self):
        """Return the name of the server.

        Returns:
            str: the server's name
        """
        
        return self._name

    def parent(self):
        """Return the parent of the server node.

            SessionNode: the parent
        """

        return self._parent

    def removeChild(self, child):
        """Remove a child from the children list.
        """

        pass

    def row(self):
        """Returns the row of this node regarding its parent.

        Returns:
            int: the row
        """

        return self._parent._children.index(self)

class SessionsModel(QtCore.QAbstractItemModel):
    """Implements a model for storing the SSH sessions.
    """

    SessionData = QtCore.Qt.UserRole

    SSHSession = QtCore.Qt.UserRole + 1

    def __init__(self):
        """The constructor.
        """

        QtCore.QAbstractItemModel.__init__(self)
        self._root = RootNode()

    def addChild(self, node, parentIndex):
        """Add a node to a given index.

        Args:
            node (RootNode|SessionNode|ServerNode): the node
            parentIndex (PyQt5.QtCore.QModelIndex): the index 
        """
        
        if not isinstance(node,(RootNode,SessionNode,ServerNode)):
            return

        if not parentIndex or not parentIndex.isValid():
            parent = self._root
        else:
            parent = parentIndex.internalPointer()
        parent.addChild(node)

    def addServer(self, serverName, sessionNode):
        """Add a server to a given session.

        Args:
            serverName (str): the name of the server
            sessionNode (SessionNode): the session node
        """

        servers = [sessionNode.child(i).name() for i in range(sessionNode.childCount())]
        if serverName in servers:
            logging.error('A server with name {} already exists'.format(serverName))
            return

        sessionNode.addChild(ServerNode(serverName,sessionNode))
        self.layoutChanged.emit()

    def addSession(self,data):
        """Add a new session to the model.

        Args:
            data (dict): the session data
        """

        sessionNode = SessionNode(data, self._root)
        for server in data.get('servers',[]):
            serverNode = ServerNode(server,sessionNode)
            for fsType, files in data['servers'][server].items():
                for f in files:
                    serverNode.addFavorite(fsType,f)
            sessionNode.addChild(serverNode)
        self._root.addChild(sessionNode)
        self.layoutChanged.emit()

    def addToFavorites(self, serverIndex, fileSystemType, currentDirectory):
        """Add a favorite to a server.

        Args:
            serverIndex (PyQt5.QtCore.QModelIndex): the server index
            fileSystemType (str): either 'local' or 'remote'
            currentDirectory (str): the path to be added to favorites
        """

        serverNode = serverIndex.internalPointer()
        serverNode.addFavorite(fileSystemType,currentDirectory)

    def clear(self):
        """Clear the model.
        """

        self.beginResetModel()
        self._root.clear()
        self.endResetModel()

    def columnCount(self, index):
        """Return the column count of the model for a given index.

        Args:
            index (PyQt5.QtCore.QmodelIndex): the index
        """

        if index is None or not index.isValid():
            return self._root.columnCount()
        return index.internalPointer().columnCount()

    def connect(self, sessionIndex):
        """Connect a given session.
        """

        sessionNode = sessionIndex.internalPointer()
        data = sessionNode.data(0)

        if data['keytype'] == 'RSA':
            paramikoKeyModule = paramiko.RSAKey
        elif data['keytype'] == 'ECDSA':
            paramikoKeyModule = paramiko.ECDSAKey
        elif data['keytype'] == 'ED25519':
            paramikoKeyModule = paramiko.Ed25519Key
        else:
            logging.error('Unknown key type')
            return

        password = REFKEY.decrypt(data['password']).decode() if data['password'] is not None else None

        try:
            f = open(data['key'],'r')
            s = f.read()
            f.close()
            keyfile = io.StringIO(s)
            key = paramikoKeyModule.from_private_key(keyfile,password=password)
        except Exception as e:
            logging.error(str(e))
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
            sessionNode.setSSHSession(sshSession)
            logging.info('Successfully connected to {}'.format(data['address']))

    def data(self, index, role):
        """Return the data for a given index and role.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index
            role (int): the role
        """
        
        if not index.isValid():
            return None
        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole:
            if isinstance(node,SessionNode):
                return node.data(index.column())['name']
            elif isinstance(node,ServerNode):
                return node.name()
            else:
                return None
        elif role == QtCore.Qt.DecorationRole:
            if isinstance(node,SessionNode):
                return QtGui.QIcon(os.path.join(iconsDirectory(),'session.png'))
            elif isinstance(node,ServerNode):
                return QtGui.QIcon(os.path.join(iconsDirectory(),'server.png'))
            else:
                return None
        elif role == QtCore.Qt.ToolTipRole:
            if isinstance(node,SessionNode):
                data = node.data(0)
                tooltip = []
                for k,v in data.items():
                    if k == 'password':
                        continue
                    if k == 'servers':
                        tooltip.append(('servers',list(v.keys())))
                    else:
                        tooltip.append((k,v))
                return '\n'.join(['{}: {}'.format(k,v) for k,v in tooltip])
            else:
                return None
        elif role == SessionsModel.SessionData:
            if isinstance(node,SessionNode):
                return node.data(index.column())
            elif isinstance(node,ServerNode):
                return node.data(index.column())
            else:
                return None
        elif role == SessionsModel.SSHSession:
            if isinstance(node,SessionNode):
                return node.sshSession()
            else:
                return None

        return None

    def findServers(self, sessionIndex):
        """Find the servers bound to a bastion session and add them to the model.

        Args:
            sessionIndex (PyQt5.QtCore.QModelIndex): the session index
        """

        sessionNode = sessionIndex.internalPointer()
        sshSession = sessionNode.sshSession()
        if sshSession is None:
            logging.error('Not connected to bastion server')
            return

        shell = sshSession.invoke_shell()

        out = ''
        time.sleep(1)

        while shell.recv_ready():
            out += shell.recv(2048).decode()
        out = out.split('\n')[2:-1]
        servers = [l.split()[1].strip() for l in out]

        for server in servers:
            sessionNode.addChild(ServerNode(server,sessionNode))

        self.layoutChanged.emit()

    def index(self, row, column, parentIndex=QtCore.QModelIndex()):
        """Return the index from a row and a column regarding to a given parent.

        Args:
            row (int): the row
            column (int): the column
            parentIndex (PyQt5.QtCore.QModelIndex): the parent index
        """

        if not parentIndex or not parentIndex.isValid():
            parent = self._root
        else:
            parent = parentIndex.internalPointer()

        if not QtCore.QAbstractItemModel.hasIndex(self, row, column, parentIndex):
            return QtCore.QModelIndex()

        child = parent.child(row)
        if child:
            return QtCore.QAbstractItemModel.createIndex(self, row, column, child)
        else:
            return QtCore.QModelIndex()

    def loadSessions(self, sessionsFile):
        """Load existing sessions from a session file.

        Args:
            sessionsFile: the YAML file containing the sessions
        """

        if not os.path.exists(sessionsFile):
            logging.error('The session file {} does not exist'.format(sessionsFile))
            return

        try:
            with open(sessionsFile,'r') as fin:
                sessions = yaml.unsafe_load(fin)
        except Exception as e:
            logging.error(str(e))
            return

        self.clear()

        for session in sessions:
            self.addSession(session)

        logging.info('Sessions successfully loaded from {}'.format(sessionsFile))

    def moveSession(self, sessionIndex, newSessionData):
        """Move a session to another one.

        Args:
            sessionIndex (PyQt5.QtCore.QModelIndex): the index of the session
            newSessionData (dict): the session data
        """

        serverNodes = [self.index(i,0,sessionIndex).internalPointer() for i in range(self.rowCount(sessionIndex))]
        newSessionData['servers'] = collections.OrderedDict([(n.name(),n.data(0)) for n in serverNodes])
        self.removeRow(sessionIndex,sessionIndex.parent())
        self.addSession(newSessionData)

    def parent(self, index):
        """Return the parent index of a given index.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index
        """
        
        if index.isValid():
            p = index.internalPointer().parent()
            if p:
                return QtCore.QAbstractItemModel.createIndex(self, p.row(), 0, p)
        return QtCore.QModelIndex()

    def removeRow(self, index, parentIndex):
        """Remove a row from the model.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index to remove
            parentIndex (PyQt5.QtCore.QModelIndex): the parent index of the index to remove
        """

        node = index.internalPointer()
        parentNode = parentIndex.internalPointer()
        if parentNode is None:
            return

        self.beginRemoveRows(parentIndex,index.row(),index.row())
        parentNode.removeChild(node)
        self.endRemoveRows()

    def root(self):
        """Return the root node.

        Returns:
            RootNode: the root node
        """
        
        return self._root

    def rowCount(self, index=None):
        """Return the row count of the model for a given index.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index
        """

        if index is None or not index.isValid():
            return self._root.childCount()
    
        return index.internalPointer().childCount()

    def saveSessions(self, sessionsFile):
        """Save the current sessions to a YAML file.

        Args:
            sessionsFile (str): the path to the sessions file
        """

        sessionNodes = [self._root.child(i) for i in range(self._root.childCount())]

        sessionsData = []
        for sessionNode in sessionNodes:
            data = sessionNode.data(0)
            serverNodes = [sessionNode.child(i) for i in range(sessionNode.childCount())]
            serverNames = [serverNode.name() for serverNode in serverNodes]
            serverFavorites = [serverNode.data(0) for serverNode in serverNodes]
            data['servers'] = collections.OrderedDict()
            for server,favorites in zip(serverNames,serverFavorites):
                data['servers'][server] = favorites
            sessionsData.append(data)
        
        try:
            with open(sessionsFile,'w') as fout:
                yaml.dump(sessionsData,fout)
        except Exception as e:
            logging.error(str(e))
            return
        else:
            logging.info('Session successfully saved to {}'.format(sessionsFile))
        
    def updateSession(self, sessionIndex, newSessionData):
        """Update a given session with new data.

        Args:
            sessionIndex (PyQt5.QtCore.QModelIndex): the index of the session
            newSessionData (dict): the session data
        """

        serverNodes = [self.index(i,0,sessionIndex).internalPointer() for i in range(self.rowCount(sessionIndex))]
        newSessionData['servers'] = collections.OrderedDict([(n.name(),n.data(0)) for n in serverNodes])

        sessionNode = sessionIndex.internalPointer()
        sessionNode.setData(newSessionData)
        self.layoutChanged.emit()

