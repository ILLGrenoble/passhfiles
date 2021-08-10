import os
import platform

import bastion_browser

def applicationDirectory():

    system = platform.system()

    if system in ['Linux','Darwin']:
        basedir = os.path.join(os.environ['HOME'], '.bastion_browser')
    else:
        basedir = os.path.join(os.environ['APPDATA'], 'bastion_browser')
    
    # If the application directory does not exist, create it.
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    
    return basedir

def applicationKeyPath():

    return os.path.join(applicationDirectory(),'application_key.yml')

def preferencesPath():

    return os.path.join(applicationDirectory(),'preferences.yml')

def sessionsDatabasePath():

    return os.path.join(applicationDirectory(),'sessions.yml')

def baseDirectory():

    return bastion_browser.__path__[0]