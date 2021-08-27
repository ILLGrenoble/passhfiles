import os
import platform
import re

import bastion_browser

if platform.system() == 'Windows':
    import ctypes as ctypes
    from ctypes import wintypes as wintypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)

    ERROR_INVALID_FUNCTION  = 0x0001
    ERROR_FILE_NOT_FOUND    = 0x0002
    ERROR_PATH_NOT_FOUND    = 0x0003
    ERROR_ACCESS_DENIED     = 0x0005
    ERROR_SHARING_VIOLATION = 0x0020

    SE_FILE_OBJECT = 1
    OWNER_SECURITY_INFORMATION = 0x00000001
    GROUP_SECURITY_INFORMATION = 0x00000002
    DACL_SECURITY_INFORMATION  = 0x00000004
    SACL_SECURITY_INFORMATION  = 0x00000008
    LABEL_SECURITY_INFORMATION = 0x00000010

    _DEFAULT_SECURITY_INFORMATION = (OWNER_SECURITY_INFORMATION |
        GROUP_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION |
        LABEL_SECURITY_INFORMATION)

    LPDWORD = ctypes.POINTER(wintypes.DWORD)
    SE_OBJECT_TYPE = wintypes.DWORD
    SECURITY_INFORMATION = wintypes.DWORD

    class SID_NAME_USE(wintypes.DWORD):
        _sid_types = dict(enumerate('''
            User Group Domain Alias WellKnownGroup DeletedAccount
            Invalid Unknown Computer Label'''.split(), 1))

        def __init__(self, value=None):
            if value is not None:
                if value not in self.sid_types:
                    raise ValueError('invalid SID type')
                wintypes.DWORD.__init__(value)

        def __str__(self):
            if self.value not in self._sid_types:
                raise ValueError('invalid SID type')
            return self._sid_types[self.value]

        def __repr__(self):
            return 'SID_NAME_USE(%s)' % self.value

    PSID_NAME_USE = ctypes.POINTER(SID_NAME_USE)

    class PLOCAL(wintypes.LPVOID):
        _needs_free = False
        def __init__(self, value=None, needs_free=False):
            super(PLOCAL, self).__init__(value)
            self._needs_free = needs_free

        def __del__(self):
            if self and self._needs_free:
                kernel32.LocalFree(self)
                self._needs_free = False

    PACL = PLOCAL

    class PSID(PLOCAL):
        def __init__(self, value=None, needs_free=False):
            super(PSID, self).__init__(value, needs_free)

        def __str__(self):
            if not self:
                raise ValueError('NULL pointer access')
            sid = wintypes.LPWSTR()
            advapi32.ConvertSidToStringSidW(self, ctypes.byref(sid))
            try:
                return sid.value
            finally:
                if sid:
                    kernel32.LocalFree(sid)

    class PSECURITY_DESCRIPTOR(PLOCAL):
        def __init__(self, value=None, needs_free=False):
            super(PSECURITY_DESCRIPTOR, self).__init__(value, needs_free)
            self.pOwner = PSID()
            self.pGroup = PSID()
            self.pDacl = PACL()
            self.pSacl = PACL()
            # back references to keep this object alive
            self.pOwner._SD = self
            self.pGroup._SD = self
            self.pDacl._SD = self
            self.pSacl._SD = self

        def getOwner(self, system_name=None):
            if not self or not self.pOwner:
                raise ValueError('NULL pointer access')
            return lookUpAccountSid(self.pOwner, system_name)

        def getGroup(self, system_name=None):
            if not self or not self.pGroup:
                raise ValueError('NULL pointer access')
            return lookUpAccountSid(self.pGroup, system_name)

    def lookUpAccountSid(sid, system_name=None):
        SIZE = 256
        name = ctypes.create_unicode_buffer(SIZE)
        domain = ctypes.create_unicode_buffer(SIZE)
        cch_name = wintypes.DWORD(SIZE)
        cch_domain = wintypes.DWORD(SIZE)
        sid_type = SID_NAME_USE()
        advapi32.LookupAccountSidW(system_name, sid, name, ctypes.byref(cch_name),
            domain, ctypes.byref(cch_domain), ctypes.byref(sid_type))
        return name.value, domain.value, sid_type

    def getFileSecurity(filename, request=_DEFAULT_SECURITY_INFORMATION):
        # N.B. This query may fail with ERROR_INVALID_FUNCTION
        # for some filesystems.
        pSD = PSECURITY_DESCRIPTOR(needs_free=True)
        error = advapi32.GetNamedSecurityInfoW(filename, SE_FILE_OBJECT, request,
                    ctypes.byref(pSD.pOwner), ctypes.byref(pSD.pGroup),
                    ctypes.byref(pSD.pDacl), ctypes.byref(pSD.pSacl),
                    ctypes.byref(pSD))
        if error != 0:
            raise ctypes.WinError(error)
        return pSD

    def findOwner(filename):
        try:
            userInfo = getFileSecurity(filename).getOwner()
        except:
            return 'unknown'
        else:
            return userInfo[0]

    def homeDirectory():
        return os.environ['USERPROFILE']

else:

    def findOwner(filename):
        import pwd
        return pwd.getpwuid(os.stat(filename).st_uid).pw_name

    def homeDirectory():
        return os.environ['HOME']

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

def unixPathsJoin(*args):
    """Equivalent of os.path.join for unix system.
    """

    path = '/'.join(args)

    path = re.sub('/+','/',path)
    return path

def unixNormPath(path):
    """Normalize path, eliminating double slashes, etc."""
    if isinstance(path, bytes):
        sep = b'/'
        empty = b''
        dot = b'.'
        dotdot = b'..'
    else:
        sep = '/'
        empty = ''
        dot = '.'
        dotdot = '..'
    if path == empty:
        return dot
    initial_slashes = path.startswith(sep)
    # POSIX allows one or two initial slashes, but treats three or more
    # as single slash.
    if (initial_slashes and
        path.startswith(sep*2) and not path.startswith(sep*3)):
        initial_slashes = 2
    comps = path.split(sep)
    new_comps = []
    for comp in comps:
        if comp in (empty, dot):
            continue
        if (comp != dotdot or (not initial_slashes and not new_comps) or
             (new_comps and new_comps[-1] == dotdot)):
            new_comps.append(comp)
        elif new_comps:
            new_comps.pop()
    comps = new_comps
    path = sep.join(comps)
    if initial_slashes:
        path = sep*initial_slashes + path
    return path or dot