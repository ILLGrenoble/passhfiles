from datetime import datetime
import logging
import os
import platform
import shutil
import subprocess

import scp

from bastion_browser.models.IFileSystemModel import IFileSystemModel
from bastion_browser.utils.Numbers import sizeOf
from bastion_browser.utils.Platform import findOwner
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

    def openFile(self, path):
        """Open the file using its default application.

        Args:
            path: the path of the file to be edited
        """

        try:
            system = platform.system()
            if system == 'Linux':
                subprocess.call(['xdg-open',path])
            elif system == 'Darwin':
                subprocess.call(['open',path])
            elif system == 'Windows':
                subprocess.call(['start',path])
        except Exception as e:
            logging.error(str(e))

    def favorites(self):
        """Return the favorites paths.

        Returns:
            list: the list of favorites
        """

        return self._serverIndex.internalPointer().data(0)['local']

    def getEntries(self,indexes):
        """Returns the entries for a set of rows.

        Args:
            indexes (list of int): the indexes of the entries to fetch

        Returns:
            list: list of tuples where the 1st element is the full path of the entry, the 2nd element 
            is a boolean indicating whether the entry is a directory or not and the 3rd element is a 
            boolean indicatig whether the entry is local or not 
        """

        entries = []

        for index in indexes:
            entry = self._entries[index]
            isDirectory = entry[2] == 'Folder'
            entries.append((os.path.join(self._currentDirectory,entry[0]),isDirectory,True))

        return entries

    def onEnterDirectory(self, index):
        """Called when the user double clicks on a model's entry. 
        
        The entry can be a directory or a file. In case of a folder, the folder will be entered in and in 
        case of a file, the file will be opened in a text editor.

        Args:
            index (QtCore.QModelIndex): the index of the entry
        """

        row = index.row()

        entry = self._entries[row]

        fullPath = os.path.normpath(os.path.join(self._currentDirectory,entry[0]))
        if entry[2] == 'Folder':
            self.setDirectory(fullPath)
        else:
            self.openFile(fullPath)

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

        if not self._showHiddenFiles:
            contents = [c for c in contents if not c.startswith('.')]

        self._currentDirectory = directory

        # Sort the contents of the directory (first the sorted directories and then the sorted files)
        sortedContents = sorted([(c,True) for c in contents if os.path.isdir(os.path.join(self._currentDirectory,c))])
        sortedContents += sorted([(c,False) for c in contents if not os.path.isdir(os.path.join(self._currentDirectory,c))])

        self._entries = [['..',None,'Folder',None,None,self._directoryIcon]]
        for (name,isDirectory) in sortedContents:
            absPath = os.path.join(self._currentDirectory,name)
            size = None if isDirectory else sizeOf(os.path.getsize(absPath))
            typ = 'Folder' if isDirectory else 'File'
            modificationTime = str(datetime.fromtimestamp(os.path.getmtime(absPath))).split('.')[0]
            icon = self._directoryIcon if isDirectory else self._fileIcon
            owner = findOwner(absPath)
            self._entries.append([name,size,typ,owner,modificationTime,icon])

        self.layoutChanged.emit()

        self.currentDirectoryChangedSignal.emit(self._currentDirectory)

    def transferData(self, data):
        """Transfer some data (directories and/or files) from a remote host to the local file system.

        Args:
            data (list): the list of data to be transfered
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        progressBar.reset(len(data))
        for i, (d,isDirectory,isLocal) in enumerate(data):
            if isLocal:
                if isDirectory:
                    shutil.copytree(d,os.path.join(self._currentDirectory,os.path.basename(d)))
                else:
                    shutil.copy(d,self._currentDirectory)
            else:
                cmd = scp.SCPClient(sshSession.get_transport())
                cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(), d),self._currentDirectory, recursive=True)
            progressBar.update(i+1)

        self.setDirectory(self._currentDirectory)
