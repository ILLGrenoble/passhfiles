from genericpath import isdir
import os

from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser.models.IFileSystemModel import IFileSystemModel
from bastion_browser.utils.Gui import mainWindow

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

            selectedData = [(l,os.path.isdir(l),True) for l in links]
        else:
            selectedRows = [index.row() for index in event.source().selectionModel().selectedRows()]
            selectedData = event.source().model().getEntries(selectedRows)
        self.model().transferData(selectedData)

    def keyPressEvent(self, event):
        """Event triggered when user press a key of the keyboard.

        Args:
            PyQt5.QtGui.QKeyEvent: the key press event
        """
        
        key = event.key()

        if key == QtCore.Qt.Key_Delete:

            selectedRows = [index.row() for index in self.selectionModel().selectedRows()]

            self.model().removeEntries(selectedRows)

        return super(FileSystemTableView,self).keyPressEvent(event)

    def onAddToFavorites(self):
        """Called when the user add a path to the favorites.
        """

        if self.model() is None:
            return

        self.model().addToFavorites()

    def onCreateDirectory(self):
        """Called when the user creates a directory.
        """

        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename Entry Dialog', 'Enter new name:')
        if ok and text.strip():
            self.model().createDirectory(text.strip())

    def onGoToFavorite(self, path):
        """Called when the user select one path among the favorites.
        
        Updates the file system with the selected directory.

        Args:
            path (str): the selected path
        """

        self.model().setDirectory(path)

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

        menu = QtWidgets.QMenu()

        selectedRow = self.indexAt(point).row()

        createDirectoryAction = menu.addAction('Create Directory')
        createDirectoryAction.triggered.connect(self.onCreateDirectory)
        menu.addAction(createDirectoryAction)

        renameAction = menu.addAction('Rename')
        renameAction.triggered.connect(lambda : self.onRenameEntry(selectedRow))
        menu.addAction(renameAction)

        menu.addSeparator()

        addToFavoritesAction = menu.addAction('Add to favorites')
        addToFavoritesAction.triggered.connect(self.onAddToFavorites)
        menu.addAction(addToFavoritesAction)

        favoritesMenu = QtWidgets.QMenu('Favorites')

        favorites = self.model().favorites()
        for fav in favorites:
            favAction = favoritesMenu.addAction(fav)
            favAction.triggered.connect(lambda : self.onGoToFavorite(fav))

        menu.addMenu(favoritesMenu)

        menu.exec_(QtGui.QCursor.pos())

    def setModel(self, model):
        """Set the model.

        Args:
            LocalFileSystemModel or RemoteFileSystemModel: the model
        """

        super(FileSystemTableView,self).setModel(model)

        self.doubleClicked.connect(self.model().onEnterDirectory)
