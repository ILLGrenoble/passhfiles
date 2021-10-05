import abc
import pathlib

from PyQt5 import QtCore, QtGui

from passhfiles.utils.Platform import iconsDirectory

class MyMeta(abc.ABCMeta, type(QtCore.QAbstractTableModel)):
    pass

class IFileSystemModel(QtCore.QAbstractTableModel, metaclass=MyMeta):
    """Interface for a model of file system.
    """
    
    sections = ['Name','Size','Type','Owner','Date Modified']

    addToFavoritesSignal = QtCore.pyqtSignal(pathlib.PurePath)

    currentDirectoryChangedSignal = QtCore.pyqtSignal(pathlib.PurePath)

    dataCopiedSignal = QtCore.pyqtSignal(tuple)

    def __init__(self, serverIndex, startingDirectory, *args, **kwargs):
        """Constructor.

        Args:
            serverIndex (QtCore.QModelIndex): the index of the server to browse
            startingDirectory (str): the starting directory
        """

        super(IFileSystemModel,self).__init__(*args, **kwargs)

        self._directoryIcon = QtGui.QIcon(str(iconsDirectory().joinpath('directory.png')))
        self._fileIcon = QtGui.QIcon(str(iconsDirectory().joinpath('file.png')))

        self._entries = []

        self._serverIndex = serverIndex

        self._showHiddenFiles = True

        self._currentDirectory = None

        self.setDirectory(startingDirectory)

    def addToFavorites(self, selectedRow):
        """Add the current directory to favorites.
        """

        if selectedRow < 0 or selectedRow >= len(self._entries):
            return

        entry = self._entries[selectedRow][0]

        self.addToFavoritesSignal.emit(self._currentDirectory.joinpath(entry))

    def columnCount(self, parent=None):
        """Return the number of columns of the table.

        Returns:
            int: the number of columns
        """
        
        return 5

    def copyData(self, selectedRows):
        """Copy the data.

        Args:
            selectedRows (list of int): the row to copy
        """

        data = (self.server(),self.getEntries(selectedRows))

        self.dataCopiedSignal.emit(data)

    @abc.abstractmethod
    def createDirectory(self, directoryName):
        """Creates a directory.

        Args:
            directoryName (pathlib.Path): the name of the directory
        """

        pass

    @abc.abstractmethod
    def createNewFile(self, path):
        """Create a new file.

        Args:
            path: the path to the new file
        """

        pass

    @abc.abstractmethod
    def createTemporaryFile(self,index):
        """Copy the selected file to a temporary file on the local file system and returns both 
        temporary and actual file names.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the file

        Returns:
            2-tuple: respectively the path to the temporary and actual file names
        """

        pass

    def currentDirectory(self):
        """Returns the curren directory.

        Returns:
            pathlib.Path: the path to the current directory
        """

        return self._currentDirectory

    def data(self, index, role):
        """Returns the data for a given index and role.

        Args:
            index (QtCore.QModelIndex): the index
            role (int): the role
        """

        if not index.isValid():
            return QtCore.QVariant()

        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole:
            return self._entries[row][col]

        elif role == QtCore.Qt.DecorationRole:
            if col == 0:
                return self._entries[row][-1]

        elif role == QtCore.Qt.ToolTipRole:
            return self._currentDirectory

    @abc.abstractmethod
    def dropData(self, data):
        """Drop some data (directories and/or files).

        Args:
            data (list): the list of data to be transfered
        """

        pass

    @abc.abstractmethod
    def favorites(self):
        """Return the favorites paths.

        Returns:
            list: the list of favorites
        """

        pass

    def flags(self, index):
        """Retur the flags for a given index.

        Returns:
            int: the flag
        """

        return QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled
    
    @abc.abstractmethod
    def getEntries(self,indexes):
        """Returns the entries for a set of rows.

        Args:
            indexes (list of int): the indexes of the entries to fetch

        Returns:
            list: list of tuples where the 1st element is the full path of the entry, the 2nd element 
            is a boolean indicating whether the entry is a directory or not and the 3rd element is a 
            boolean indicatig whether the entry is local or not 
        """

        pass

    def headerData(self, section, orientation, role):
        """Return the header data for a given section, orientation and role.

        Args:
            section (int): the section
            orientation (QtCore.Qt.Horizontal or QtCore.Qt.Vertical): the orientation
            role (int): the role 
        """

        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return IFileSystemModel.sections[section]

    def isDirectory(self, row):
        """Return true if the entry is a directory.

        Args:
            row (int): the row
        """

        if row < 0 or row >= len(self._entries):
            return False

        entry = self._entries[row]

        return (entry[2] == 'Folder')

    def onOpenEntry(self, index):
        """Called when the user double clicks on a model's entry. 
        
        The entry can be a directory or a file. In case of a folder, the folder will be entered in and in 
        case of a file, the file will be opened with its default application.

        Args:
            index (QtCore.QModelIndex): the index of the entry
        """

        pass
    
    @abc.abstractmethod
    def openFile(self, path):
        """Open the file using its default application.

        Args:
            path (pathlib.Path): the path of the file to be edited
        """

        pass

    @abc.abstractmethod
    def pasteData(self, data):
        """Paste data to this model.

        Args
            data (tuple): the data to paste
        """

        pass

    def reloadDirectory(self):
        """Reload the directory.
        """

        self.setDirectory(self._currentDirectory)

    @abc.abstractmethod
    def removeEntries(self, path):
        """Remove some entries of the model.

        Args:
            selectedRows (list of int): the list of indexes of the entries to be removed
        """

        pass

    @abc.abstractmethod
    def renameEntry(self, selectedRow, newName):
        """Rename a given entry.

        Args:
            selectedRow (int): the index of the entry to rename
            newName (str): the new name
        """

        pass

    def rowCount(self, parent=None):
        """Returns the number of rows of the model.

        Args:
            parent (QtCore.QModelIndex): the parent index

        Returns:
            int: the number of rows
        """
        
        return len(self._entries)

    @abc.abstractmethod
    def saveFile(tempFile,actualFile):
        """Save a file that was opened for edition.

        Args:
            tempFile (pathlib.Path): the temporary file that contains the saved data
            actualFile (pathlib.PurePath): the actual path to which the file should be saved
        """

        pass


    def serverIndex(self):
        """Returns the index of the server item.

        Returns:
            QtCore.QModelIndex: the index of the server item
        """

        return self._serverIndex

    @abc.abstractmethod
    def setDirectory(self, directory):
        """Sets a directory.

        This will trigger a full update of the model.

        Args:
            directory (str): the directory
        """

        pass

    def showHiddenFiles(self, show):
        """Show or hide the hidden files. 
        """

        self._showHiddenFiles = show

        self.setDirectory(self._currentDirectory)

    def sort(self, col, order):
        """Sort the model.

        Args:
            col (int): the column
        """

        self.layoutAboutToBeChanged.emit()
        self._entries = sorted(self._entries, key=lambda x : (x[col] is not None, x[col]),reverse=order)
        self.layoutChanged.emit()

    def server(self):
        """Returns the server that host the file system.
        """
        
        return self._serverIndex.internalPointer().name()
