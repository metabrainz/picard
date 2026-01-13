import os
import tempfile
import time

from picard.file import FileIdentity


def write_temp(contents=b"hello"):
    fd, fname = tempfile.mkstemp()
    with os.fdopen(fd, "wb") as f:
        f.write(contents)
    return fname


def test_identity_equal():
    fname = write_temp(b"abcdef")
    id1 = FileIdentity(fname)
    time.sleep(0.01)
    id2 = FileIdentity(fname)
    assert id1 == id2


def test_identity_diff_mtime():
    fname = write_temp(b"abcdef")
    id1 = FileIdentity(fname)
    with open(fname, "ab") as f:
        f.write(b"X")
    id2 = FileIdentity(fname)
    assert id1 != id2


def test_identity_hash_diff():
    f1 = write_temp(b"A" * (FileIdentity._READ_SIZE + 10))
    f2 = write_temp(b"B" * (FileIdentity._READ_SIZE + 10))
    id1 = FileIdentity(f1)
    id2 = FileIdentity(f2)
    assert id1 != id2


def test_identity_missing_file():
    fname = write_temp(b"xxx")
    os.remove(fname)
    id_missing = FileIdentity(fname)
    assert not id_missing
