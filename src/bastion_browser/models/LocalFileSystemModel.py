from datetime import datetime
import logging
import os
import shutil
import subprocess

import scp

from bastion_browser.models.IFileSystemModel import IFileSystemModel
from bastion_browser.utils.Numbers import sizeOf

class LocalFileSystemModel(IFileSystemModel):

    def editFile(self, path):

        subprocess.call(['gedit',path])

    def favorites(self):

        return self._serverIndex.internalPointer().data(0)['local']

    def removeEntry(self, selectedRows):

        for row in selectedRows[::-1]:
            selectedPath = os.path.join(self._currentDirectory,self._entries[row][0])
            if os.path.isdir(selectedPath):
                shutil.rmtree(selectedPath)
            else:
                os.remove(selectedPath)

        self.setDirectory(self._currentDirectory)

    def renameEntry(self, selectedRow, newName):

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

        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            directory = os.path.dirname(directory)

        try:
            contents = os.listdir(directory)
        except PermissionError as e:
            logging.error(str(e))
            return

        self._currentDirectory = directory

        sortedContents = [('..',True)]
        sortedContents += sorted([(c,True) for c in contents if os.path.isdir(os.path.join(self._currentDirectory,c))])
        sortedContents += sorted([(c,False) for c in contents if not os.path.isdir(os.path.join(self._currentDirectory,c))])

        self._entries = []
        self._icons = []
        for (name,isDirectory) in sortedContents:
            absPath = os.path.join(self._currentDirectory,name)
            size = sizeOf(os.path.getsize(absPath))
            typ = 'Folder' if isDirectory else 'File'
            modificationTime = str(datetime.fromtimestamp(os.path.getmtime(absPath))).split('.')[0]
            icon = self._directoryIcon if isDirectory else self._fileIcon
            self._entries.append([name,size,typ,modificationTime])
            self._icons.append(icon)

        self.layoutChanged.emit()

    def transferData(self, data):

        for (d,_) in data:
            cmd = scp.SCPClient(self._sshSession.get_transport())
            cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(), d),self._currentDirectory, recursive=True)

        self.setDirectory(self._currentDirectory)
