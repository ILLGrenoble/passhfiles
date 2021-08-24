import os

from PyQt5 import QtGui, QtWidgets

from bastion_browser.__pkginfo__ import __version__
from bastion_browser.utils.Platform import iconsDirectory

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

        self.setWindowTitle('About bastion_browser')

    def _initUi(self):
        """Setup the dialog.
        """

        pixmap = QtGui.QPixmap(os.path.join(iconsDirectory(),'bastion_browser.png'))
        pixmap = pixmap.scaled(180,180)
        label = QtWidgets.QLabel()
        label.setPixmap(pixmap)

        mainLayout = QtWidgets.QHBoxLayout()

        about = QtWidgets.QTextEdit()
        about.setReadOnly(True)
        about.setText('''This is bastion_browser version {}.

Developped at the Institut Laue Langevin
        
Developper: Eric Pellegrini (pellegrini[at]ill.fr)'''.format(__version__))

        mainLayout.addWidget(label)
        mainLayout.addWidget(about)

        self.setGeometry(0, 0, 600, 300)

        self.setLayout(mainLayout)
