import io
import logging

import paramiko

def checkAndGetSSHKey(keyfile,keytype,password):
    """Check and returns the SSH key.

    Args:
        keyfile (pathlib.Path): the path to the private key
        password (str): the password (if any)
    """

    if keytype == 'RSA':
        paramikoKeyModule = paramiko.RSAKey
    elif keytype == 'ECDSA':
        paramikoKeyModule = paramiko.ECDSAKey
    elif keytype == 'ED25519':
        paramikoKeyModule = paramiko.Ed25519Key
    else:
        logging.error('Unknown key type')
        return False, None

    try:
        f = open(str(keyfile),'r')
        s = f.read()
        f.close()
        keyfile = io.StringIO(s)
        key = paramikoKeyModule.from_private_key(keyfile,password=password)
    except Exception as e:
        logging.error(str(e))
        return (False, None)
    else:
        return (True,key)

def runRemoteCmd(sshSession,serverNode,cmd):

    _, stdout, stderr = sshSession.exec_command('{} {}'.format(serverNode.name(),cmd))

    stdout = stdout.read().decode().replace(serverNode.stdoutMotd(),'').strip()
    stderr = stderr.read().decode().replace(serverNode.stderrMotd(),'').strip()

    return stdout,stderr
