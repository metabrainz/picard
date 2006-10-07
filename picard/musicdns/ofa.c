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

#include <Python.h>
#include <ofa1/ofa.h>

static PyObject *
create_print(PyObject *self, PyObject *args)
{
    PyObject *buffer;
    int samples, sample_rate, stereo;
    const char *fingerprint;

    if (!PyArg_ParseTuple(args, "Oiii", &buffer, &samples, &sample_rate, &stereo))
        return NULL;

    fingerprint = ofa_create_print(PyCObject_AsVoidPtr(buffer),
                                   OFA_LITTLE_ENDIAN,
                                   samples,
                                   sample_rate,
                                   stereo);

    if (fingerprint)
        return PyString_FromString(fingerprint);
    else
        Py_RETURN_NONE;
}

static PyMethodDef ofa_methods[] = {
    {"create_print", create_print, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initofa(void)
{
    (void)Py_InitModule("ofa", ofa_methods);
}

