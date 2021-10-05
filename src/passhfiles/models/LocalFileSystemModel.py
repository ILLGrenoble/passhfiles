from datetime import datetime
import logging
import os
import pathlib
import platform
import re
import shutil
import subprocess
import tempfile

import scp

from passhfiles.models.IFileSystemModel import IFileSystemModel
from passhfiles.utils.Numbers import sizeOf
from passhfiles.utils.Platform import findOwner
from passhfiles.utils.ProgressBar import progressBar

class LocalFileSystemModel(IFileSystemModel):
    """Implements the IFileSystemModel interface in case of a local file system.
    """

    def createDirectory(self, directoryName):
        """Creates a directory.

        Args:
            directoryName (pathlib.Path): the name of the directory
        """

        if not directoryName.is_absolute():
            directoryName = self._currentDirectory.joinpath(directoryName)

        try:
            directoryName.mkdir()
        except Exception as e:
            logging.error(str(e))
        else:
            self.setDirectory(self._currentDirectory)

    def createNewFile(self, path):
        """Create a new file.

        Args:
            path: the path to the new file
        """

        newFilePath = self._currentDirectory.joinpath(path)
        try:
            fout = open(str(newFilePath),'w')
        except Exception as e:
            logging.error(str(e))
        else:
            fout.close()

        self.setDirectory(self._currentDirectory)

    def createTemporaryFile(self,index):
        """Copy the selected file to a temporary file on the local file system and returns both 
        temporary and actual file names.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the file

        Returns:
            2-tuple: respectively the path to the temporary and actual file names
        """

        row = index.row()

        entry = self._entries[row]

        actualFile = pathlib.PurePath(self._currentDirectory.joinpath(entry[0]))

        tempFile = pathlib.Path(tempfile.mktemp(suffix=actualFile.suffix))

        shutil.copy(str(actualFile),str(tempFile))

        return tempFile, actualFile

    def dropData(self, data):
        """Drop some data (directories and/or files) from a remote host to the local file system.

        Args:
            data (list): the list of data to be transfered
        """

        sshSession = self._serverIndex.parent().internalPointer().sshSession()

        progressBar.reset(len(data))
        for i, (d,isDirectory,isLocal) in enumerate(data):
            try:
                if isLocal:
                    if isDirectory:
                        shutil.copytree(d,str(self._currentDirectory.joinpath(d.name)))
                    else:
                        shutil.copy(d,self._currentDirectory)
                else:
                    cmd = scp.SCPClient(sshSession.get_transport())
                    cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(), d),str(self._currentDirectory), recursive=True)
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
            entries.append((self._currentDirectory.joinpath(entry[0]),isDirectory,True))

        return entries

    def onOpenEntry(self, index):
        """Called when the user double clicks on a model's entry. 
        
        The entry can be a directory or a file. In case of a folder, the folder will be entered in and in 
        case of a file, the file will be opened its default application.

        Args:
            index (QtCore.QModelIndex): the index of the entry
        """

        row = index.row()

        entry = self._entries[row]

        # Any error must be caught here when resolving the file
        try:
            fullPath = self._currentDirectory.joinpath(entry[0]).resolve()
        except Exception as e:
            self._currentDirectory = pathlib.Path()
            logging.error(str(e))
            return
        
        if entry[2] == 'Folder':
            self.setDirectory(fullPath)
        else:
            self.openFile(fullPath)

    def openFile(self, path):
        """Open the file using its default application.

        Args:
            path: the path of the file to be edited
        """

        path = str(path.resolve())

        try:
            system = platform.system()
            if system == 'Linux':
                subprocess.call(['xdg-open',path])
            elif system == 'Darwin':
                subprocess.call(['open',path])
            elif system == 'Windows':
                subprocess.call(['start',path],shell=True)
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

        progressBar.reset(len(entries))
        for i, (d,isDirectory,isLocal) in enumerate(entries):
            target = self._currentDirectory.joinpath(d.stem+d.suffix)
            num = 1
            while target.exists():
                base = str(target.parent.joinpath(target.stem))
                match = re.search('(.*)_\d+',base)
                if match is not None:
                    base = match.groups(0)[0].strip()
                target = target.parent.joinpath('{}_{}{}'.format(base,num,target.suffix))
                num += 1                
            try:
                if isLocal:
                    if isDirectory:
                        shutil.copytree(d,target)
                    else:
                        shutil.copy(d,target)
                else:
                    cmd = scp.SCPClient(sshSession.get_transport())
                    cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(), d),str(target), recursive=True)
            except Exception as e:
                logging.error(str(e))
                pass
            progressBar.update(i+1)

        self.setDirectory(self._currentDirectory)

    def removeEntries(self, selectedRows):
        """Remove some entries of the model.

        Args:
            selectedRows (list of int): the list of indexes of the entries to be removed
        """

        for row in selectedRows[::-1]:
            selectedPath = self._currentDirectory.joinpath(self._entries[row][0])
            if selectedPath.is_dir():
                shutil.rmtree(str(selectedPath))
            else:
                selectedPath.unlink()

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

        oldName = self._currentDirectory.joinpath(oldName)
        newName = self._currentDirectory.joinpath(newName)
        
        shutil.move(str(oldName),str(newName))

        self.layoutChanged.emit()

    def saveFile(self, tempFile, actualFile):
        """Save a file that was opened for edition.

        Args:
            tempFile (pathlib.Path): the temporary file that contains the saved data
            actualFile (pathlib.Path): the actual path to which the file should be saved
        """

        savedFile = actualFile
        num = 1
        while os.path.exists(str(savedFile)):
            base = str(savedFile.parent.joinpath(savedFile.stem))
            match = re.search('(.*)_\d+',base)
            if match is not None:
                base = match.groups(0)[0].strip()
            savedFile = savedFile.parent.joinpath('{}_{}{}'.format(base,num,savedFile.suffix))
            num += 1

        shutil.copy(str(actualFile),str(savedFile))
        shutil.move(str(tempFile),str(actualFile))

        self.setDirectory(self._currentDirectory)

    def setDirectory(self, directory):
        """Sets a directory.

        This will trigger a full update of the model.

        Args:
            directory (str): the directory
        """

        if not directory.is_absolute():
            directory = directory.absolute()
        
        # If the input argument was a filename, get its base directory
        if directory.is_file():
            directory = directory.parent

        if platform.system() == 'Windows' and self._currentDirectory == directory:
            from passhfiles.utils.Platform import getDrives
            availableDrives = getDrives()

            self._entries = []
            for drive in availableDrives:
                size = None
                typ = 'Folder'
                modificationTime = ''
                icon = self._directoryIcon
                owner = findOwner(drive)
                self._entries.append([drive,size,typ,owner,modificationTime,icon])

            self._currentDirectory = directory

            self.layoutChanged.emit()
            self.currentDirectoryChangedSignal.emit(self._currentDirectory)
            return

        try:
            contents = [v.name for v in directory.iterdir()]
        except PermissionError as e:
            logging.error(str(e))
            return

        if not self._showHiddenFiles:
            contents = [c for c in contents if not c.startswith('.')]

        self._currentDirectory = directory

        # Sort the contents of the directory (first the sorted directories and then the sorted files)
        sortedDirectories = sorted([c for c in contents if self._currentDirectory.joinpath(c).is_dir()],key=str.casefold)
        sortedDirectories = [(c,True) for c in sortedDirectories]
        sortedFiles = sorted([c for c in contents if not self._currentDirectory.joinpath(c).is_dir()],key=str.casefold)
        sortedFiles = [(c,False) for c in sortedFiles]
        sortedContents = sortedDirectories + sortedFiles

        self._entries = [['..',None,'Folder',None,None,self._directoryIcon]]
        for (name,isDirectory) in sortedContents:
            absPath = self._currentDirectory.joinpath(name)
            size = None if isDirectory else sizeOf(absPath.lstat().st_size)
            typ = 'Folder' if isDirectory else 'File'
            modificationTime = str(datetime.fromtimestamp(absPath.lstat().st_mtime)).split('.')[0]
            icon = self._directoryIcon if isDirectory else self._fileIcon
            owner = findOwner(absPath)
            self._entries.append([name,size,typ,owner,modificationTime,icon])

        self.layoutChanged.emit()

        self.currentDirectoryChangedSignal.emit(self._currentDirectory)
