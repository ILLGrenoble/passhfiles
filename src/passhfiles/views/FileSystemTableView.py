from genericpath import isdir
import pathlib

from PyQt5 import QtCore, QtGui, QtWidgets

from passhfiles.models.IFileSystemModel import IFileSystemModel
from passhfiles.utils.Gui import mainWindow

class FileSystemTableView(QtWidgets.QTableView):
    """Implements a view to the file system (local or remote). The view is implemented as a table view with four 
    columns where the first column is the name of a file or directory, the second column is the size of the file,
    the third column is the type of the entry (file or directory) and the fourth column is the date of the last 
    modification of the entry.
    """

    def __init__(self, *args, **kwargs):
        """Consructor.
        """

        super(FileSystemTableView,self).__init__(*args, **kwargs)

        self.setShowGrid(False)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self.onShowContextualMenu)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setSortingEnabled(True)

        self._menu = None

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()

    def dropEvent(self, event):
        """Event triggered when the dragged item is dropped into this widget.

        Args:
            PyQt5.QtGui.QDropEvent: the drop event
        """

        if event.source() == self:
            return

        # The source is outside the application (e.g. Nautilus file manager)
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            links = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    links.append(str(url.toLocalFile()))
                else:
                    links.append(str(url.toString()))

            selectedData = []
            for l in links:
                path = pathlib.Path(l)
                selectedData.append((l,path.is_dir(),True))
        else:
            selectedRows = [index.row() for index in event.source().selectionModel().selectedRows()]
            selectedData = event.source().model().getEntries(selectedRows)
        self.model().dropData(selectedData)

    def keyPressEvent(self, event):
        """Event triggered when user press a key of the keyboard.

        Args:
            PyQt5.QtGui.QKeyEvent: the key press event
        """
        
        key = event.key()

        if key == QtCore.Qt.Key_Delete:

            selectedRows = [index.row() for index in self.selectionModel().selectedRows()]

            self.model().removeEntries(selectedRows)

        elif key == QtCore.Qt.Key_C and (event.modifiers() & QtCore.Qt.ControlModifier):
            
            selectedRows = [index.row() for index in self.selectionModel().selectedRows()]

            self.model().copyData(selectedRows)

        elif key == QtCore.Qt.Key_V and (event.modifiers() & QtCore.Qt.ControlModifier):

            mw = mainWindow(self)
            self.model().pasteData(mw.copiedData())

        return super(FileSystemTableView,self).keyPressEvent(event)

    def initContextualMenu(self, selectedIndex):
        """Initializes the context menu.
        """

        self._menu = QtWidgets.QMenu()

        self._showHiddenFilesAction = self._menu.addAction('Show hidden files')
        self._showHiddenFilesAction.setCheckable(True)
        self._showHiddenFilesAction.setChecked(True)
        self._showHiddenFilesAction.triggered.connect(self.onShowHiddenFiles)
        self._menu.addAction(self._showHiddenFilesAction)

        self._createDirectoryAction = self._menu.addAction('Create Directory')
        self._createDirectoryAction.triggered.connect(self.onCreateDirectory)
        self._menu.addAction(self._createDirectoryAction)

        self._renameAction = self._menu.addAction('Rename')
        self._renameConnection = None
        self._menu.addAction(self._renameAction)

        self._openAction = self._menu.addAction('Open')
        self._openConnection = None
        self._menu.addAction(self._openAction)

        self._reloadAction = self._menu.addAction('Reload')
        self._reloadAction.triggered.connect(self.onReloadDirectory)
        self._reloadConnection = None
        self._menu.addAction(self._openAction)

        self._menu.addSeparator()

        self._favoritesMenu = QtWidgets.QMenu('Favorites')
        self._menu.addMenu(self._favoritesMenu)

    def onAddToFavorites(self, selectedRow):
        """Called when the user add a path to the favorites.
        """

        if self.model() is None:
            return

        self.model().addToFavorites(selectedRow)

    def onCreateDirectory(self):
        """Called when the user creates a directory.
        """

        if self.model() is None:
            return

        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename Entry Dialog', 'Enter new name:')
        if ok and text.strip():
            self.model().createDirectory(pathlib.Path(text.strip()))

    def onGoToFavorite(self, path):
        """Called when the user select one path among the favorites.
        
        Updates the file system with the selected directory.

        Args:
            path (str): the selected path
        """

        if self.model() is None:
            return

        self.model().setDirectory(path)

    def onOpenEntry(self,selectedIndex):
        """Called when the user open an entry.
        """

        self.model().onOpenEntry(selectedIndex)

    def onReloadDirectory(self):
        """Refresh the directory.
        """

        fileSystemModel = self.model()
        if fileSystemModel is None:
            return

        fileSystemModel.reloadDirectory()

    def onRenameEntry(self, selectedRow):
        """Called when the user rename one entry.

        Args:
            selectedRow (int): the index of the entry to rename
        """
        
        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename Entry Dialog', 'Enter new name:')
        if ok and text.strip():
            self.model().renameEntry(selectedRow, text.strip())

    def onShowContextualMenu(self, point):
        """Pops up a contextual menu when the user right-clicks on the file system.

        Args:
            point (PyQt5.QtCore.QPoint): the point where the user right-clicked
        """

        if self.model() is None:
            return

        selectedIndex = self.indexAt(point)
        selectedRow = selectedIndex.row()

        if self._menu is None:
            self.initContextualMenu(selectedIndex)

        if self._renameConnection is not None:
            self._renameAction.disconnect(self._renameConnection)
        self._renameConnection = self._renameAction.triggered.connect(lambda item, row=selectedRow: self.onRenameEntry(row))

        if self._openConnection is not None:
            self._openAction.disconnect(self._openConnection)
        self._openConnection = self._openAction.triggered.connect(lambda item, index=selectedIndex : self.onOpenEntry(index))

        self._menu.removeAction(self._favoritesMenu.menuAction())
        self._favoritesMenu = QtWidgets.QMenu('Favorites')

        try:
            if self.model().isDirectory(selectedRow):
                self._addToFavoritesAction = self._favoritesMenu.addAction('Add to favorites')
                self._addToFavoritesAction.triggered.connect(lambda item, row=selectedRow : self.onAddToFavorites(row))
        except IndexError:
            pass

        self._gotoFavoritesMenu = QtWidgets.QMenu('Go to')
        favorites = self.model().favorites()
        for fav in favorites:
            favAction = self._gotoFavoritesMenu.addAction(str(fav))
            favAction.triggered.connect(lambda item, f=fav : self.onGoToFavorite(f))

        self._favoritesMenu.addMenu(self._gotoFavoritesMenu)
        self._menu.addMenu(self._favoritesMenu)

        self._menu.exec_(QtGui.QCursor.pos())

    def onShowHiddenFiles(self, show):
        """Show/hide hidden files.

        Args:
            show (bool): indicates whether or not the files has to be showed
        """

        self.model().showHiddenFiles(show)

    def setModel(self, model):
        """Set the model.

        Args:
            LocalFileSystemModel or RemoteFileSystemModel: the model
        """

        super(FileSystemTableView,self).setModel(model)

        self.doubleClicked.connect(self.model().onOpenEntry)
