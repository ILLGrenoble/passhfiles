from PyQt5 import QtCore, QtGui, QtWidgets

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

    def onShowContextualMenu(self, point):

        menu = QtWidgets.QMenu()

        selectedRow = self.indexAt(point).row()

        action = menu.addAction('Rename')
        action.triggered.connect(lambda : self.onRenameEntry(selectedRow))

        menu.addAction(action)
        menu.exec_(QtGui.QCursor.pos())

    def onRenameEntry(self, selectedRow):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Rename Entry Dialog', 'Enter new name:')
        if ok and text.strip():
            self.model().renameEntry(selectedRow, text.strip())

    def setModel(self, model):

        super(FileSystemTableView,self).setModel(model)

        self.doubleClicked.connect(self.model().onEnterDirectory)
