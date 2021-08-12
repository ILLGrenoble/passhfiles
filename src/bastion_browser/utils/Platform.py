import os
import platform
import pwd

import bastion_browser

def applicationSettingsDirectory(create=True):
    """Returns (and creates if it does not exists) the application settings directory.

    Returns:
        str: the application settings directory
    """

    system = platform.system()

    if system in ['Linux','Darwin']:
        basedir = os.path.join(os.environ['HOME'], '.bastion_browser')
    else:
        basedir = os.path.join(os.environ['APPDATA'], 'bastion_browser')
    
    # If the application directory does not exist, create it.
    if create and not os.path.exists(basedir):
        os.makedirs(basedir)
    
    return basedir

def applicationKeyPath():
    """Return the path to the application key file.

    Returns:
        str: the path to the application key file
    """

    return os.path.join(applicationSettingsDirectory(),'application_key.yml')

def iconsDirectory():
    """Returns the path to the icons directory.

    Returns:
        str: the icons directory path
    """

    return os.path.join(applicationDirectory(),'icons')

def preferencesPath():
    """Returns the path to the preferences file.

    Returns:
        str: the path to the preferences file
    """

    return os.path.join(applicationSettingsDirectory(),'preferences.yml')

def sessionsDatabasePath():
    """Returns the path to the sessions file.

    Returns:
        str: the path to the sessions file
    """

    return os.path.join(applicationSettingsDirectory(),'sessions.yml')

def applicationDirectory():
    """Returns the path to the application base directory.

    Returns:
        str: the path to the application base directory
    """

    return bastion_browser.__path__[0]

def findOwner(filename):
    return pwd.getpwuid(os.stat(filename).st_uid).pw_name