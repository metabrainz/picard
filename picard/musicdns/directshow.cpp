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
#include <tchar.h>
#include <dshow.h>
#include <stdio.h>
#include <qedit.h>
#include <atlbase.h>

/* Lots of ugly DirectX code... */

/**
 * Find an Unconnected Pin on a Filter
 *
 * @see http://msdn.microsoft.com/library/default.asp?url=/library/en-us/directshow/htm/findanunconnectedpinonafilter.asp
 */
HRESULT GetUnconnectedPin(
    IBaseFilter *pFilter,   // Pointer to the filter.
    PIN_DIRECTION PinDir,   // Direction of the pin to find.
    IPin **ppPin)           // Receives a pointer to the pin.
{
    *ppPin = 0;
    IEnumPins *pEnum = 0;
    IPin *pPin = 0;
    HRESULT hr = pFilter->EnumPins(&pEnum);
    if (FAILED(hr))
    {
        return hr;
    }
    while (pEnum->Next(1, &pPin, NULL) == S_OK)
    {
        PIN_DIRECTION ThisPinDir;
        pPin->QueryDirection(&ThisPinDir);
        if (ThisPinDir == PinDir)
        {
            IPin *pTmp = 0;
            hr = pPin->ConnectedTo(&pTmp);
            if (SUCCEEDED(hr))  // Already connected, not the pin we want.
            {
                pTmp->Release();
            }
            else  // Unconnected, this is the pin we want.
            {
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

/**
 * Connect a Pin To a Filter
 *
 * @see http://msdn.microsoft.com/library/default.asp?url=/library/en-us/directshow/htm/connecttwofilters.asp
 */
HRESULT ConnectFilters(
    IGraphBuilder *pGraph, // Filter Graph Manager.
    IPin *pOut,            // Output pin on the upstream filter.
    IBaseFilter *pDest)    // Downstream filter.
{
    if ((pGraph == NULL) || (pOut == NULL) || (pDest == NULL))
    {
        return E_POINTER;
    }
#ifdef debug
        PIN_DIRECTION PinDir;
        pOut->QueryDirection(&PinDir);
        _ASSERTE(PinDir == PINDIR_OUTPUT);
#endif

    // Find an input pin on the downstream filter.
    IPin *pIn = 0;
    HRESULT hr = GetUnconnectedPin(pDest, PINDIR_INPUT, &pIn);
    if (FAILED(hr))
    {
        return hr;
    }
    // Try to connect them.
    hr = pGraph->Connect(pOut, pIn);
    pIn->Release();
    return hr;

}

/**
 * Connect Two Filters
 *
 * @see http://msdn.microsoft.com/library/default.asp?url=/library/en-us/directshow/htm/connecttwofilters.asp
 */
HRESULT ConnectFilters(
    IGraphBuilder *pGraph,
    IBaseFilter *pSrc,
    IBaseFilter *pDest)
{
    if ((pGraph == NULL) || (pSrc == NULL) || (pDest == NULL))
    {
        return E_POINTER;
    }

    // Find an output pin on the first filter.
    IPin *pOut = 0;
    HRESULT hr = GetUnconnectedPin(pSrc, PINDIR_OUTPUT, &pOut);
    if (FAILED(hr))
    {
        return hr;
    }
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

    STDMETHODIMP_(ULONG) AddRef()  { return 2; }
    STDMETHODIMP_(ULONG) Release() { return 1; }

    STDMETHODIMP QueryInterface(REFIID riid, void ** ppv)
    {
        if (riid == IID_ISampleGrabberCB || riid == IID_IUnknown) {
            *ppv = (void *)static_cast<ISampleGrabberCB *>(this);
            return NOERROR;
        }

        return E_NOINTERFACE;
    }

    STDMETHODIMP SampleCB(double SampleTime, IMediaSample * pSample)
    {
        return 0;
    }

    STDMETHODIMP BufferCB(double SampleTime, BYTE * pBuffer, long BufferLen)
    {
//		CAutoLock autoLock(&lock);

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

	long STDMETHODCALLTYPE GetBytesLeft()
	{
//		CAutoLock autoLock(&lock);

		return bytesLeft;
	}

private:

//	CCritSec lock;
	long bytesLeft;
	unsigned char *buffer;

};

static PyObject *
ds_init(PyObject *self, PyObject *args)
{
    HRESULT hr = CoInitialize(NULL);
    if (FAILED(hr)) {
		//errorMessage = "Could not initialize COM library";
		return Py_BuildValue("b", 0);
    }
    return Py_BuildValue("b", 1);
}

static PyObject *
ds_done(PyObject *self, PyObject *args)
{
	CoUninitialize();
    return Py_BuildValue("b", 1);
}

#define DEBUG 0
//#include <iostream>
//#include <string>
//using namespace std;

static PyObject *
ds_decode(PyObject *self, PyObject *args)
{
    PyObject *filename;
	IBaseFilter *pGrabberF = NULL;
	HRESULT hr;

    if (!PyArg_ParseTuple(args, "U", &filename))
        return NULL;

#ifdef DEBUG
	printf("Decoding...\n");
#endif

	IGraphBuilder *pGraph;
	hr = CoCreateInstance(CLSID_FilterGraph, NULL, CLSCTX_INPROC_SERVER,
		                  IID_IGraphBuilder, (void **)&pGraph);

	hr = CoCreateInstance(CLSID_SampleGrabber, NULL, CLSCTX_INPROC_SERVER,
		                  IID_IBaseFilter, (void**)&pGrabberF);
	if (FAILED(hr))
	{
		PyErr_SetString(PyExc_Exception, "Could not create the Sample Grabber.");
		return NULL;
	}

	hr = pGraph->AddFilter(pGrabberF, L"Sample Grabber");
	if (FAILED(hr))
	{
		PyErr_SetString(PyExc_Exception, "Could not add Sample Grabber filter to graph.");
		return NULL;
	}

	ISampleGrabber *pGrabber;
	hr = pGrabberF->QueryInterface(IID_ISampleGrabber, (void**)&pGrabber);
	if (FAILED(hr))
	{
		PyErr_SetString(PyExc_Exception, "Could not create ISampleGrabber interface.");
		return NULL;
	}

	AM_MEDIA_TYPE smt;
	ZeroMemory(&smt, sizeof(AM_MEDIA_TYPE));
	smt.majortype = MEDIATYPE_Audio;
	smt.subtype = MEDIASUBTYPE_PCM;
	smt.lSampleSize = 8;
	smt.formattype = FORMAT_WaveFormatEx;
	hr = pGrabber->SetMediaType(&smt);
	if (FAILED(hr))
	{
		PyErr_SetString(PyExc_Exception, "Could not set media type for pSampleGrabber.");
		return NULL;
	}

	pGrabber->SetOneShot(FALSE);
	pGrabber->SetBufferSamples(FALSE);

	IBaseFilter *pSrc;
	hr = pGraph->AddSourceFilter(PyUnicode_AS_UNICODE(filename), L"Source", &pSrc);
	if (FAILED(hr))
	{
		PyErr_SetString(PyExc_IOError, "Couldn't add the DirectX source.");
		return NULL;
	}

	hr = ConnectFilters(pGraph, pSrc, pGrabberF);
	if (FAILED(hr))
	{
		PyErr_SetString(PyExc_Exception, "ConnectFilters(pGraph, pSrc, pGrabberF)");
		return NULL;
	}

    // A Null Renderer does not display the video
    // but it allows the Sample Grabber to run.
	IBaseFilter *nullRenderer;
	CoCreateInstance(CLSID_NullRenderer, NULL, CLSCTX_INPROC_SERVER, IID_IBaseFilter, (void**)&nullRenderer);

	// Connect grabber to the null renderer
	pGraph->AddFilter(nullRenderer, L"Null Renderer");
	hr = ConnectFilters(pGraph, pGrabberF, nullRenderer);
	if (FAILED(hr))
	{
		PyErr_SetString(PyExc_Exception, "ConnectFilters(pGraph, pGrabberF, nullRenderer)");
		return NULL;
	}

	AM_MEDIA_TYPE cmt;
	pGrabber->GetConnectedMediaType(&cmt);
	WAVEFORMATEX *wf;
	wf = ((WAVEFORMATEX *)cmt.pbFormat);

	int stereo = wf->nChannels == 2 ? 1 : 0;
	int sample_rate = wf->nSamplesPerSec;
	int bits_per_sample = wf->wBitsPerSample;

	long bytes = 135 * wf->nSamplesPerSec * 2 * wf->nChannels;
	unsigned char *buffer = new unsigned char[bytes];
	ZeroMemory(buffer, bytes);

	CFakeCallback callback(bytes, buffer);

	CComQIPtr<ISampleGrabberCB, &IID_ISampleGrabberCB> pCBa(&callback);
	hr = pGrabber->SetCallback(pCBa, 1);
	if (FAILED(hr))
	{
		PyErr_SetString(PyExc_Exception,
			            "Couldn't set callback for the sample grabber.");
		return NULL;
	}

    // Clear the graph clock
    IMediaFilter *mediaFilter = 0;
    pGraph->QueryInterface(IID_IMediaFilter, (void **)&mediaFilter);
    mediaFilter->SetSyncSource(NULL);
    mediaFilter->Release();

	CComQIPtr<IMediaControl, &IID_IMediaControl> pControl(pGraph);
	CComQIPtr<IMediaEvent, &IID_IMediaEvent> pEvent(pGraph);
	CComQIPtr<IMediaSeeking, &IID_IMediaSeeking> pMediaSeeking(pGraph);

	LONGLONG duration = 0;
	pMediaSeeking->GetDuration(&duration);
	duration /= 10000;
#ifdef DEBUG
	printf("duration %d\n", duration);

	printf("Running the DirectX graph...\n");
#endif
    Py_BEGIN_ALLOW_THREADS
	pControl->Run();
	do {
		long evCode = 0;
		if (pEvent->WaitForCompletion(10, &evCode) == S_OK)
			break;
	} while (callback.GetBytesLeft() > 0);
	pControl->Stop();
    Py_END_ALLOW_THREADS
#ifdef DEBUG
	printf("OK\n");
#endif

	pGraph->Release();

	return Py_BuildValue("(N,i,i,i,i)", PyCObject_FromVoidPtr(buffer, free),
		                 bytes / 2, sample_rate, stereo, duration);
}

static PyMethodDef DirectShowMethods[] = {
    {"init", ds_init, METH_VARARGS, ""},
    {"done", ds_done, METH_VARARGS, ""},
    {"decode", ds_decode, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initdirectshow(void)
{
    (void)Py_InitModule("directshow", DirectShowMethods);
}

