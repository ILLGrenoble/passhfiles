from PyQt5 import QtCore, QtGui, QtWidgets

from bastion_browser.models.IFileSystemModel import IFileSystemModel
from bastion_browser.utils.Gui import mainWindow

class FileSystemTableView(QtWidgets.QTableView):

    def __init__(self, *args, **kwargs):

        super(FileSystemTableView,self).__init__(*args, **kwargs)

        self.setShowGrid(False)
        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self.onShowContextualMenu)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)

    def dropEvent(self, event):
        """Event triggered when the dragged item is dropped into this widget.
        """

        if event.source() == self:
            return

        selectedRows = [index.row() for index in event.source().selectionModel().selectedRows()]

        selectedData = event.source().model().getEntries(selectedRows)

        self.model().transferData(selectedData)

    def keyPressEvent(self, event):
        
        key = event.key()

        if key == QtCore.Qt.Key_Delete:

            selectedRows = [index.row() for index in self.selectionModel().selectedRows()]

            self.model().removeEntry(selectedRows)

        return super(FileSystemTableView,self).keyPressEvent(event)

    def onAddToFavorites(self):

        if self.model() is None:
            return

        self.model().addToFavorites()

    def onCreateDirectory(self):

        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename Entry Dialog', 'Enter new name:')
        if ok and text.strip():
            self.model().createDirectory(text.strip())

    def onGoToFavorite(self, path):

        self.model().setDirectory(path)

    def onRenameEntry(self, selectedRow):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename Entry Dialog', 'Enter new name:')
        if ok and text.strip():
            self.model().renameEntry(selectedRow, text.strip())

    def onShowContextualMenu(self, point):

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

        super(FileSystemTableView,self).setModel(model)

        self.doubleClicked.connect(self.model().onEnterDirectory)
