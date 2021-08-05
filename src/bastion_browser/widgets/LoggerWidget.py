import logging

from PyQt5 import QtWidgets

class _EnhancedTextEdit(QtWidgets.QPlainTextEdit):

    def contextMenuEvent(self, event):
        popup_menu = self.createStandardContextMenu()

        popup_menu.addSeparator()
        popup_menu.addAction('Clear', self.on_clear_logger)
        popup_menu.addSeparator()
        popup_menu.addAction('Save as ...', self.on_save_logger)
        popup_menu.exec_(event.globalPos())

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

class LoggerWidget(logging.Handler):
    
    def __init__(self, parent):

        super(LoggerWidget,self).__init__()
        self._widget = _EnhancedTextEdit(parent)
        self._widget.setReadOnly(True)

    def emit(self, record):
        """
        """

        msg = self.format(record)
        self._widget.appendPlainText(msg)

    @property
    def widget(self):
        """Return the underlying widget used for displaying the log.
        """

        return self._widget
