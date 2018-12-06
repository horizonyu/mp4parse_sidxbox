import datetime
import struct



def maximum_element_size_for_length(length):
    """

    Returns the maximum element size representable in a given number of bytes.

    :arg length: the limit on the length of the encoded representation in bytes
    :type length: int
    :returns: the maximum element size representable
    :rtype: int

    """

    return (2 ** (7 * length)) - 2


def decode_vint_length(byte, mask=True):
    length = None
    value_mask = None
    for n in range(1, 9):
        if byte & (2 ** 8 - (2 ** (8 - n))) == 2 ** (8 - n):
            length = n
            value_mask = (2 ** (8 - n)) - 1
            break
    if length is None:
        raise IOError('Cannot decode invalid varible-length integer.')
    if mask:
        byte = byte & value_mask
    return length, byte


def read_element_id(stream):
    """

    Reads an element ID from a file-like object.

    :arg stream: the file-like object
    :returns: the decoded element ID and its length in bytes
    :rtype: tuple

    """

    byte = ord(stream.read(1))
    length, id_ = decode_vint_length(byte, False)
    if length > 4:
        raise IOError('Cannot decode element ID with length > 8.')
    for i in range(0, length - 1):
        byte = ord(stream.read(1))
        id_ = (id_ * 2 ** 8) + byte
    return id_, length


def read_element_size(stream):
    """

    Reads an element size from a file-like object.

    :arg stream: the file-like object
    :returns: the decoded size (or None if unknown) and the length of the descriptor in bytes
    :rtype: tuple

    """

    byte = ord(stream.read(1))
    length, size = decode_vint_length(byte)

    for i in range(0, length - 1):
        byte = ord(stream.read(1))
        size = (size * 2 ** 8) + byte

    if size == maximum_element_size_for_length(length) + 1:
        size = None

    return size, length


def read_unsigned_integer(stream, size):
    """

    Reads an encoded unsigned integer value from a file-like object.

    :arg stream: the file-like object
    :arg size: the number of bytes to read and decode
    :type size: int
    :returns: the decoded unsigned integer value
    :rtype: int

    """

    value = 0
    for i in range(0, size):
        byte = ord(stream.read(1))
        value = (value << 8) | byte
    return value


def read_signed_integer(stream, size):
    """

    Reads an encoded signed integer value from a file-like object.

    :arg stream: the file-like object
    :arg size: the number of bytes to read and decode
    :type size: int
    :returns: the decoded signed integer value
    :rtype: int

    """

    value = 0
    if size > 0:
        first_byte = ord(stream.read(1))
        value = first_byte
        for i in range(1, size):
            byte = ord(stream.read(1))
            value = (value << 8) | byte
        if (first_byte & 0b10000000) == 0b10000000:
            value = -(2 ** (size * 8) - value)
    return value


def read_float(stream, size):
    """

    Reads an encoded floating point value from a file-like object.

    :arg stream: the file-like object
    :arg size: the number of bytes to read and decode (must be 0, 4, or 8)
    :type size: int
    :returns: the decoded floating point value
    :rtype: float

    """

    if size not in (0, 4, 8):
        raise IOError('Cannot read floating point values with lengths other than 0, 4, or 8 bytes.')
    value = 0.0
    if size in (4, 8):
        data = stream.read(size)
        value = struct.unpack({
                                  4: '>f',
                                  8: '>d'
                              }[size], data)[0]
    return value


def read_string(stream, size):
    """

    Reads an encoded ASCII string value from a file-like object.

    :arg stream: the file-like object
    :arg size: the number of bytes to read and decode
    :type size: int
    :returns: the decoded ASCII string value
    :rtype: str

    """

    value = ''
    if size > 0:
        value = stream.read(size)
        value = value.partition(chr(0))[0]
    return value


def read_unicode_string(stream, size):
    """

    Reads an encoded unicode string value from a file-like object.

    :arg stream: the file-like object
    :arg size: the number of bytes to read and decode
    :type size: int
    :returns: the decoded unicode string value
    :rtype: unicode

    """

    if size > 0:
        data = stream.read(size)
        value = str(data)
    return value


def read_date(stream, size):
    """

    Reads an encoded date (and time) value from a file-like object.

    :arg stream: the file-like object
    :arg size: the number of bytes to read and decode (must be 8)
    :type size: int
    :returns: the decoded date (and time) value
    :rtype: datetime

    """

    if size != 8:
        raise IOError('Cannot read date values with lengths other than 8 bytes.')
    data = stream.read(size)
    nanoseconds = struct.unpack('>q', data)[0]
    delta = datetime.timedelta(microseconds=(nanoseconds // 1000))
    return datetime.datetime(2001, 1, 1, tzinfo=None) + delta
