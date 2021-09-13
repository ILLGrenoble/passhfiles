import logging
import pathlib

from PyQt5 import QtCore, QtGui, QtWidgets

from passhfiles.dialogs.FileEditorDialog import FileEditorDialog
from passhfiles.models.IFileSystemModel import IFileSystemModel
from passhfiles.utils.Gui import mainWindow
from passhfiles.utils.String import isBinaryString

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

            self.onDeleteFile()

        elif key == QtCore.Qt.Key_C and (event.modifiers() & QtCore.Qt.ControlModifier):
            
            self.onCopyData()

        elif key == QtCore.Qt.Key_V and (event.modifiers() & QtCore.Qt.ControlModifier):

            self.onPasteData()

        return super(FileSystemTableView,self).keyPressEvent(event)

    def onAddToFavorites(self, selectedRow):
        """Called when the user adds a path to the favorites.

        Args:
            selectedRow (int): the row of the selected directory
        """

        if self.model() is None:
            return

        self.model().addToFavorites(selectedRow)

    def onCopyData(self):
        """Copy data.
        """

        selectedRows = [index.row() for index in self.selectionModel().selectedRows()]

        self.model().copyData(selectedRows)

    def onCreateDirectory(self):
        """Called when the user creates a directory.
        """

        if self.model() is None:
            return

        text, ok = QtWidgets.QInputDialog.getText(self, 'Create Directory Dialog', 'Enter directory name:')
        if ok and text.strip():
            self.model().createDirectory(text.strip())

    def onCreateFile(self):
        """Called when the user creates a new file.
        """

        if self.model() is None:
            return

        text, ok = QtWidgets.QInputDialog.getText(self, 'Create New File Dialog', 'Enter filename:')
        if ok and text.strip():
            self.model().createNewFile(text.strip())

    def onDeleteFile(self):
        """Delete the selected file.
        """

        selectedRows = [index.row() for index in self.selectionModel().selectedRows()]

        self.model().removeEntries(selectedRows)

    def onEditFile(self, index):
        """Edit a given file.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the selected file
        """

        tempFile, actualFile = self.model().createTemporaryFile(index)

        if isBinaryString(open(str(tempFile),'rb').read(1024)):
            logging.error('The file is a binary. Can not edit')
            return

        dialog = FileEditorDialog(tempFile, actualFile)

        dialog.fileSaved.connect(self.onSaveFile)

        dialog.exec_()

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

    def onPasteData(self):
        """Paste data.
        """

        mw = mainWindow(self)
        self.model().pasteData(mw.copiedData())

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

    def onSaveFile(self, tempFile, actualFile):
        """Save a file that was opened for edition.

        Args:
            tempFile (pathlib.Path): the temporary file that contains the saved data
            actualFile (pathlib.PurePath): the actual path to which the file should be saved
        """

        self.model().saveFile(tempFile, actualFile)

    def onShowContextualMenu(self, point):
        """Pops up a contextual menu when the user right-clicks on the file system.

        Args:
            point (PyQt5.QtCore.QPoint): the point where the user right-clicked
        """

        if self.model() is None:
            return

        selectedIndex = self.indexAt(point)
        selectedRow = selectedIndex.row()
        if selectedRow == -1:
            return

        entryIsADirectory =  self.model().isDirectory(selectedRow)

        menu = QtWidgets.QMenu()

        showHiddenFilesAction = menu.addAction('Show hidden files')
        showHiddenFilesAction.setCheckable(True)
        showHiddenFilesAction.setChecked(True)
        showHiddenFilesAction.triggered.connect(self.onShowHiddenFiles)

        menu.addSeparator()

        createDirectoryAction = menu.addAction('Create Directory')
        createDirectoryAction.triggered.connect(self.onCreateDirectory)

        newFileAction = menu.addAction('New File')
        newFileAction.triggered.connect(self.onCreateFile)

        deleteAction = menu.addAction('Delete')
        deleteAction.triggered.connect(self.onDeleteFile)

        renameAction = menu.addAction('Rename')
        renameAction.triggered.connect(lambda item, row=selectedRow: self.onRenameEntry(row))

        openAction = menu.addAction('Open')
        openAction.triggered.connect(lambda item, index=selectedIndex : self.onOpenEntry(index))

        if not entryIsADirectory:
            editAction = menu.addAction('Edit')
            editAction.triggered.connect(lambda item, index=selectedIndex : self.onEditFile(index))

        reloadAction = menu.addAction('Reload')
        reloadAction.triggered.connect(self.onReloadDirectory)

        menu.addSeparator()

        copyAction = menu.addAction('Copy')
        copyAction.triggered.connect(self.onCopyData)

        pasteAction = menu.addAction('Paste')
        pasteAction.triggered.connect(self.onPasteData)

        menu.addSeparator()

        favoritesMenu = QtWidgets.QMenu('Favorites')

        favoritesMenu = QtWidgets.QMenu('Favorites')

        if entryIsADirectory:
            addToFavoritesAction = favoritesMenu.addAction('Add to favorites')
            addToFavoritesAction.triggered.connect(lambda item, row=selectedRow : self.onAddToFavorites(row))

        gotoFavoritesMenu = QtWidgets.QMenu('Go to')
        favorites = self.model().favorites()
        for fav in favorites:
            favAction = gotoFavoritesMenu.addAction(str(fav))
            favAction.triggered.connect(lambda item, f=fav : self.onGoToFavorite(f))
        favoritesMenu.addMenu(gotoFavoritesMenu)
        menu.addMenu(favoritesMenu)

        menu.exec_(QtGui.QCursor.pos())

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
