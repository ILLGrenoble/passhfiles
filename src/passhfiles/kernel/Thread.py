import time

from PyQt5 import QtCore

class RefreshFileSystemWorker(QtCore.QObject):

    updateFileSystems = QtCore.pyqtSignal()
        
    def run(self):
        """Run the worker.
        """

        while True:

            self.updateFileSystems.emit()

            time.sleep(1)
