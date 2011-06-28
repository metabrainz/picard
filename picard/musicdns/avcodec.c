/*
 * Picard, the next-generation MusicBrainz tagger
 * Copyright (C) 2006 Lukáš Lalinský
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

/* avcodec/avformat-based audio decoder for Picard */

#ifdef _MSC_VER
#define INT64_C(val) val##i64
#define inline __inline
#endif

#ifdef USE_OLD_FFMPEG_LOCATIONS
#include <avcodec.h>
#include <avformat.h>
#include <avio.h>
#else
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavformat/avio.h>
#endif
#include <Python.h>

#if (LIBAVCODEC_VERSION_INT < ((52<<16)+(64<<8)+0))
#define AVMEDIA_TYPE_AUDIO CODEC_TYPE_AUDIO
#endif

#ifdef _WIN32

#include <string.h>
#include <fcntl.h>
#include <windows.h>

static int
ufile_open(URLContext *h, const char *filename, int flags)
{
    int access;
    int fd;
    int size;
    const char *ptr;
    wchar_t *w_filename, *w_ptr;
    char *ansi_filename;

    /* skip "ufile:" */
    filename += 6;
    ptr = filename;
    w_filename = malloc(strlen(filename));
    w_ptr = w_filename;
    while (*ptr)
    {
        char a = (*ptr++) - 0x20;
        char b = (*ptr++) - 0x20;
        char c = (*ptr++) - 0x20;
        char d = (*ptr++) - 0x20;
    	  *w_ptr = a | (b << 4) | (c << 8) | (d << 12);
    	  if (*w_ptr == 0)
					break;
				w_ptr++;				   
		}
		*w_ptr = 0;

    if (flags & URL_RDWR) {
        access = O_CREAT | O_TRUNC | O_RDWR;
    } else if (flags & URL_WRONLY) {
        access = O_CREAT | O_TRUNC | O_WRONLY;
    } else {
        access = O_RDONLY;
    }
    access |= O_BINARY;

    if (GetVersion() < 0x80000000) {
        fd = _wopen(w_filename, access, 0666);
    }
    else {
        fd = -1;
        size = wcslen(w_filename) + 2;
        ansi_filename = malloc(size);
        if (ansi_filename) { 
            if (WideCharToMultiByte(CP_ACP, 0, w_filename, -1, ansi_filename, size, NULL, NULL) > 0) {
	  	          fd = _open(ansi_filename, access, 0666);
						}
            free(ansi_filename);
				}
    }

    free(w_filename);

    if (fd < 0)
        return AVERROR(ENOENT);
    h->priv_data = (void *)(size_t)fd;
    return 0;
}

static int
ufile_read(URLContext *h, unsigned char *buf, int size)
{
    int fd = (size_t)h->priv_data;
    return _read(fd, buf, size);
}

static int
ufile_write(URLContext *h, unsigned char *buf, int size)
{
    int fd = (size_t)h->priv_data;
    return _write(fd, buf, size);
}

#if LIBAVFORMAT_VERSION_MAJOR >= 52
static int64_t
ufile_seek(URLContext *h, int64_t pos, int whence)
#else
static offset_t
ufile_seek(URLContext *h, offset_t pos, int whence)
#endif
{
    int fd = (size_t)h->priv_data;
    return _lseek(fd, pos, whence);
}

static int
ufile_close(URLContext *h)
{
    int fd = (size_t)h->priv_data;
    return _close(fd);
}

URLProtocol ufile_protocol = {
    "ufile",
    ufile_open,
    ufile_read,
    ufile_write,
    ufile_seek,
    ufile_close,
};

#endif

static PyObject *
init(PyObject *self, PyObject *args)
{
    av_register_all();
#ifdef _WIN32
    register_protocol(&ufile_protocol);
#endif
    Py_RETURN_NONE;
}

static PyObject *
done(PyObject *self, PyObject *args)
{
    Py_RETURN_NONE;
}

static PyObject *
decode(PyObject *self, PyObject *args)
{
    AVFormatContext *format_context;
    AVCodecContext *codec_context;
    AVCodec *codec;
    PyObject *filename;
    AVPacket packet;
    unsigned int i;
    int buffer_size, channels, sample_rate, size, len, output_size;
    uint8_t *buffer, *buffer_ptr, *data;
    PyThreadState *_save;

#ifdef _WIN32
    Py_ssize_t w_length;
    wchar_t *w_filename, *w_ptr;
    char *e_filename, *e_ptr;

    if (!PyArg_ParseTuple(args, "U", &filename))
        return NULL;

    /* get the original filename as wchar_t* */
    w_length = PyUnicode_GetSize(filename) + 1;
		w_filename = malloc(w_length * sizeof(wchar_t));
		if (!w_filename)
        return NULL;
		memset(w_filename, 0, w_length * sizeof(wchar_t));
		PyUnicode_AsWideChar((PyUnicodeObject *)filename, w_filename, w_length - 1);

    /* 'encode' the filename, so we can pass it as char* */
		e_filename = malloc(w_length * sizeof(wchar_t) * 2 + w_length + 7);
		if (!e_filename)
        return NULL;
		strcpy(e_filename, "ufile:");
		w_ptr = w_filename;
		e_ptr = e_filename + 6;
		while (*w_ptr) {
		    *e_ptr++ = 0x20 + ((*w_ptr >>  0) & 0x0F);
		    *e_ptr++ = 0x20 + ((*w_ptr >>  4) & 0x0F);
		    *e_ptr++ = 0x20 + ((*w_ptr >>  8) & 0x0F);
		    *e_ptr++ = 0x20 + ((*w_ptr >> 12) & 0x0F);
		    w_ptr++;
		}
		*e_ptr++ = 0x20;
		*e_ptr++ = 0x20;
		*e_ptr++ = 0x20;
		*e_ptr++ = 0x20;
		/* copy ASCII filename to the end for extension-based format detection */		
		w_ptr = w_filename;
		while (*w_ptr) {
		    *e_ptr++ = (*w_ptr++) & 0xFF;
		}
		*e_ptr = 0;
		
    Py_UNBLOCK_THREADS
    if (av_open_input_file(&format_context, e_filename, NULL, 0, NULL) != 0) {
        Py_BLOCK_THREADS
        free(e_filename);
        free(w_filename);
        PyErr_SetString(PyExc_Exception, "Couldn't open the file.");
        return NULL;
    }

    free(e_filename);
    free(w_filename);
#else
    if (!PyArg_ParseTuple(args, "S", &filename))
        return NULL;

    Py_UNBLOCK_THREADS
    if (av_open_input_file(&format_context, PyString_AS_STRING(filename), NULL, 0, NULL) != 0) {
        Py_BLOCK_THREADS
        PyErr_SetString(PyExc_Exception, "Couldn't open the file.");
        return NULL;
    }
#endif

    if (av_find_stream_info(format_context) < 0) {
        Py_BLOCK_THREADS
        PyErr_SetString(PyExc_Exception, "Couldn't find stream information in the file.");
        return NULL;
    }

#ifndef NDEBUG
    dump_format(format_context, 0, PyString_AS_STRING(filename), 0);
#endif

    codec_context = NULL;
    for (i = 0; i < format_context->nb_streams; i++) {
        codec_context = (AVCodecContext *)format_context->streams[i]->codec;
        if (codec_context && codec_context->codec_type == AVMEDIA_TYPE_AUDIO)
            break;
    }
    if (codec_context == NULL) {
        Py_BLOCK_THREADS
        PyErr_SetString(PyExc_Exception, "Couldn't find any audio stream in the file.");
        return NULL;
    }

    codec = avcodec_find_decoder(codec_context->codec_id);
    if (codec == NULL) {
        Py_BLOCK_THREADS
        PyErr_SetString(PyExc_Exception, "Unknown codec.");
        return NULL;
    }

    if (avcodec_open(codec_context, codec) < 0) {
        Py_BLOCK_THREADS
        PyErr_SetString(PyExc_Exception, "Couldn't open the codec.");
        return NULL;
    }

    channels = codec_context->channels;
    sample_rate = codec_context->sample_rate;

    buffer_size = 135 * channels * sample_rate * 2;
    buffer = (uint8_t *)av_malloc(buffer_size + AVCODEC_MAX_AUDIO_FRAME_SIZE);
    buffer_ptr = buffer;
    memset(buffer, 0, buffer_size);

    while (buffer_size > 0) {
        if (av_read_frame(format_context, &packet) < 0)
            break;

        size = packet.size;
        data = packet.data;

        while (size > 0) {
            output_size = buffer_size + AVCODEC_MAX_AUDIO_FRAME_SIZE;
#if (LIBAVCODEC_VERSION_INT <= ((52<<16) + (25<<8) + 0))
            len = avcodec_decode_audio2(codec_context, (int16_t *)buffer_ptr, &output_size, data, size);
#else
            {
                AVPacket avpkt;
                av_init_packet(&avpkt);
                avpkt.data = data;
                avpkt.size = size;
                len = avcodec_decode_audio3(codec_context, (int16_t *)buffer_ptr, &output_size, &avpkt);
                av_free_packet(&avpkt);
            }
#endif

            if (len < 0)
                break;

            size -= len;
            data += len;

            if (output_size <= 0)
                continue;

            buffer_ptr += output_size;
            buffer_size -= output_size;
            if (buffer_size <= 0)
                break;
        }

        if (packet.data)
            av_free_packet(&packet);
    }

    if (codec_context)
        avcodec_close(codec_context);

    if (format_context)
        av_close_input_file(format_context);

    Py_BLOCK_THREADS

    return Py_BuildValue("(N,i,i,i,i)",
        PyCObject_FromVoidPtr(buffer, av_free),
        (buffer_ptr - buffer) / 2,
        sample_rate,
        channels == 2 ? 1 : 0,
        0);
}

static PyMethodDef avcodec_methods[] = {
    {"init", init, METH_VARARGS, ""},
    {"done", done, METH_VARARGS, ""},
    {"decode", decode, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initavcodec(void)
{
    (void)Py_InitModule("avcodec", avcodec_methods);
}
