from datetime import datetime
import logging
import os
import shutil
import subprocess

import scp

from bastion_browser.kernel.Preferences import PREFERENCES
from bastion_browser.models.IFileSystemModel import IFileSystemModel
from bastion_browser.utils.Numbers import sizeOf
from bastion_browser.utils.ProgressBar import progressBar

class LocalFileSystemModel(IFileSystemModel):
    """Implements the IFileSystemModel interface in case of a local file system.
    """

    def createDirectory(self, directoryName):
        """Creates a directory.

        Args:
            directoryName: the name of the directory
        """

        if not os.path.isabs(directoryName):
            directoryName = os.path.join(self._currentDirectory,directoryName)

        try:
            os.makedirs(directoryName)
        except Exception as e:
            logging.error(str(e))
        else:
            self.setDirectory(self._currentDirectory)

    def editFile(self, path):
        """Edit the file using a text editor (set via the preferences settings).

        Args:
            path: the path of the file to be edited
        """

        if not PREFERENCES['editor']:
            logging.error('No text editor set in the preferences')
            return

        try:
            subprocess.call([PREFERENCES['editor'],path])
        except Exception as e:
            logging.error(str(e))

    def favorites(self):
        """Return the favorites paths.

        Returns:
            list: the list of favorites
        """

        return self._serverIndex.internalPointer().data(0)['local']

    def removeEntries(self, selectedRows):
        """Remove some entries of the model.

        Args:
            selectedRows (list of int): the list of indexes of the entries to be removed
        """

        for row in selectedRows[::-1]:
            selectedPath = os.path.join(self._currentDirectory,self._entries[row][0])
            if os.path.isdir(selectedPath):
                shutil.rmtree(selectedPath)
            else:
                os.remove(selectedPath)

        self.setDirectory(self._currentDirectory)

    def renameEntry(self, selectedRow, newName):
        """Rename a given entry.

        Args:
            selectedRow (int): the index of the entry to rename
            newName (str): the new name
        """

        oldName = self._entries[selectedRow][0]
        if oldName == newName:
            return

        allEntryNames = [v[0] for v in self._entries]
        if newName in allEntryNames:
            logging.info('{} already exists'.format(newName))
            return
        
        self._entries[selectedRow][0] = newName

        oldName = os.path.join(self._currentDirectory,oldName)
        newName = os.path.join(self._currentDirectory,newName)
        
        shutil.move(oldName,newName)

        self.layoutChanged.emit()

    def setDirectory(self, directory):
        """Sets a directory.

        This will trigger a full update of the model.

        Args:
            directory (str): the directory
        """

        if not os.path.isabs(directory):
            directory = os.path.abspath(directory)
        
        # If the input argument was a filename, get its base directory
        if not os.path.isdir(directory):
            directory = os.path.dirname(directory)

        try:
            contents = os.listdir(directory)
        except PermissionError as e:
            logging.error(str(e))
            return

        self._currentDirectory = directory

        # Sort the contents of the directory (.. first, then the sorted directories and finally the sorted files)
        sortedContents = [('..',True)]
        sortedContents += sorted([(c,True) for c in contents if os.path.isdir(os.path.join(self._currentDirectory,c))])
        sortedContents += sorted([(c,False) for c in contents if not os.path.isdir(os.path.join(self._currentDirectory,c))])

        self._entries = []
        self._icons = []
        for (name,isDirectory) in sortedContents:
            absPath = os.path.join(self._currentDirectory,name)
            size = None if isDirectory else sizeOf(os.path.getsize(absPath))
            typ = 'Folder' if isDirectory else 'File'
            modificationTime = str(datetime.fromtimestamp(os.path.getmtime(absPath))).split('.')[0]
            icon = self._directoryIcon if isDirectory else self._fileIcon
            self._entries.append([name,size,typ,modificationTime])
            self._icons.append(icon)

        self.layoutChanged.emit()

    def transferData(self, data):
        """Transfer some data (directories and/or files) from a remote host to the local file system.

        Args:
            data (list): the list of data to be transfered
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        progressBar.reset(len(data))
        for i, (d,_) in enumerate(data):
            cmd = scp.SCPClient(sshSession.get_transport())
            cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(), d),self._currentDirectory, recursive=True)
            progressBar.update(i+1)

        self.setDirectory(self._currentDirectory)
