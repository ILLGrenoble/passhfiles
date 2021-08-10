import os

from cryptography.fernet import Fernet

from bastion_browser.utils.Platform import applicationKeyPath

if not os.path.exists(applicationKeyPath()):
    with open(applicationKeyPath(),'wb') as fout:
        key = Fernet.generate_key()
        fout.write(key)

with open(applicationKeyPath()) as fin:
    key = fin.read()
    REFKEY = Fernet(key)