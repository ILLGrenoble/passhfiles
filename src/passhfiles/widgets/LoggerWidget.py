import logging

from PyQt5 import QtCore, QtWidgets

class _EnhancedTextEdit(QtWidgets.QPlainTextEdit):

    def contextMenuEvent(self, point):
        """Pops up a contextual menu when the user right-clicks on the logger.

        Args:
            point (PyQt5.QtCore.QPoint): the point where the user right-clicked
        """

        popup_menu = self.createStandardContextMenu()

        popup_menu.addSeparator()
        popup_menu.addAction('Clear', self.on_clear_logger)
        popup_menu.addSeparator()
        popup_menu.addAction('Save as ...', self.on_save_logger)
        popup_menu.exec_(point.globalPos())

    def on_clear_logger(self):
        """Clear the logger
        """

        self.clear()

    def on_save_logger(self):
        """Save the logger contents to a file
        """

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')
        if not filename:
            return

        with open(filename, 'w') as fin:
            fin.write(self.toPlainText())

class LoggerWidget(QtCore.QObject,logging.Handler):
    
    sendLog = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        """Constructor.
        """

        super(LoggerWidget,self).__init__()
        self._widget = _EnhancedTextEdit(parent)
        self._widget.setReadOnly(True)

    def emit(self, record):
        """Emits a record.

        Args:
            record (logging.LogRecord): the emitted record
        """

        msg = self.format(record)

        self.sendLog.emit(msg)

    def widget(self):
        """Return the underlying widget used for displaying the log.

        Returns:
            PyQt5.QtWidgets.QWidget: the widget
        """

        return self._widget
