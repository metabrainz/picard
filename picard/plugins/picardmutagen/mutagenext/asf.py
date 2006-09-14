# -*- coding: utf-8 -*-
# ASF reader/tagger
#
# Copyright 2006 Lukáš Lalinský <lalinsky@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# $Id$

"""Read and write metadata to Window Media Audio files.
"""

__all__ = ["ASF", "Open", "delete"]

import struct
from mutagen import FileType, Metadata
from mutagen._util import insert_bytes, delete_bytes

class ASFError(IOError): pass

class ASFInfo(object):
    """ASF stream information."""
    def __init__(self):
        self.length = 0.0
        self.sample_rate = 0
        self.bitrate = 0
        self.channels = 0
    def pprint(self):
        s = "Windows Media Audio %d bps, %s Hz, %d channels, %.2f seconds" % (
            self.bitrate, self.sample_rate, self.channels, self.length)
        return s 

class ASFTags(dict):
    """Dictionary containing ASF attributes."""
    def pprint(self):
        return "\n".join(["%s=%s" % (k, v) for k, v in self.items()]) 

class BaseAttribute(object):
    """Generic attribute."""
    TYPE = None 
    def __init__(self, name, value=None, data=None):
        self.name = name
        if data:
            self.value = self.parse(data)
        else:
            self.value = value
    def render(self):
        name = self.name.encode("utf-16-le") + "\x00\x00"
        data = self._render()
        return struct.pack("<H", len(name)) + name + \
               struct.pack("<HH", self.TYPE, len(data)) + data

class UnicodeAttribute(BaseAttribute):
    """Unicode string attribute."""
    TYPE = 0x0000
    def parse(self, data):
        return data.decode("utf-16").strip("\x00")
    def _render(self):
        return self.value.encode("utf-16-le") + "\x00\x00"
    def __str__(self):
        return self.value

class ByteArrayAttribute(BaseAttribute):
    """Byte array attribute."""
    TYPE = 0x0001
    def parse(self, data):
        return data
    def _render(self):
        return self.value
    def __str__(self):
        return self.value

class BoolAttribute(BaseAttribute):
    """Bool attribute."""
    TYPE = 0x0002
    def parse(self, data):
        return struct.unpack("<L", data)[0] == 1
    def _render(self):
        return struct.pack("<L", int(self.value))
    def __bool__(self):
        return self.value
    def __str__(self):
        return str(self.value)

class DWordAttribute(BaseAttribute):
    """DWORD attribute."""
    TYPE = 0x0003
    def parse(self, data):
        return struct.unpack("<L", data)[0]
    def _render(self):
        return struct.pack("<L", self.value)
    def __int__(self):
        return self.value
    def __str__(self):
        return str(self.value)

class QWordAttribute(BaseAttribute):
    """QWORD attribute."""
    TYPE = 0x0004
    def parse(self, data):
        return struct.unpack("<Q", data)[0]
    def _render(self):
        return struct.pack("<Q", self.value)
    def __int__(self):
        return self.value
    def __str__(self):
        return str(self.value)

class WordAttribute(BaseAttribute):
    """WORD attribute."""
    TYPE = 0x0005
    def parse(self, data):
        return struct.unpack("<H", data)[0]
    def _render(self):
        return struct.pack("<H", self.value)
    def __int__(self):
        return self.value
    def __str__(self):
        return str(self.value)

_attribute_types = {
    UnicodeAttribute.TYPE: UnicodeAttribute,
    ByteArrayAttribute.TYPE: ByteArrayAttribute,
    BoolAttribute.TYPE: BoolAttribute,
    DWordAttribute.TYPE: DWordAttribute,
    QWordAttribute.TYPE: QWordAttribute,
    WordAttribute.TYPE: WordAttribute
}

_standard_attribute_names = [
    "Title",
    "Author",
    "Copyright",
    "Description",
    "Rating"
]

class BaseObject(object):
    """Base ASF object."""
    GUID = None

class HeaderObject(object):
    """ASF header."""
    GUID = "\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C"
    
class ContentDescriptionObject(BaseObject):
    """Content description."""
    GUID = "\x33\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C"
    def parse(self, asf, data, fileobj, size):
        asf.offset1 = fileobj.tell() - size
        asf.size1 = size
        lengths = struct.unpack("<HHHHH", data[:10])
        texts = []
        pos = 10
        for length in lengths:
            end = pos + length
            texts.append(data[pos:end].decode("utf-16").strip("\x00"))
            pos = end
        asf.tags["Title"], asf.tags["Author"], asf.tags["Copyright"], \
            asf.tags["Description"], asf.tags["Rating"] = texts
    def render(self, asf):
        def render_text(name):
            value = asf.tags.get(name, "")
            if value:
                return value.encode("utf-16-le") + "\x00\x00"
            else:
                return ""
        texts = map(render_text, _standard_attribute_names)
        data = struct.pack("<HHHHH", *map(str.__len__, texts)) + "".join(texts)
        return self.GUID + struct.pack("<Q", 24 + len(data)) + data
        
class ExtendedContentDescriptionObject(BaseObject):
    """Extended content description."""
    GUID = "\x40\xA4\xD0\xD2\x07\xE3\xD2\x11\x97\xF0\x00\xA0\xC9\x5E\xA8\x50"
    def parse(self, asf, data, fileobj, size):
        asf.offset2 = fileobj.tell() - size
        asf.size2 = size
        num_attributes, = struct.unpack("<H", data[0:2])
        pos = 2
        for i in range(num_attributes):
            name_length, = struct.unpack("<H", data[pos:pos+2])
            pos += 2
            name = data[pos:pos+name_length].decode("utf-16").strip("\x00")
            pos += name_length
            value_type, value_length = struct.unpack("<HH", data[pos:pos+4])
            pos += 4
            value = data[pos:pos+value_length]
            pos += value_length
            attr = _attribute_types[value_type](name, data=value)
            asf.tags[attr.name] = attr
    def render(self, asf):
        attrs = [attr for name, attr in asf.tags.items()
                 if name not in _standard_attribute_names]
        data = "".join(map(BaseAttribute.render, attrs))
        data = struct.pack("<QH", 26 + len(data), len(attrs)) + data
        return self.GUID + data

class FilePropertiesObject(BaseObject):
    """File properties.""" 
    GUID = "\xA1\xDC\xAB\x8C\x47\xA9\xCF\x11\x8E\xE4\x00\xC0\x0C\x20\x53\x65"
    def parse(self, asf, data, fileobj, size):
        length, = struct.unpack("<Q", data[40:48])
        asf.info.length = length / 600000000.0

class StreamPropertiesObject(BaseObject):
    """Stream properties.""" 
    GUID = "\x91\x07\xDC\xB7\xB7\xA9\xCF\x11\x8E\xE6\x00\xC0\x0C\x20\x53\x65"
    def parse(self, asf, data, fileobj, size):
        channels, sample_rate, bitrate = struct.unpack("<HII", data[56:66])
        asf.info.channels = channels
        asf.info.sample_rate = sample_rate
        asf.info.bitrate = bitrate * 8 / 1000

_object_types = {
    ExtendedContentDescriptionObject.GUID: ExtendedContentDescriptionObject,
    ContentDescriptionObject.GUID: ContentDescriptionObject,
    FilePropertiesObject.GUID: FilePropertiesObject,
    StreamPropertiesObject.GUID: StreamPropertiesObject
}

class ASF(FileType):
    """An ASF file, probably containing WMA or WMV."""
    
    def load(self, filename):
        self.filename = filename
        fileobj = file(filename, "rb")
        try:
            self.size = 0
            self.size1 = 0
            self.size2 = 0
            self.offset1 = 0
            self.offset2 = 0
            self.num_objects = 0
            self.info = ASFInfo()
            self.tags = ASFTags()
            self.__read_file(fileobj)
        finally:
            fileobj.close()

    def save(self):
        fileobj = file(self.filename, "rb+")
        try:
            if not self.offset1:
                self.offset1 = 30
                self.num_objects += 1
            if not self.offset2:
                self.offset2 = 30
                self.num_objects += 1

            data = ContentDescriptionObject().render(self) + \
                   ExtendedContentDescriptionObject().render(self)
            size = len(data)

            fileobj.seek(16)
            fileobj.write(struct.pack("<QL", self.size + size - self.size1 - 
                                      self.size2, self.num_objects))

            if self.offset1 + self.size1 == self.offset2: 
                offset = self.offset1
                orig_size = self.size1 + self.size2
            elif self.offset2 + self.size2 == self.offset1:
                offset = self.offset2
                orig_size = self.size1 + self.size2
            elif self.offset1 < self.offset2:
                delete_bytes(fileobj, self.size2, self.offset2)
                offset = self.offset1
                orig_size = self.size1
            else:
                delete_bytes(fileobj, self.size1, self.offset1)
                offset = self.offset2
                orig_size = self.size2

            if size > orig_size:
                insert_bytes(fileobj, size - orig_size, offset)
            if size < orig_size:
                delete_bytes(fileobj, orig_size - size, offset)

            fileobj.seek(offset)
            fileobj.write(data)

        finally:
            fileobj.close()

    def __read_file(self, fileobj):
        header = fileobj.read(30)
        if len(header) != 30 or header[:16] != HeaderObject.GUID:
            raise ASFError, "Not an ASF file."

        self.size, self.num_objects = struct.unpack("<QL", header[16:28])
        for i in range(self.num_objects):
            self.__read_object(fileobj)

    def __read_object(self, fileobj):
        guid, size = struct.unpack("<16sQ", fileobj.read(24))
        if guid in _object_types:
            data = fileobj.read(size - 24)
            obj = _object_types[guid]()
            obj.parse(self, data, fileobj, size)
        else:
            fileobj.seek(size - 24, 1)

    def score(filename, fileobj, header):
        return header.startswith(Header.GUID) * 2
    score = staticmethod(score) 

Open = ASF

def delete(filename):
    """Remove tags from a file."""
    ASF(filename).delete()