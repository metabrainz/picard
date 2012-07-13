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

static PyObject *
init(PyObject *self, PyObject *args)
{
    av_register_all();
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
    AVFormatContext *format_context = NULL;
    AVCodecContext *codec_context;
    AVCodec *codec;
    PyObject *filename;
    AVPacket packet;
    unsigned int i;
    int buffer_size, channels, sample_rate, len, output_size;
    uint8_t *buffer, *buffer_ptr;
    PyThreadState *_save;

    if (!PyArg_ParseTuple(args, "S", &filename))
        return NULL;

    Py_UNBLOCK_THREADS
#if LIBAVFORMAT_VERSION_INT < AV_VERSION_INT(53, 2, 0)
    if (av_open_input_file(&format_context, PyString_AS_STRING(filename), NULL, 0, NULL) != 0) {
#else
    if (avformat_open_input(&format_context, PyString_AS_STRING(filename), NULL, NULL) != 0) {
#endif
        Py_BLOCK_THREADS
        PyErr_SetString(PyExc_Exception, "Couldn't open the file.");
        return NULL;
    }

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

    AVPacket avpkt;
    av_init_packet(&avpkt);

    while (buffer_size > 0) {
        if (av_read_frame(format_context, &packet) < 0)
            break;

        avpkt.size = packet.size;
        avpkt.data = packet.data;

        while (avpkt.size > 0) {
            output_size = buffer_size + AVCODEC_MAX_AUDIO_FRAME_SIZE;
#if (LIBAVCODEC_VERSION_INT <= ((52<<16) + (25<<8) + 0))
            len = avcodec_decode_audio2(codec_context, (int16_t *)buffer_ptr, &output_size, avpkt.data, avpkt.size);
#else
            len = avcodec_decode_audio3(codec_context, (int16_t *)buffer_ptr, &output_size, &avpkt);
#endif

            if (len < 0)
                break;

            avpkt.size -= len;
            avpkt.data += len;

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

    if (avpkt.data)
        av_free_packet(&avpkt);

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
