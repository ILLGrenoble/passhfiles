import logging
import os
import platform
import subprocess
import tempfile

import scp

from bastion_browser.kernel.Preferences import PREFERENCES
from bastion_browser.models.IFileSystemModel import IFileSystemModel
from bastion_browser.utils.Numbers import sizeOf
from bastion_browser.utils.ProgressBar import progressBar

class RemoteFileSystemModel(IFileSystemModel):
    """Implements the IFileSystemModel interface in case of a remote file system.
    """

    def createDirectory(self, directoryName):
        """Creates a directory.

        Args:
            directoryName: the name of the directory
        """

        directoryName = os.path.join(self._currentDirectory,directoryName)

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        _, _, stderr = sshSession.exec_command('{} mkdir {}'.format(self._serverIndex.internalPointer().name(), directoryName))
        error = stderr.read().decode()
        if error:
            logging.error(error)
            return
        else:
            self.setDirectory(self._currentDirectory)

    def editFile(self, path):
        """Edit the file using a text editor (set via the preferences settings).

        Args:
            path: the path of the file to be edited
        """

        editor = PREFERENCES['editor']
        if not editor:
            logging.error('No text editor set in the preferences')
            if platform.system() == 'Linux':
                editor = '/usr/bin/xdg-open'
                logging.info('xdg-open will be used as a replacement')
            else:
                return

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        tempFile = tempfile.mktemp()
        cmd = scp.SCPClient(sshSession.get_transport())
        cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(),path),tempFile, recursive=True)
        try:
            subprocess.call([editor,tempFile])
        except Exception as e:
            logging.error(str(e))

    def favorites(self):
        """Return the favorites paths.

        Returns:
            list: the list of favorites
        """

        return self._serverIndex.internalPointer().data(0)['remote']

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
            entries.append((os.path.join(self._currentDirectory,entry[0]),isDirectory,False))

        return entries

    def removeEntries(self, selectedRow):
        """Remove some entries of the model.

        Args:
            selectedRows (list of int): the list of indexes of the entries to be removed
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        for row in selectedRow[::-1]:
            selectedPath = os.path.join(self._currentDirectory,self._entries[row][0])
            _, _, stderr = sshSession.exec_command('{} rm -rf {}'.format(self._serverIndex.internalPointer().name(), selectedPath))
            error = stderr.read().decode()
            if error:
                logging.error(error)
                continue

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
        
        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        _, _, stderr = sshSession.exec_command('{} mv {} {}'.format(self._serverIndex.internalPointer().name(), oldName,newName))
        error = stderr.read().decode()
        if error:
            logging.error(error)
            return

        self.setDirectory(self._currentDirectory)

    def setDirectory(self, directory):
        """Sets a directory.

        This will trigger a full update of the model.

        Args:
            directory (str): the directory
        """

        self._currentDirectory = directory

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        _, stdout, stderr = sshSession.exec_command('{} ls --group-directories --full-time -alpL {}'.format(self._serverIndex.internalPointer().name(),self._currentDirectory))
        error = stderr.read().decode()
        if error:
            logging.error(error)
            return
        
        contents = [l.strip() for l in stdout.readlines()]
        if len(contents) == 1:
            return
                
        contents = contents[2:]
        self._entries = []
        for c in contents:
            words = [v.strip() for v in c.split()]
            typ = 'Folder' if words[-1].endswith('/') else 'File'
            size = sizeOf(int(words[4])) if typ == 'Folder' else None
            icon = self._directoryIcon if typ=='Folder' else self._fileIcon
            owner = words[2]
            date = words[5]
            time = words[6].split('.')[0]
            modificationTime = '{} {}'.format(date,time)
            name = words[-1][:-1] if typ=='Folder' else words[-1]
            self._entries.append([name,size,typ,owner,modificationTime,icon])

        self.layoutChanged.emit()

    def transferData(self, data):
        """Transfer some data (directories and/or files) from a local file system to the remote host.

        Args:
            data (list): the list of data to be transfered
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        progressBar.reset(len(data))
        for i, (d,_,_) in enumerate(data):
            cmd = scp.SCPClient(sshSession.get_transport())
            cmd.put(d, remote_path='{}/{}'.format(self._serverIndex.internalPointer().name(),self._currentDirectory), recursive=True)
            progressBar.update(i+1)

        self.setDirectory(self._currentDirectory)
