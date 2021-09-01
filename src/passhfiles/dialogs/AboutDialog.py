from PyQt5 import QtGui, QtWidgets

from passhfiles.__pkginfo__ import __version__
from passhfiles.utils.Platform import iconsDirectory

class AboutDialog(QtWidgets.QDialog):
    """Dialog used for showing global information about the application.
    """

    def __init__(self, parent):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QWidget): the parent widget
        """

        super(AboutDialog,self).__init__(parent)

        self._initUi()

        self.setWindowTitle('About passhfiles')

    def _initUi(self):
        """Setup the dialog.
        """

        pixmap = QtGui.QPixmap(str(iconsDirectory()/'passhfiles.png'))
        pixmap = pixmap.scaled(180,180)
        label = QtWidgets.QLabel()
        label.setPixmap(pixmap)

        mainLayout = QtWidgets.QHBoxLayout()

        about = QtWidgets.QTextEdit()
        about.setReadOnly(True)
        about.setText('''This is passhfiles version {}.

Developped at the Institut Laue Langevin
        
Developper: Eric Pellegrini (pellegrini[at]ill.fr)'''.format(__version__))

        mainLayout.addWidget(label)
        mainLayout.addWidget(about)

        self.setGeometry(0, 0, 600, 300)

        self.setLayout(mainLayout)
