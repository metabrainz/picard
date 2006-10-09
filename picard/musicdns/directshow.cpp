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
#include <dshow.h>
#include <qedit.h>
#include <atlbase.h>

#define DEBUG 1
#ifdef DEBUG
#include <stdio.h>
#endif

// Find an Unconnected Pin on a Filter
// http://msdn.microsoft.com/library/default.asp?url=/library/en-us/directshow/htm/findanunconnectedpinonafilter.asp
HRESULT
GetUnconnectedPin(IBaseFilter *pFilter, PIN_DIRECTION PinDir, IPin **ppPin)
{
    *ppPin = 0;
    IEnumPins *pEnum = 0;
    IPin *pPin = 0;
    HRESULT hr = pFilter->EnumPins(&pEnum);
    if (FAILED(hr))
        return hr;

    while (pEnum->Next(1, &pPin, NULL) == S_OK) {
        PIN_DIRECTION ThisPinDir;
        pPin->QueryDirection(&ThisPinDir);
        if (ThisPinDir == PinDir) {
            IPin *pTmp = 0;
            hr = pPin->ConnectedTo(&pTmp);
			// Already connected, not the pin we want.
            if (SUCCEEDED(hr)) {
                pTmp->Release();
            }
			// Unconnected, this is the pin we want.
            else {
                pEnum->Release();
                *ppPin = pPin;
                return S_OK;
            }
        }
        pPin->Release();
    }
    pEnum->Release();
    // Did not find a matching pin.
    return E_FAIL;
}

// Connect a Pin To a Filter
// http://msdn.microsoft.com/library/default.asp?url=/library/en-us/directshow/htm/connecttwofilters.asp
HRESULT
ConnectFilters(IGraphBuilder *pGraph, IPin *pOut, IBaseFilter *pDest)
{
    if ((pGraph == NULL) || (pOut == NULL) || (pDest == NULL))
        return E_POINTER;

    // Find an input pin on the downstream filter.
    IPin *pIn = 0;
    HRESULT hr = GetUnconnectedPin(pDest, PINDIR_INPUT, &pIn);
    if (FAILED(hr))
        return hr;

    // Try to connect them.
    hr = pGraph->Connect(pOut, pIn);
    pIn->Release();
    return hr;
}

// Connect Two Filters
// http://msdn.microsoft.com/library/default.asp?url=/library/en-us/directshow/htm/connecttwofilters.asp
HRESULT
ConnectFilters(IGraphBuilder *pGraph, IBaseFilter *pSrc, IBaseFilter *pDest)
{
    if ((pGraph == NULL) || (pSrc == NULL) || (pDest == NULL))
        return E_POINTER;

    // Find an output pin on the first filter.
    IPin *pOut = 0;
    HRESULT hr = GetUnconnectedPin(pSrc, PINDIR_OUTPUT, &pOut);
    if (FAILED(hr))
        return hr;

    // Try to connect them.
    hr = ConnectFilters(pGraph, pOut, pDest);
    pOut->Release();
    return hr;
}

class CFakeCallback : public ISampleGrabberCB
{
public:

	CFakeCallback(long bytes, unsigned char *buffer)
		: bytesLeft(bytes), buffer(buffer)
	{
	}

    STDMETHODIMP_(ULONG) AddRef() { return 2; }
    STDMETHODIMP_(ULONG) Release() { return 1; }

    STDMETHODIMP
	QueryInterface(REFIID riid, void **ppv)
    {
        if (riid == IID_ISampleGrabberCB || riid == IID_IUnknown) {
            *ppv = (void *)static_cast<ISampleGrabberCB *>(this);
            return NOERROR;
        }
        return E_NOINTERFACE;
    }

    STDMETHODIMP
	SampleCB(double SampleTime, IMediaSample *pSample)
    {
        return 0;
    }

    STDMETHODIMP
	BufferCB(double SampleTime, BYTE *pBuffer, long BufferLen)
    {
		if (BufferLen < bytesLeft) {
			memcpy(buffer, pBuffer, BufferLen);
			buffer += BufferLen;
			bytesLeft -= BufferLen;
		}
		else if (bytesLeft > 0) {
			memcpy(buffer, pBuffer, bytesLeft);
			buffer += bytesLeft;
			bytesLeft = 0;
		}
        return 0;
    }

	long STDMETHODCALLTYPE
	GetBytesLeft()
	{
		return bytesLeft;
	}

private:

	long bytesLeft;
	unsigned char *buffer;

};

static PyObject *
directshow_init(PyObject *self, PyObject *args)
{
    HRESULT hr = CoInitialize(NULL);
    if (FAILED(hr)) {
		PyErr_SetString(PyExc_Exception, "Couldn't add the source file.");
		return NULL;
    }
    return Py_BuildValue("");
}

static PyObject *
directshow_done(PyObject *self, PyObject *args)
{
	CoUninitialize();
    return Py_BuildValue("");
}

static PyObject *
directshow_decode(PyObject *self, PyObject *args)
{
    PyObject *filename;
	HRESULT hr;
	PyThreadState *_save;

    if (!PyArg_ParseTuple(args, "U", &filename))
        return NULL;

    Py_UNBLOCK_THREADS

#ifdef DEBUG
	printf("Decoding using DirectShow...\n");
#endif

	CComPtr<IFilterGraph> pGraph;
	hr = pGraph.CoCreateInstance(CLSID_FilterGraph);
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't create the filter graph manager.");
		return NULL;
	}

	CComQIPtr<IGraphBuilder, &IID_IGraphBuilder> pBuilder(pGraph);

	//////////////////////////////////////////////////////////////////////////
	// Source file
	//////////////////////////////////////////////////////////////////////////
	
	CComPtr<IBaseFilter> pSource;
	hr = pBuilder->AddSourceFilter(PyUnicode_AS_UNICODE(filename), L"Source", &pSource);
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't add the source file.");
		return NULL;
	}

	//////////////////////////////////////////////////////////////////////////
	// Sample grabber
	//////////////////////////////////////////////////////////////////////////
	
	CComPtr<IBaseFilter> pGrabberFilter;
	hr = pGrabberFilter.CoCreateInstance(CLSID_SampleGrabber);
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't create the sample grabber.");
		return NULL;
	}

	CComQIPtr<ISampleGrabber, &IID_ISampleGrabber> pGrabber(pGrabberFilter);

	AM_MEDIA_TYPE smt;
	ZeroMemory(&smt, sizeof(AM_MEDIA_TYPE));
	smt.majortype = MEDIATYPE_Audio;
	smt.subtype = MEDIASUBTYPE_PCM;
	smt.lSampleSize = 8;
	smt.formattype = FORMAT_WaveFormatEx;
	hr = pGrabber->SetMediaType(&smt);
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Could not set media type for pSampleGrabber.");
		return NULL;
	}

	pGrabber->SetOneShot(FALSE);
	pGrabber->SetBufferSamples(FALSE);

	hr = pBuilder->AddFilter(pGrabberFilter, L"Sample Grabber");
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't add the sample grabber.");
		return NULL;
	}

	hr = ConnectFilters(pBuilder, pSource, pGrabberFilter);
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't connect the source file and the sample grabber.");
		return NULL;
	}

	//////////////////////////////////////////////////////////////////////////
	// Null renderer
	//////////////////////////////////////////////////////////////////////////
	
	CComPtr<IBaseFilter> pNullRenderer;
	hr = pNullRenderer.CoCreateInstance(CLSID_NullRenderer);
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't create the null renderer.");
		return NULL;
	}

	hr = pBuilder->AddFilter(pNullRenderer, L"Null Renderer");
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't add the null renderer.");
		return NULL;
	}

	hr = ConnectFilters(pBuilder, pGrabberFilter, pNullRenderer);
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't connect the sample grabber and the null renderer.");
		return NULL;
	}

	//////////////////////////////////////////////////////////////////////////
	// Setup the sample grabber callback
	//////////////////////////////////////////////////////////////////////////

	AM_MEDIA_TYPE cmt;
	pGrabber->GetConnectedMediaType(&cmt);
	WAVEFORMATEX *wf = ((WAVEFORMATEX *)cmt.pbFormat);

	int stereo = wf->nChannels == 2 ? 1 : 0;
	int sample_rate = wf->nSamplesPerSec;
	int bits_per_sample = wf->wBitsPerSample;

	long bytes = 135 * wf->nSamplesPerSec * 2 * wf->nChannels;
	BYTE *buffer = (BYTE *)malloc(bytes * sizeof(BYTE));
	ZeroMemory(buffer, bytes);

	CFakeCallback callback(bytes, buffer);
	CComQIPtr<ISampleGrabberCB, &IID_ISampleGrabberCB> pGrabberCallback(&callback);
	hr = pGrabber->SetCallback(pGrabberCallback, 1);
	if (FAILED(hr)) {
		Py_BLOCK_THREADS
		PyErr_SetString(PyExc_Exception, "Couldn't set callback for the sample grabber.");
		return NULL;
	}

    // Clear the graph clock
	CComQIPtr<IMediaFilter, &IID_IMediaFilter> pMediaFilter(pGraph);
    pMediaFilter->SetSyncSource(NULL);

	// Get the stream duration
	CComQIPtr<IMediaSeeking, &IID_IMediaSeeking> pSeeking(pGraph);
	REFERENCE_TIME duration = 0;
	pSeeking->GetDuration(&duration);
	duration /= 10000;

	CComQIPtr<IMediaControl, &IID_IMediaControl> pControl(pGraph);
	CComQIPtr<IMediaEvent, &IID_IMediaEvent> pEvent(pGraph);

#ifdef DEBUG
	printf("Running the DirectShow graph...\n");
#endif

	pControl->Run();
	do {
		long evCode = 0;
		if (pEvent->WaitForCompletion(10, &evCode) == S_OK)
			break;
	} while (callback.GetBytesLeft() > 0);
	pControl->Stop();

#ifdef DEBUG
	printf("OK\n");
#endif

    Py_BLOCK_THREADS
	return Py_BuildValue("(N,i,i,i,i)", PyCObject_FromVoidPtr(buffer, free),
		                 bytes / 2, sample_rate, stereo, duration);
}

static PyMethodDef directshow_methods[] = {
    {"init", directshow_init, METH_VARARGS, ""},
    {"done", directshow_done, METH_VARARGS, ""},
    {"decode", directshow_decode, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initdirectshow(void)
{
    (void)Py_InitModule("directshow", directshow_methods);
}

