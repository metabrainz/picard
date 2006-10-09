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
static PyObject *
quicktime_init(PyObject *self, PyObject *args)
{
    return Py_BuildValue("");
}

static PyObject *
quicktime_done(PyObject *self, PyObject *args)
{
    return Py_BuildValue("");
}

static PyObject *
quicktime_decode(PyObject *self, PyObject *args)
{
    PyObject *filename;

    if (!PyArg_ParseTuple(args, "U", &filename))
        return NULL;

	PyErr_SetString(PyExc_NotImplementedError, "");
	return NULL;
}

static PyMethodDef quicktime_methods[] = {
    {"init", quicktime_init, METH_VARARGS, ""},
    {"done", quicktime_done, METH_VARARGS, ""},
    {"decode", quicktime_decode, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initquicktime(void)
{
    (void)Py_InitModule("quicktime", quicktime_methods);
}

