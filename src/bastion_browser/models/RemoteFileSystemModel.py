import logging
import os
import subprocess
import tempfile

import scp

from bastion_browser.kernel.Preferences import PREFERENCES
from bastion_browser.models.IFileSystemModel import IFileSystemModel
from bastion_browser.utils.Numbers import sizeOf

class RemoteFileSystemModel(IFileSystemModel):
            
    def editFile(self, path):

        if not PREFERENCES['editor']:
            logging.error('No text editor set in the preferences')
            return

        tempFile = tempfile.mktemp()
        cmd = scp.SCPClient(self._sshSession.get_transport())
        cmd.get('{}/{}'.format(self._serverIndex.internalPointer().name(),path),tempFile, recursive=True)
        try:
            subprocess.call([PREFERENCES['editor'],tempFile])
        except Exception as e:
            logging.error(str(e))

    def favorites(self):

        return self._serverIndex.internalPointer().data(0)['remote']

    def removeEntry(self, selectedRow):

        for row in selectedRow[::-1]:
            selectedPath = os.path.join(self._currentDirectory,self._entries[row][0])
            _, _, stderr = self._sshSession.exec_command('{} rm -rf {}'.format(self._serverIndex.internalPointer().name(), selectedPath))
            error = stderr.read().decode()
            if error:
                logging.error(error)
                continue

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
        
        _, _, stderr = self._sshSession.exec_command('{} mv {} {}'.format(self._serverIndex.internalPointr().name(), oldName,newName))
        error = stderr.read().decode()
        if error:
            logging.error(error)
            return

        self.setDirectory(self._currentDirectory)

    def setDirectory(self, directory):

        self._currentDirectory = directory

        _, stdout, stderr = self._sshSession.exec_command('{} ls --group-directories --full-time -alpL {}'.format(self._serverIndex.internalPointer().name(),self._currentDirectory))
        error = stderr.read().decode()
        if error:
            logging.error(error)
            return
        
        contents = [l.strip() for l in stdout.readlines()]
        if len(contents) == 1:
            return
                
        contents = contents[2:]
        self._entries = []
        self._icons = []
        for c in contents:
            words = [v.strip() for v in c.split()]
            typ = 'Folder' if words[-1].endswith('/') else 'File'
            size = sizeOf(int(words[4]))
            icon = self._directoryIcon if typ=='Folder' else self._fileIcon
            date = words[5]
            time = words[6].split('.')[0]
            modificationTime = '{} {}'.format(date,time)
            name = words[-1][:-1] if typ=='Folder' else words[-1]
            self._entries.append([name,size,typ,modificationTime])
            self._icons.append(icon)

        self.layoutChanged.emit()

    def transferData(self, data):

        for (d,_) in data:
            cmd = scp.SCPClient(self._sshSession.get_transport())
            cmd.put(d, remote_path='{}/{}'.format(self._serverIndex.internalPointer().name(),self._currentDirectory), recursive=True)

        self.setDirectory(self._currentDirectory)
