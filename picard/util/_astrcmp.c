/*
 * Picard, the next-generation MusicBrainz tagger
 * Copyright (C) 2018 Philipp Wolfer
 * Copyright (C) 2006 Lukáš Lalinský
 * Copyright (C) 2003 Benbuck Nason
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

/***
 *
 * Approximate string comparison
 *
 * This work is based on the Levenshtein Metric or "edit distance", which is
 * well known, simple, and seems to be unencumbered by any usage restrictions.
 * For more information on the Levenshtein Distance you can refer to the web,
 * e.g. http://www.merriampark.com/ld.htm
 *
 * Accuracy and speed enhancements could probably be made to this algorithm by
 * implementing the improvements suggested by such people as Esko Ukkonen, Hal
 * Berghel & David Roach, and Sun Wu and Udi Manber.
 *
 * This has been successfully compiled using:
 *	Microsoft Visual C++ 6 SP 5
 *	GNU gcc 3.2 & Cygwin
 *	GNU gcc 3.2 & MinGW
 *
 * Benbuck Nason, February 28th, 2003
 *
 ***/

#include <Python.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>


/***
 * Compute Levenshtein distance. Levenshtein distance, also known as
 * "edit distance," is a measure of the cost to transform one string
 * into another.
 ***/

#define MIN(x, y) (((x) > (y)) ? (y) : (x))
#define MAX(x, y) (((x) > (y)) ? (x) : (y))
#define MATRIX(a, b) matrix[(b) * (len1 + 1) + (a)]

float LevenshteinDistance(const Py_UCS4 * s1, Py_ssize_t len1,
                          const Py_UCS4 * s2, Py_ssize_t len2)
{
	int *matrix, index1, index2;
	float result;

	/* Step 1 */
	/* Check string lengths */

	if (len1 == 0)
		return 0.0f;

	if (len2 == 0)
		return 0.0f;

	/* Step 2 */
	/* Allocate matrix for algorithm and fill it with default values */

	matrix = malloc(sizeof(int) * (len1 + 1) * (len2 + 1));

	for (index1 = 0; index1 <= len1; index1++)
	    MATRIX(index1, 0) = index1;

	for (index2 = 0; index2 <= len2; index2++)
	    MATRIX(0, index2) = index2;

	/* Step 3 */
	/* Loop through first string */

	for (index1 = 1; index1 <= len1; index1++)
	{
		Py_UCS4 s1_current = s1[index1 - 1];

		/* Step 4 */
		/* Loop through second string */

		for (index2 = 1; index2 <= len2; index2++)
		{
			Py_UCS4 s2_current = s2[index2 - 1];

			/* Step 5 */
			/* Calculate cost of this iteration
			   (handles deletion, insertion, and substitution) */

			int cost = (s1_current == s2_current) ? 0 : 1;

			/* Step 6 */
			/* Calculate the total cost up to this point */

			int above = MATRIX(index1 - 1, index2);
			int left = MATRIX(index1, index2 - 1);
			int diagonal = MATRIX(index1 - 1, index2 - 1);
			int cell = MIN(MIN(above + 1, left + 1), diagonal + cost);

			/* Step 6a */
			/* Also cover transposition. This step is taken from:
			   Berghel, Hal ; Roach, David : "An Extension of Ukkonen's
			   Enhanced Dynamic Programming ASM Algorithm"
			   (http://berghel.net/publications/asm/asm.php) */

			if (index1 > 2 && index2 > 2)
			{
				int trans = MATRIX(index1 - 2, index2 - 2) + 1;
				if (s1[index1 - 2] != s2_current)
					trans++;
				if (s1_current != s2[index2 - 2])
					trans++;
				if (cell > trans)
					cell = trans;
			}

			MATRIX(index1, index2) = cell;
		}
	}


	/* Step 7 */
	/* Return result */

	result = ((float)1 - ((float)MATRIX(len1, len2) / (float)MAX(len1, len2)));

	free(matrix);

	return result;
}

static PyObject *
astrcmp(PyObject *self, PyObject *args)
{
	PyObject *s1, *s2;
	float d;
	Py_UCS4 *us1, *us2;
	Py_ssize_t len1, len2;
	PyThreadState *_save;

	if (!PyArg_ParseTuple(args, "UU", &s1, &s2))
		return NULL;

	if (PyUnicode_READY(s1) == -1 || PyUnicode_READY(s2) == -1)
		return NULL;

	len1 = PyUnicode_GetLength(s1);
	len2 = PyUnicode_GetLength(s2);
	us1 = PyUnicode_AsUCS4Copy(s1);
	us2 = PyUnicode_AsUCS4Copy(s2);

	Py_UNBLOCK_THREADS
	d = LevenshteinDistance(us1, len1, us2, len2);
	Py_BLOCK_THREADS

	PyMem_Free(us1);
	PyMem_Free(us2);

	return Py_BuildValue("f", d);
}

static PyMethodDef AstrcmpMethods[] = {
	{"astrcmp", astrcmp, METH_VARARGS, "Compute Levenshtein distance"},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef AstrcmpModule =
{
    PyModuleDef_HEAD_INIT,
    "astrcmp", /* name of module */
    NULL,      /* module documentation, may be NULL */
    -1,        /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    AstrcmpMethods
};

PyMODINIT_FUNC
PyInit__astrcmp(void)
{
    return PyModule_Create(&AstrcmpModule);
}
