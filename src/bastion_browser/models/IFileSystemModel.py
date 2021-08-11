import abc
import os

from PyQt5 import QtCore, QtGui

import bastion_browser

class MyMeta(abc.ABCMeta, type(QtCore.QAbstractTableModel)):
    pass

class IFileSystemModel(QtCore.QAbstractTableModel, metaclass=MyMeta):

    sections = ['Name','Size','Type','Date Modified']

    addToFavoritesSignal = QtCore.pyqtSignal(str)

    def __init__(self, sshSession, serverIndex, startingDirectory, *args, **kwargs):

        super(IFileSystemModel,self).__init__(*args, **kwargs)

        self._directoryIcon = QtGui.QIcon(os.path.join(bastion_browser.__path__[0],'icons','directory.png'))
        self._fileIcon = QtGui.QIcon(os.path.join(bastion_browser.__path__[0],'icons','file.png'))

        self._entries = []

        self._sshSession = sshSession

        self._serverIndex = serverIndex

        self.setDirectory(startingDirectory)

    def addToFavorites(self):

        self.addToFavoritesSignal.emit(self._currentDirectory)

    @abc.abstractmethod
    def createDirectory(self, directoryName):
        pass

    def columnCount(self, parent=None):
        
        return 4

    def currentDirectory(self):

        return self._currentDirectory

    def data(self, index, role):

        if not index.isValid():
            return QtCore.QVariant()

        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole:
            return self._entries[row][col]

        elif role == QtCore.Qt.DecorationRole:
            if col == 0:
                return self._icons[row]

        elif role == QtCore.Qt.ToolTipRole:
            return self._currentDirectory

    @abc.abstractmethod
    def editFile(self, path):
        pass

    @abc.abstractmethod
    def favorites(self):
        pass

    def flags(self, index):

        return QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled

    def getEntries(self,indexes):

        entries = []

        for index in indexes:
            entry = self._entries[index]
            isDirectory = entry[2] == 'Folder'
            entries.append((os.path.join(self._currentDirectory,entry[0]),isDirectory))

        return entries

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return IFileSystemModel.sections[section]

    def onEnterDirectory(self, index):

        row = index.row()

        entry = self._entries[row]

        fullPath = os.path.normpath(os.path.join(self._currentDirectory,entry[0]))
        if entry[2] == 'Folder':
            self.setDirectory(fullPath)
        else:
            self.editFile(fullPath)

    @abc.abstractmethod
    def removeEntry(self, path):
        pass

    @abc.abstractmethod
    def renameEntry(self, selectedRow, newName):
        pass

    def rowCount(self, parent=None):
        
        return len(self._entries)

    def serverIndex(self):

        return self._serverIndex

    @abc.abstractmethod
    def setDirectory(self, directory):
        pass

    @abc.abstractmethod
    def transferData(self, data):
        pass
