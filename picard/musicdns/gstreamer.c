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

#include <gst/gst.h>
#include <Python.h>

typedef struct {
	gboolean exit_loop;
	unsigned char *audio_buffer;
	int audio_buffer_size;
	unsigned char *audio_buffer_cur;
	int srate, channels, depth, width;
    gboolean sign;
} DecoderData;

static void
link_pad(GstElement *element, GstPad *pad, gboolean last, GstElement *sink)
{
    GstPad *sinkpad = gst_element_get_pad(sink, "sink");
    gst_pad_link(pad, sinkpad);
    g_object_unref(G_OBJECT(sinkpad));
}

static void
handoff_cb(GstElement *sink, GstBuffer *buffer, GstPad *pad, DecoderData *data)
{
    GstStructure *str;
    int size;

    if (!data->audio_buffer) {
		str = gst_caps_get_structure(GST_BUFFER_CAPS(buffer), 0);
		if (str) {
	        gst_structure_get_int(str, "rate", &data->srate);
	        gst_structure_get_int(str, "width", &data->width);
	        gst_structure_get_int(str, "channels", &data->channels);
	        gst_structure_get_int(str, "depth", &data->depth);
	        gst_structure_get_boolean(str, "signed", &data->sign);
	        g_print("%d %d %d %d %d\n", data->srate, data->channels, data->depth, data->sign, data->width);
			data->audio_buffer_size = 135 * data->srate * data->channels * 2;
			data->audio_buffer = g_malloc(data->audio_buffer_size);
			data->audio_buffer_cur = data->audio_buffer;
        }
    }
    
    size = GST_BUFFER_SIZE(buffer);
    if (size > data->audio_buffer_size)
		size = data->audio_buffer_size;
	
  	memcpy(data->audio_buffer_cur, GST_BUFFER_DATA(buffer), size);
    data->audio_buffer_size -= size;
    data->audio_buffer_cur += size;
    
//    unsigned time = GST_BUFFER_TIMESTAMP(buffer) / GST_SECOND;
//    g_print("%02d:%02d %d\n", time / 60, time % 60, GST_BUFFER_SIZE(buffer));

    if (data->audio_buffer_size <= 0) {
    	data->exit_loop = TRUE;
	}
}

static GstBusSyncReply 
sync_handler(GstBus *bus, GstMessage *message, DecoderData *data)
{
   	g_print("Message %s\n", gst_message_type_get_name(GST_MESSAGE_TYPE(message)));
   	
    switch(GST_MESSAGE_TYPE(message)) {
        case GST_MESSAGE_EOS:
        	data->exit_loop = TRUE;
	        break;
        case GST_MESSAGE_ERROR:
        	data->exit_loop = TRUE;
        	break;
        default:
        	break;
    }
        
    gst_message_unref(message);
    return GST_BUS_DROP;
}

static PyObject *
gstreamer_init(PyObject *self, PyObject *args)
{
    gst_init(NULL, NULL);
    return Py_BuildValue("");
}

static PyObject *
gstreamer_done(PyObject *self, PyObject *args)
{
    return Py_BuildValue("");
}

static PyObject *
gstreamer_decode(PyObject *self, PyObject *args)
{
	GstElement *pipeline, *source, *decoder, *conv, *sink;
    GstBus *bus;
    PyObject *filename;
	PyThreadState *_save;
	DecoderData data;

    if (!PyArg_ParseTuple(args, "S", &filename))
        return NULL;

	memset(&data, 0, sizeof(data));

    Py_UNBLOCK_THREADS

    pipeline = gst_pipeline_new("pipeline");
  
    source = gst_element_factory_make ("filesrc", "source");
    g_assert(source);
  
    decoder = gst_element_factory_make("decodebin", "decoder");
    g_assert(decoder);
  
    conv = gst_element_factory_make ("audioconvert", "converter");
    g_assert(conv);
    
    sink = gst_element_factory_make ("fakesink", "sink");
    g_assert(sink);

    g_object_set (G_OBJECT (source), "location", PyString_AS_STRING(filename), NULL);

    gst_bin_add_many (GST_BIN (pipeline), source, decoder, conv, sink, NULL);

    gst_element_link(source, decoder);
    gst_element_link_many(conv, sink, NULL);
    
    g_object_set(G_OBJECT(sink), "signal-handoffs", TRUE, NULL);
    g_signal_connect(sink, "handoff", G_CALLBACK(handoff_cb), &data);  
    g_signal_connect(decoder, "new-decoded-pad", G_CALLBACK(link_pad), conv);  

    gst_element_set_clock(pipeline, NULL);
    gst_element_set_state(pipeline, GST_STATE_PLAYING);

    bus = gst_pipeline_get_bus(GST_PIPELINE (pipeline));
    gst_bus_set_sync_handler(bus, (GstBusSyncHandler)&sync_handler, &data);

	// FIXME    
	data.exit_loop = FALSE;
    while (!data.exit_loop)
    	sleep(1);
    
    gst_object_unref(bus);

    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(GST_OBJECT (pipeline));
    
    Py_BLOCK_THREADS

	return Py_BuildValue("(N,i,i,i,i)", PyCObject_FromVoidPtr(data.audio_buffer, g_free),
		                 (data.audio_buffer_cur - data.audio_buffer) / 2, data.srate, data.channels == 2 ? 1 : 0, 0);
}

static PyMethodDef gstreamer_methods[] = {
    {"init", gstreamer_init, METH_VARARGS, ""},
    {"done", gstreamer_done, METH_VARARGS, ""},
    {"decode", gstreamer_decode, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initgstreamer(void)
{
    (void)Py_InitModule("gstreamer", gstreamer_methods);
}

