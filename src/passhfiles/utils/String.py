def isBinaryString(bytes):
    """Return True if the bytes is a binary string.

    Args:
        bytes (bytes): the string to check
    """

    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(bytes.translate(None, textchars))
