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
 * This has been succesfully compiled using:
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
 * Get minimum of three values
 ***/

int min3(int a, int b, int c)
{
	int mi;

	mi = a;
	if (b < mi)
	{
		mi = b;
	}
	if (c < mi)
	{
		mi = c;
	}
	return mi;
}

/***
 * Get the contents of the specified cell in the matrix 
 ***/

int GetCellContents(int * matrix, int col, int row, int column_count)
{
	int const * const cell = matrix + col + (row * (column_count + 1));
	return *cell;

}

/***
 * Fill the specified cell in the matrix with the given contents
 ***/

void PutCellContents(int * matrix, int col, int row, int column_count, int contents)
{
	int * const cell = matrix + col + (row * (column_count + 1));
	*cell = contents;

}

/***
 * Compute Levenshtein distance
 ***/

float LevenshteinDistance(const Py_UNICODE * s1, int len1,
	                      const Py_UNICODE * s2, int len2)
{
	int * matrix; /* pointer to matrix */
	int maxlen; /* length of larger string */
	int index1; /* iterates through s1 */
	int index2; /* iterates through s2 */
	Py_UNICODE s1_current; /* current character of s1 */
	Py_UNICODE s2_current; /* current character of s2 */
	int cost; /* cost */
	int result; /* result */
	int cell; /* contents of s2 cell */
	int above; /* contents of cell immediately above */
	int left; /* contents of cell immediately to left */
	int diagonal; /* contents of cell immediately above and to left */
	int cell_count; /* number of cells in matrix */

	/* Step 1 */
	/* Check string lengths */

	if ((s1 == NULL) || (s2 == NULL))
	{
		return (float)0;
	}

	if (len1 == 0)
	{
		return (float)len2;
	}
	if (len2 == 0)
	{
		return (float)len1;
	}

	/* Step 2 */
	/* Allocate matrix for algorithm and fill it with default values */

	cell_count = (len1 + 1) * (len2 + 1) * sizeof(int);
	matrix = (int *)malloc(cell_count);

	for (index1 = 0; index1 <= len1; index1++)
	{
		PutCellContents(matrix, index1, 0, len1, index1);
	}

	for (index2 = 0; index2 <= len2; index2++)
	{
		PutCellContents(matrix, 0, index2, len1, index2);
	}

	/* Step 3 */
	/* Loop through first string */

	for (index1 = 1; index1 <= len1; index1++)
	{
		s1_current = s1[index1 - 1];

		/* Step 4 */
		/* Loop through second string */

		for (index2 = 1; index2 <= len2; index2++)
		{
			s2_current = s2[index2 - 1];

			/* Step 5 */
			/* Calculate cost of this iteration
			   (handles deletion, insertion, and substitution) */

			if (s1_current == s2_current)
			{
				cost = 0;
			}
			else
			{
				cost = 1;
			}

			/* Step 6 */
			/* Calculate the total cost up to this point */

			above = GetCellContents(matrix, index1 - 1, index2, len1);
			left = GetCellContents(matrix, index1, index2 -1 , len1);
			diagonal = GetCellContents(matrix, index1 - 1, index2 - 1, len1);
			cell = min3(above + 1, left + 1, diagonal + cost);

			/* Step 6a */
			/* Also cover transposition. This step is taken from:
			   Berghel, Hal ; Roach, David : "An Extension of Ukkonen's 
			   Enhanced Dynamic Programming ASM Algorithm"
			   (http://www.acm.org/~hlb/publications/asm/asm.html) */
			
			if ((index1 > 2) && (index2 > 2))
			{
				int trans = GetCellContents(matrix, index1 - 2, index2 - 2, len1) + 1;
				if (s1[index1 - 2] != s2_current)
				{
					trans++;
				}
				if (s1_current != s2[index2 - 2])
				{
					trans++;
				}
				if (cell > trans)
				{
					cell = trans;
				}
			}

			PutCellContents(matrix, index1, index2, len1, cell);
		}
	}

	/* Step 7 */
	/* Clean up and return result */

	result = GetCellContents(matrix, len1, len2, len1);
	free(matrix);

	maxlen = (len2 > len1) ? len2 : len1; /* max */
#	ifdef DEBUG
		printf("Levenshtein Distance: %d of %d\n", result, maxlen);
#	endif
	return ((float)1 - ((float)result / (float)maxlen));
}

static PyObject *
astrcmp(PyObject *self, PyObject *args)
{
    PyObject *s1, *s2;
	float d;

    if (!PyArg_ParseTuple(args, "UU", &s1, &s2))
        return NULL;

	d = LevenshteinDistance(PyUnicode_AS_UNICODE(s1), PyUnicode_GetSize(s1),
	                        PyUnicode_AS_UNICODE(s2), PyUnicode_GetSize(s2));
    return Py_BuildValue("f", d);
}

static PyMethodDef AstrcmpMethods[] = {
    {"astrcmp", astrcmp, METH_VARARGS, "Compute Levenshtein distance"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initastrcmp(void)
{
    (void)Py_InitModule("astrcmp", AstrcmpMethods);
}
