import logging
import pathlib
import platform
import re
import subprocess
import tempfile

import scp

from passhfiles.models.IFileSystemModel import IFileSystemModel
from passhfiles.utils.Numbers import sizeOf
from passhfiles.utils.ProgressBar import progressBar
from passhfiles.utils.Security import runRemoteCmd

class RemoteFileSystemModel(IFileSystemModel):
    """Implements the IFileSystemModel interface in case of a remote file system.
    """

    def createDirectory(self, directoryName):
        """Creates a directory.

        Args:
            directoryName: the name of the directory
        """

        directoryName = self._currentDirectory.joinpath(directoryName)

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        serverNode = self._serverIndex.internalPointer()

        _, error = runRemoteCmd(sshSession,serverNode,'mkdir {}'.format(directoryName))
        if error:
            logging.error(error)
            return
        else:
            self.setDirectory(self._currentDirectory)

    def createNewFile(self, path):
        """Create a new file.

        Args:
            path: the path to the new file
        """

        newFilePath = self._currentDirectory.joinpath(re.escape(path))

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        serverNode = self._serverIndex.internalPointer()

        _, error = runRemoteCmd(sshSession,serverNode,'touch {}'.format(newFilePath))
        if error:
            logging.error(error)
            return
        else:
            self.setDirectory(self._currentDirectory)

    def createTemporaryFile(self,index):
        """Copy the selected file to a temporary file on the local file system and returns both 
        temporary and actual file names.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the file

        Returns:
            2-tuple: respectively the path to the temporary and actual file names
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        if sshSession is None:
            return

        row = index.row()

        entry = self._entries[row]

        actualFile = pathlib.PurePosixPath(self._currentDirectory.joinpath(entry[0]))

        tempFile = pathlib.Path(tempfile.mktemp(suffix=actualFile.suffix))
        cmd = scp.SCPClient(sshSession.get_transport())
        cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(),actualFile),str(tempFile), recursive=True)

        return tempFile, actualFile

    def dropData(self, data):
        """Drop some data (directories and/or files) from a local file system to the remote host.

        Args:
            data (list): the list of data to be transfered
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()        

        progressBar.reset(len(data))
        for i, (d,_,_) in enumerate(data):

            currentSubEntries = [entry[0] for entry in self._entries]
            base = d.stem + d.suffix
            num = 1
            while base in currentSubEntries:
                base = '{}_{}{}'.format(d.stem,num,d.suffix)
                num += 1

            targetFile = self._currentDirectory.joinpath(base)

            try:
                cmd = scp.SCPClient(sshSession.get_transport())
                cmd.put(str(d), remote_path='{}/{}'.format(self._serverIndex.internalPointer().name(),targetFile), recursive=True)
            except Exception as e:
                logging.error(str(e))
                pass
            progressBar.update(i+1)

        self.setDirectory(self._currentDirectory)

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
            entries.append((self._currentDirectory.joinpath(entry[0]),isDirectory,False))

        return entries

    def onOpenEntry(self, index):
        """Called when the user double clicks on a model's entry. 
        
        The entry can be a directory or a file. In case of a folder, the folder will be entered in and in 
        case of a file, the file will be opened with its default application.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the entry
        """

        row = index.row()

        entry = self._entries[row]

        if entry[0] == '..':
            fullPath = self._currentDirectory.parent
        else:
            fullPath = self._currentDirectory.joinpath(entry[0])

        if entry[2] == 'Folder':
            self.setDirectory(fullPath)
        else:
            self.openFile(fullPath)

    def openFile(self, path):
        """Open the file using its default application.

        Args:
            path: the path of the file to be edited
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        if sshSession is None:
            return
                
        try:
            tempFile = tempfile.mktemp(suffix=path.suffix)
            cmd = scp.SCPClient(sshSession.get_transport())
            cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(),str(path)),tempFile, recursive=True)
            system = platform.system()
            if system == 'Linux':
                subprocess.call(['xdg-open',tempFile])
            elif system == 'Darwin':
                subprocess.call(['open',tempFile])
            elif system == 'Windows':
                subprocess.call(['start',tempFile],shell=True)
        except Exception as e:
            logging.error(str(e))

    def pasteData(self, data):
        """Paste data to this model.

        Args
            data (tuple): the data to paste
        """

        if data is None:
            return

        server, entries = data

        if server != self._serverIndex.internalPointer().name():
            return

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        currentSubEntries = [entry[0] for entry in self._entries]
        progressBar.reset(len(entries))
        for i, (d,_,_) in enumerate(entries):

            target = d.name
            ext = d.suffix
            num = 1
            while target in currentSubEntries:
                target = '{}_{}{}'.format(d.stem,num,ext)
                num += 1

            try:
                cmd = scp.SCPClient(sshSession.get_transport())
                cmd.put(d, remote_path='{}/{}'.format(self._serverIndex.internalPointer().name(),str(self._currentDirectory.joinpath(target))), recursive=True)
            except Exception as e:
                logging.error(str(e))
                pass
            progressBar.update(i+1)

        self.setDirectory(self._currentDirectory)

    def removeEntries(self, selectedRow):
        """Remove some entries of the model.

        Args:
            selectedRows (list of int): the list of indexes of the entries to be removed
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        serverNode = self._serverIndex.internalPointer()

        for row in selectedRow[::-1]:
            selectedPath = self._currentDirectory.joinpath(re.escape(self._entries[row][0]))
            _, error = runRemoteCmd(sshSession,serverNode,'rm -rf {}'.format(selectedPath))
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
        
        oldName = self._currentDirectory.joinpath(re.escape(oldName))
        newName = self._currentDirectory.joinpath(newName)

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        serverNode = self._serverIndex.internalPointer()

        _, error = runRemoteCmd(sshSession,serverNode,'mv {} {}'.format(oldName,newName))
        if error:
            logging.error(error)
            return

        self._entries[selectedRow][0] = newName

        self.setDirectory(self._currentDirectory)

    def saveFile(self, tempFile, actualFile):
        """Save a file that was opened for edition.

        Args:
            tempFile (pathlib.Path): the temporary file that contains the saved data
            actualFile (pathlib.Path): the actual path to which the file should be saved
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()
        if sshSession is None:
            return

        currentSubEntries = [entry[0] for entry in self._entries]

        base = actualFile.stem + actualFile.suffix
    
        num = 1
        while base in currentSubEntries:
            base = '{}_{}{}'.format(actualFile.stem,num,actualFile.suffix)
            num += 1

        serverNode = self._serverIndex.internalPointer()

        backupFile = self._currentDirectory.joinpath(base)
        _, error = runRemoteCmd(sshSession,serverNode,'mv {} {}'.format(actualFile,backupFile))
        if error:
            logging.error(error)
            return

        try:
            cmd = scp.SCPClient(sshSession.get_transport())
            cmd.put(str(tempFile), remote_path='{}/{}'.format(self._serverIndex.internalPointer().name(),actualFile), recursive=True)
        except Exception as e:
            logging.error(str(e))

        self.setDirectory(self._currentDirectory)

    def setDirectory(self, directory):
        """Sets a directory.

        This will trigger a full update of the model.

        Args:
            directory (str): the directory
        """

        self._currentDirectory = directory

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        char = 'a' if self._showHiddenFiles else ''

        serverNode = self._serverIndex.internalPointer()
        output,error = runRemoteCmd(sshSession,serverNode,'ls --full-time -{}lpL {}'.format(char,self._currentDirectory))
        if error:
            logging.error(error)
            return
        
        self._entries = [['..',None,'Folder',None,None,self._directoryIcon]]
        contents = [l.strip() for l in output.split('\n')]

        # The 1st element of contents is always the total count of entries output by the ls command. It is not used.
        # For ls -a command the 2nd and 3rd entries are for . and .. directories. It is not used.
        if self._showHiddenFiles:
            contents = contents[3:] if len(contents) >= 4 else []
        else:
            contents = contents[1:] if len(contents) >= 2 else []

        for c in contents:
            words = [v.strip() for v in c.split()]
            typ = 'Folder' if words[-1].endswith('/') else 'File'
            size = sizeOf(int(words[4])) if typ == 'File' else None
            icon = self._directoryIcon if typ=='Folder' else self._fileIcon
            owner = words[2]
            date = words[5]
            time = words[6].split('.')[0]
            modificationTime = '{} {}'.format(date,time)
            name = words[-1][:-1] if typ=='Folder' else words[-1]
            self._entries.append([name,size,typ,owner,modificationTime,icon])

        sortedDirectories = sorted([v for v in self._entries if v[2]=='Folder'],key= lambda s : s[0].lower())
        sortedFiles = sorted([v for v in self._entries if v[2]=='File'],key= lambda s : s[0].lower())
        self._entries = sortedDirectories + sortedFiles

        self.layoutChanged.emit()

        self.currentDirectoryChangedSignal.emit(self._currentDirectory)