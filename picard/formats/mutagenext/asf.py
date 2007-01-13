# -*- coding: utf-8 -*-
# ASF reader/tagger
#
# Copyright 2006 Lukáš Lalinský <lalinsky@gmail.com>
# Copyright 2005-2006 Joe Wreschnig
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# $Id$

"""Read and write metadata to Window Media Audio files.
"""

__all__ = ["ASF", "Open"]

import struct
from mutagen import FileType, Metadata
from mutagen._util import insert_bytes, delete_bytes, DictMixin

class error(IOError): pass
class ASFError(error): pass
class ASFHeaderError(error): pass


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


class ASFTags(list, DictMixin):
    """Dictionary containing ASF attributes."""

    def pprint(self):
        return "\n".join(["%s=%s" % (k, v) for k, v in self]) 

    def __getitem__(self, key):
        """A list of values for the key.

        This is a copy, so comment['title'].append('a title') will not
        work.

        """
        values = [value for (k, value) in self if k == key]
        if not values: raise KeyError, key
        else: return values

    def __delitem__(self, key):
        """Delete all values associated with the key."""
        to_delete = filter(lambda x: x[0] == key, self)
        if not to_delete: raise KeyError, key
        else: map(self.remove, to_delete)

    def __contains__(self, key):
        """Return true if the key has any values."""
        for k, value in self:
            if k == key: return True
        else: return False

    def __setitem__(self, key, values):
        """Set a key's value or values.

        Setting a value overwrites all old ones. The value may be a
        list of Unicode or UTF-8 strings, or a single Unicode or UTF-8
        string.

        """
        if not isinstance(values, list):
            values = [values]
        try: del(self[key])
        except KeyError: pass
        for value in values:
            if key in _standard_attribute_names:
                value = unicode(value)
            elif not isinstance(value, ASFBaseAttribute):
                if isinstance(value, unicode):
                    value = ASFUnicodeAttribute(value)
                elif isinstance(value, bool):
                    value = ASFBoolAttribute(value)
                elif isinstance(value, int):
                    value = ASFDWordAttribute(value)
                elif isinstance(value, long):
                    value = ASFQWordAttribute(value)
            self.append((key, value))

    def keys(self):
        """Return all keys in the comment."""
        return self and set(zip(*self)[0])

    def as_dict(self):
        """Return a copy of the comment data in a real dict."""
        d = {}
        for key, value in self:
            d.setdefault(key, []).append(value)
        return d


class ASFBaseAttribute(object):
    """Generic attribute."""
    TYPE = None

    def __init__(self, value=None, data=None, language=None,
                 stream=None, **kwargs):
        self.language = language
        self.stream = stream
        if data:
            self.value = self.parse(data, **kwargs)
        else:
            self.value = value

    def __repr__(self):
        name = "%s(%r" % (type(self).__name__, self.value)
        if self.language:
            name += ", language=%d" % self.language
        if self.stream:
            name += ", stream=%d" % self.stream
        name += ")"
        return name

    def render(self, name):
        name = name.encode("utf-16-le") + "\x00\x00"
        data = self._render()
        return (struct.pack("<H", len(name)) + name +
                struct.pack("<HH", self.TYPE, len(data)) + data)

    def render_m(self, name):
        name = name.encode("utf-16-le") + "\x00\x00"
        if self.TYPE == 2:
            data = self._render(dword=False)
        else:
            data = self._render()
        return (struct.pack("<HHHHI", 0, self.stream or 0, len(name),
                            self.TYPE, len(data)) + name + data)

    def render_ml(self, name):
        name = name.encode("utf-16-le") + "\x00\x00"
        if self.TYPE == 2:
            data = self._render(dword=False)
        else:
            data = self._render()
        return (struct.pack("<HHHHI", self.language or 0, self.stream or 0,
                            len(name), self.TYPE, len(data)) + name + data)

class ASFUnicodeAttribute(ASFBaseAttribute):
    """Unicode string attribute."""
    TYPE = 0x0000

    def parse(self, data):
        return data.decode("utf-16").strip("\x00")

    def _render(self):
        return self.value.encode("utf-16-le") + "\x00\x00"

    def __str__(self):
        return self.value

    def __cmp__(self, other):
        return cmp(unicode(self), other)


class ASFByteArrayAttribute(ASFBaseAttribute):
    """Byte array attribute."""
    TYPE = 0x0001

    def parse(self, data):
        return data

    def _render(self):
        return self.value

    def __str__(self):
        return "[binary data (%s bytes)]" % len(self.value)

    def __cmp__(self, other):
        return cmp(str(self), other)


class ASFBoolAttribute(ASFBaseAttribute):
    """Bool attribute."""
    TYPE = 0x0002

    def parse(self, data, dword=True):
        if dword:
            return struct.unpack("<I", data)[0] == 1
        else:
            return struct.unpack("<H", data)[0] == 1

    def _render(self, dword=True):
        if dword:
            return struct.pack("<I", int(self.value))
        else:
            return struct.pack("<H", int(self.value))

    def __bool__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __cmp__(self, other):
        return cmp(bool(self), other)


class ASFDWordAttribute(ASFBaseAttribute):
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

    def __cmp__(self, other):
        return cmp(int(self), other)


class ASFQWordAttribute(ASFBaseAttribute):
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

    def __cmp__(self, other):
        return cmp(int(self), other)


class ASFWordAttribute(ASFBaseAttribute):
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

    def __cmp__(self, other):
        return cmp(int(self), other)


class ASFGUIDAttribute(ASFBaseAttribute):
    """GUID attribute."""
    TYPE = 0x0006

    def parse(self, data):
        return data

    def _render(self):
        return self.value

    def __str__(self):
        return self.value

    def __cmp__(self, other):
        return cmp(str(self), other)


UNICODE = ASFUnicodeAttribute.TYPE
BYTEARRAY = ASFByteArrayAttribute.TYPE
BOOL = ASFBoolAttribute.TYPE
DWORD = ASFDWordAttribute.TYPE
QWORD = ASFQWordAttribute.TYPE
WORD = ASFWordAttribute.TYPE
GUID = ASFGUIDAttribute.TYPE

def ASFValue(value, kind, **kwargs):
    for t, c in _attribute_types.items():
        if kind == t:
            return c(value=value, **kwargs)
    raise ValueError("Unknown value type")


_attribute_types = {
    ASFUnicodeAttribute.TYPE: ASFUnicodeAttribute,
    ASFByteArrayAttribute.TYPE: ASFByteArrayAttribute,
    ASFBoolAttribute.TYPE: ASFBoolAttribute,
    ASFDWordAttribute.TYPE: ASFDWordAttribute,
    ASFQWordAttribute.TYPE: ASFQWordAttribute,
    ASFWordAttribute.TYPE: ASFWordAttribute,
    ASFGUIDAttribute.TYPE: ASFGUIDAttribute,
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

    def parse(self, asf, data, fileobj, size):
        self.data = data

    def render(self, asf):
        data = self.GUID + struct.pack("<Q", len(self.data) + 24) + self.data
        size = len(data)
        return data


class UnknownObject(BaseObject):
    """Unknown ASF object."""
    def __init__(self, guid):
        self.GUID = guid


class HeaderObject(object):
    """ASF header."""
    GUID = "\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C"


class ContentDescriptionObject(BaseObject):
    """Content description."""
    GUID = "\x33\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C"

    def parse(self, asf, data, fileobj, size):
        super(ContentDescriptionObject, self).parse(asf, data, fileobj, size)
        asf.content_description_obj = self
        lengths = struct.unpack("<HHHHH", data[:10])
        texts = []
        pos = 10
        for length in lengths:
            end = pos + length
            texts.append(data[pos:end].decode("utf-16").strip("\x00"))
            pos = end
        (asf.tags["Title"], asf.tags["Author"], asf.tags["Copyright"],
         asf.tags["Description"], asf.tags["Rating"]) = texts

    def render(self, asf):
        def render_text(name):
            value = asf.tags.get(name, [])
            if value and value[0]:
                return value[0].encode("utf-16-le") + "\x00\x00"
            else:
                return ""
        texts = map(render_text, _standard_attribute_names)
        data = struct.pack("<HHHHH", *map(str.__len__, texts)) + "".join(texts)
        return self.GUID + struct.pack("<Q", 24 + len(data)) + data


class ExtendedContentDescriptionObject(BaseObject):
    """Extended content description."""
    GUID = "\x40\xA4\xD0\xD2\x07\xE3\xD2\x11\x97\xF0\x00\xA0\xC9\x5E\xA8\x50"

    def parse(self, asf, data, fileobj, size):
        super(ExtendedContentDescriptionObject, self).parse(asf, data, fileobj, size)
        asf.extended_content_description_obj = self
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
            attr = _attribute_types[value_type](data=value)
            asf.tags.append((name, attr))

    def render(self, asf):
        attrs = asf.to_extended_content_description.items()
        data = "".join([attr.render(name) for (name, attr) in attrs])
        data = struct.pack("<QH", 26 + len(data), len(attrs)) + data
        return self.GUID + data


class FilePropertiesObject(BaseObject):
    """File properties.""" 
    GUID = "\xA1\xDC\xAB\x8C\x47\xA9\xCF\x11\x8E\xE4\x00\xC0\x0C\x20\x53\x65"

    def parse(self, asf, data, fileobj, size):
        super(FilePropertiesObject, self).parse(asf, data, fileobj, size)
        length, _, preroll = struct.unpack("<QQQ", data[40:64])
        asf.info.length = length / 10000000.0 - preroll / 1000.0


class StreamPropertiesObject(BaseObject):
    """Stream properties.""" 
    GUID = "\x91\x07\xDC\xB7\xB7\xA9\xCF\x11\x8E\xE6\x00\xC0\x0C\x20\x53\x65"

    def parse(self, asf, data, fileobj, size):
        super(StreamPropertiesObject, self).parse(asf, data, fileobj, size)
        channels, sample_rate, bitrate = struct.unpack("<HII", data[56:66])
        asf.info.channels = channels
        asf.info.sample_rate = sample_rate
        asf.info.bitrate = bitrate * 8


class HeaderExtensionObject(BaseObject):
    """Header extension.""" 
    GUID = "\xb5\x03\xbf_.\xa9\xcf\x11\x8e\xe3\x00\xc0\x0c Se"

    def parse(self, asf, data, fileobj, size):
        super(HeaderExtensionObject, self).parse(asf, data, fileobj, size)
        asf.header_extension_obj = self
        datasize, = struct.unpack("<I", data[18:22])
        datapos = 0
        self.objects = []
        while datapos < datasize:
            guid, size = struct.unpack("<16sQ", data[22+datapos:22+datapos+24])
            if guid in _object_types:
                obj = _object_types[guid]()
            else:
                obj = UnknownObject(guid)
            obj.parse(asf, data[22+datapos+24:22+datapos+size], fileobj, size)
            self.objects.append(obj)
            datapos += size

    def render(self, asf):
        data = "".join([obj.render(asf) for obj in self.objects])
        return (self.GUID + struct.pack("<Q", 24 + 16 + 6 + len(data)) +
                "\x11\xD2\xD3\xAB\xBA\xA9\xcf\x11" +
                "\x8E\xE6\x00\xC0\x0C\x20\x53\x65" +
                "\x06\x00" + struct.pack("<I", len(data)) + data)


class MetadataObject(BaseObject):
    """Metadata description."""
    GUID = "\xea\xcb\xf8\xc5\xaf[wH\x84g\xaa\x8cD\xfaL\xca"

    def parse(self, asf, data, fileobj, size):
        super(MetadataObject, self).parse(asf, data, fileobj, size)
        asf.metadata_obj = self
        num_attributes, = struct.unpack("<H", data[0:2])
        pos = 2
        for i in range(num_attributes):
            (reserved, stream, name_length, value_type,
             value_length) = struct.unpack("<HHHHI", data[pos:pos+12])
            pos += 12
            name = data[pos:pos+name_length].decode("utf-16").strip("\x00")
            pos += name_length
            value = data[pos:pos+value_length]
            pos += value_length
            args = {'data': value, 'stream': stream}
            if value_type == 2:
                args['dword'] = False
            attr = _attribute_types[value_type](**args)
            asf.tags.append((name, attr))

    def render(self, asf):
        attrs = asf.to_metadata.items()
        data = "".join([attr.render_m(name) for (name, attr) in attrs])
        return (self.GUID + struct.pack("<QH", 26 + len(data), len(attrs)) +
                data)


class MetadataLibraryObject(BaseObject):
    """Metadata library description."""
    GUID = "\x94\x1c#D\x98\x94\xd1I\xa1A\x1d\x13NEpT"

    def parse(self, asf, data, fileobj, size):
        super(MetadataLibraryObject, self).parse(asf, data, fileobj, size)
        asf.metadata_library_obj = self
        num_attributes, = struct.unpack("<H", data[0:2])
        pos = 2
        for i in range(num_attributes):
            (language, stream, name_length, value_type,
             value_length) = struct.unpack("<HHHHI", data[pos:pos+12])
            pos += 12
            name = data[pos:pos+name_length].decode("utf-16").strip("\x00")
            pos += name_length
            value = data[pos:pos+value_length]
            pos += value_length
            args = {'data': value, 'language': language, 'stream': stream}
            if value_type == 2:
                args['dword'] = False
            attr = _attribute_types[value_type](**args)
            asf.tags.append((name, attr))

    def render(self, asf):
        attrs = asf.to_metadata_library
        data = "".join([attr.render_ml(name) for (name, attr) in attrs])
        return (self.GUID + struct.pack("<QH", 26 + len(data), len(attrs)) +
                data)


_object_types = {
    ExtendedContentDescriptionObject.GUID: ExtendedContentDescriptionObject,
    ContentDescriptionObject.GUID: ContentDescriptionObject,
    FilePropertiesObject.GUID: FilePropertiesObject,
    StreamPropertiesObject.GUID: StreamPropertiesObject,
    HeaderExtensionObject.GUID: HeaderExtensionObject,
    MetadataLibraryObject.GUID: MetadataLibraryObject,
    MetadataObject.GUID: MetadataObject,
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

        # Move attributes to the right objects
        self.to_extended_content_description = {}
        self.to_metadata = {}
        self.to_metadata_library = []
        for name, value in self.tags:
            if name in _standard_attribute_names:
                continue
            if (value.language is None and value.stream is None and
                name not in self.to_extended_content_description):
                self.to_extended_content_description[name] = value
            elif (value.language is None and value.stream is not None and
                  name not in self.to_metadata):
                self.to_metadata[name] = value
            else:
                self.to_metadata_library.append((name, value))

        # Add missing objects
        if not self.content_description_obj:
            self.content_description_obj = \
                ContentDescriptionObject()
            self.objects.append(self.content_description_obj)
        if not self.extended_content_description_obj:
            self.extended_content_description_obj = \
                ExtendedContentDescriptionObject()
            self.objects.append(self.extended_content_description_obj)
        if not self.header_extension_obj:
            self.header_extension_obj = \
                HeaderExtensionObject()
            self.objects.append(self.header_extension_obj)
        if not self.metadata_obj:
            self.metadata_obj = \
                MetadataObject()
            self.header_extension_obj.objects.append(self.metadata_obj)
        if not self.metadata_library_obj:
            self.metadata_library_obj = \
                MetadataLibraryObject()
            self.header_extension_obj.objects.append(self.metadata_library_obj)

        # Render the header
        data = "".join([obj.render(self) for obj in self.objects])
        data = (HeaderObject.GUID + 
                struct.pack("<QL", len(data) + 30, len(self.objects)) +
                "\x01\x02" + data)

        fileobj = file(self.filename, "rb+")
        try:
            size = len(data)
            if size > self.size:
                insert_bytes(fileobj, size - self.size, self.size)
            if size < self.size:
                delete_bytes(fileobj, self.size - size, 0)
            fileobj.seek(0)
            fileobj.write(data)
        finally:
            fileobj.close()

    def __read_file(self, fileobj):
        header = fileobj.read(30)
        if len(header) != 30 or header[:16] != HeaderObject.GUID:
            raise ASFHeaderError, "Not an ASF file."

        self.extended_content_description_obj = None
        self.content_description_obj = None
        self.header_extension_obj = None
        self.metadata_obj = None
        self.metadata_library_obj = None

        self.size, self.num_objects = struct.unpack("<QL", header[16:28])
        self.objects = []
        for i in range(self.num_objects):
            self.__read_object(fileobj)

    def __read_object(self, fileobj):
        guid, size = struct.unpack("<16sQ", fileobj.read(24))
        if guid in _object_types:
            obj = _object_types[guid]()
        else:
            obj = UnknownObject(guid)
        data = fileobj.read(size - 24)
        obj.parse(self, data, fileobj, size)
        self.objects.append(obj)

    def score(filename, fileobj, header):
        return header.startswith(HeaderObject.GUID) * 2
    score = staticmethod(score) 

Open = ASF
