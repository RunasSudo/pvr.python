/*
 *  pvr.python - A PVR client for Kodi using Python
 *  Copyright © 2016 RunasSudo (Yingtong Li)
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include <Python.h>

#include "client.h"
#include "xbmc_pvr_dll.h"
#include "PVRDemoData.h"
#include <p8-platform/util/util.h>

using namespace std;
using namespace ADDON;

#ifdef TARGET_WINDOWS
#define snprintf _snprintf
#endif

bool m_bCreated  = false;
ADDON_STATUS  m_CurStatus = ADDON_STATUS_UNKNOWN;
PVRDemoData *m_data = NULL;
bool m_bIsPlaying  = false;
PVRDemoChannel m_currentChannel;

/* User adjustable settings are saved here.
 * Default values are defined inside client.h
 * and exported to the other source files.
 */
std::string g_strUserPath = "";
std::string g_strClientPath = "";

CHelper_libXBMC_addon *XBMC = NULL;
CHelper_libXBMC_pvr *PVR = NULL;

PyThreadState* pyState;
PyObject* pvrImpl;

ADDON_HANDLE addon_handle;

extern "C" {

#define PYTHON_LOCK() PyEval_AcquireLock(); PyThreadState_Swap(pyState);
#define PYTHON_UNLOCK() PyThreadState_Swap(NULL); PyEval_ReleaseLock();

// BEGIN PYTHON->C BRIDGE FUNCTIONS

bool PyBool_AsBool(PyObject* obj) {
	return (obj == Py_True);
}

static PyObject* bridge_XBMC_Log(PyObject* self, PyObject* args)
{
	const char *s;
	if (!PyArg_ParseTuple(args, "s", &s)) {
		PyErr_SetString(PyExc_TypeError, "parameter must be a string");
		return NULL;
	}
	
	XBMC->Log(LOG_DEBUG, "%s - %s", __FUNCTION__, s);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* bridge_PVR_TransferChannelEntry(PyObject* self, PyObject* args)
{
	PyObject* pyChannel = PyTuple_GetItem(args, 0);
	
	PVR_CHANNEL xbmcChannel;
	memset(&xbmcChannel, 0, sizeof(PVR_CHANNEL));
	
	xbmcChannel.iUniqueId = PyInt_AsLong(PyDict_GetItemString(pyChannel, "uniqueId"));
	xbmcChannel.bIsRadio = PyBool_AsBool(PyDict_GetItemString(pyChannel, "isRadio"));
	xbmcChannel.iChannelNumber = PyInt_AsLong(PyDict_GetItemString(pyChannel, "channelNumber"));
	xbmcChannel.iSubChannelNumber = PyInt_AsLong(PyDict_GetItemString(pyChannel, "subChannelNumber"));
	strcpy(xbmcChannel.strChannelName, PyString_AsString(PyDict_GetItemString(pyChannel, "channelName")));
	strcpy(xbmcChannel.strInputFormat, PyString_AsString(PyDict_GetItemString(pyChannel, "inputFormat")));
	strcpy(xbmcChannel.strStreamURL, PyString_AsString(PyDict_GetItemString(pyChannel, "streamURL")));
	xbmcChannel.iEncryptionSystem = PyInt_AsLong(PyDict_GetItemString(pyChannel, "encryptionSystem"));
	strcpy(xbmcChannel.strIconPath, PyString_AsString(PyDict_GetItemString(pyChannel, "iconPath")));
	xbmcChannel.bIsHidden = PyBool_AsBool(PyDict_GetItemString(pyChannel, "isHidden"));
	
	PVR->TransferChannelEntry(addon_handle, &xbmcChannel);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* bridge_PVR_TransferChannelGroup(PyObject* self, PyObject* args)
{
	PyObject* pyGroup = PyTuple_GetItem(args, 0);
	
	PVR_CHANNEL_GROUP xbmcGroup;
	memset(&xbmcGroup, 0, sizeof(PVR_CHANNEL_GROUP));
	
	strcpy(xbmcGroup.strGroupName, PyString_AsString(PyDict_GetItemString(pyGroup, "groupName")));
	xbmcGroup.bIsRadio = PyBool_AsBool(PyDict_GetItemString(pyGroup, "isRadio"));
	xbmcGroup.iPosition = PyInt_AsLong(PyDict_GetItemString(pyGroup, "position"));
	
	PVR->TransferChannelGroup(addon_handle, &xbmcGroup);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* bridge_PVR_TransferChannelGroupMember(PyObject* self, PyObject* args)
{
	PyObject* pyGroupMember = PyTuple_GetItem(args, 0);
	
	PVR_CHANNEL_GROUP_MEMBER xbmcGroupMember;
	memset(&xbmcGroupMember, 0, sizeof(PVR_CHANNEL_GROUP_MEMBER));
	
	strcpy(xbmcGroupMember.strGroupName, PyString_AsString(PyDict_GetItemString(pyGroupMember, "groupName")));
	xbmcGroupMember.iChannelUniqueId = PyInt_AsLong(PyDict_GetItemString(pyGroupMember, "channelUniqueId"));
	xbmcGroupMember.iChannelNumber = PyInt_AsLong(PyDict_GetItemString(pyGroupMember, "channelNumber"));
	
	PVR->TransferChannelGroupMember(addon_handle, &xbmcGroupMember);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* bridge_PVR_TransferTimerEntry(PyObject* self, PyObject* args)
{
	PyObject* pyEntry = PyTuple_GetItem(args, 0);
	
	PVR_TIMER xbmcEntry;
	memset(&xbmcEntry, 0, sizeof(PVR_TIMER));
	
	xbmcEntry.iClientIndex = PyInt_AsLong(PyDict_GetItemString(pyEntry, "clientIndex"));
	xbmcEntry.iParentClientIndex = PyInt_AsLong(PyDict_GetItemString(pyEntry, "parentClientIndex"));
	xbmcEntry.iClientChannelUid = PyInt_AsLong(PyDict_GetItemString(pyEntry, "clientChannelUid"));
	xbmcEntry.startTime = PyInt_AsLong(PyDict_GetItemString(pyEntry, "startTime"));
	xbmcEntry.endTime = PyInt_AsLong(PyDict_GetItemString(pyEntry, "endTime"));
	xbmcEntry.bStartAnyTime = PyBool_AsBool(PyDict_GetItemString(pyEntry, "startAnyTime"));
	xbmcEntry.bEndAnyTime = PyBool_AsBool(PyDict_GetItemString(pyEntry, "endAnyTime"));
	xbmcEntry.state = (PVR_TIMER_STATE) PyInt_AsLong(PyDict_GetItemString(pyEntry, "state"));
	xbmcEntry.iTimerType = PyInt_AsLong(PyDict_GetItemString(pyEntry, "timerType"));
	strcpy(xbmcEntry.strTitle, PyString_AsString(PyDict_GetItemString(pyEntry, "title")));
	strcpy(xbmcEntry.strEpgSearchString, PyString_AsString(PyDict_GetItemString(pyEntry, "epgSearchString")));
	xbmcEntry.bFullTextEpgSearch = PyBool_AsBool(PyDict_GetItemString(pyEntry, "fullTextEpgSearch"));
	strcpy(xbmcEntry.strDirectory, PyString_AsString(PyDict_GetItemString(pyEntry, "directory")));
	strcpy(xbmcEntry.strSummary, PyString_AsString(PyDict_GetItemString(pyEntry, "summary")));
	xbmcEntry.iPriority = PyInt_AsLong(PyDict_GetItemString(pyEntry, "priority"));
	xbmcEntry.iLifetime = PyInt_AsLong(PyDict_GetItemString(pyEntry, "lifetime"));
	xbmcEntry.iMaxRecordings = PyInt_AsLong(PyDict_GetItemString(pyEntry, "maxRecordings"));
	xbmcEntry.iRecordingGroup = PyInt_AsLong(PyDict_GetItemString(pyEntry, "recordingGroup"));
	xbmcEntry.firstDay = PyInt_AsLong(PyDict_GetItemString(pyEntry, "firstDay"));
	xbmcEntry.iWeekdays = PyInt_AsLong(PyDict_GetItemString(pyEntry, "weekdays"));
	xbmcEntry.iPreventDuplicateEpisodes = PyInt_AsLong(PyDict_GetItemString(pyEntry, "preventDuplicateEpisodes"));
	xbmcEntry.iEpgUid = PyInt_AsLong(PyDict_GetItemString(pyEntry, "epgUid"));
	xbmcEntry.iMarginStart = PyInt_AsLong(PyDict_GetItemString(pyEntry, "marginStart"));
	xbmcEntry.iMarginEnd = PyInt_AsLong(PyDict_GetItemString(pyEntry, "marginEnd"));
	xbmcEntry.iGenreType = PyInt_AsLong(PyDict_GetItemString(pyEntry, "genreType"));
	xbmcEntry.iGenreSubType = PyInt_AsLong(PyDict_GetItemString(pyEntry, "genreSubType"));
	
	PVR->TransferTimerEntry(addon_handle, &xbmcEntry);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* bridge_PVR_TransferRecordingEntry(PyObject* self, PyObject* args)
{
	PyObject* pyEntry = PyTuple_GetItem(args, 0);
	
	PVR_RECORDING xbmcEntry;
	memset(&xbmcEntry, 0, sizeof(PVR_RECORDING));
	
	strcpy(xbmcEntry.strRecordingId, PyString_AsString(PyDict_GetItemString(pyEntry, "recordingId")));
	strcpy(xbmcEntry.strTitle, PyString_AsString(PyDict_GetItemString(pyEntry, "title")));
	strcpy(xbmcEntry.strEpisodeName, PyString_AsString(PyDict_GetItemString(pyEntry, "episodeName")));
	xbmcEntry.iSeriesNumber = PyInt_AsLong(PyDict_GetItemString(pyEntry, "seriesNumber"));
	xbmcEntry.iEpisodeNumber = PyInt_AsLong(PyDict_GetItemString(pyEntry, "episodeNumber"));
	xbmcEntry.iYear = PyInt_AsLong(PyDict_GetItemString(pyEntry, "year"));
	strcpy(xbmcEntry.strStreamURL, PyString_AsString(PyDict_GetItemString(pyEntry, "streamURL")));
	strcpy(xbmcEntry.strDirectory, PyString_AsString(PyDict_GetItemString(pyEntry, "directory")));
	strcpy(xbmcEntry.strPlotOutline, PyString_AsString(PyDict_GetItemString(pyEntry, "plotOutline")));
	strcpy(xbmcEntry.strPlot, PyString_AsString(PyDict_GetItemString(pyEntry, "plot")));
	strcpy(xbmcEntry.strChannelName, PyString_AsString(PyDict_GetItemString(pyEntry, "channelName")));
	strcpy(xbmcEntry.strIconPath, PyString_AsString(PyDict_GetItemString(pyEntry, "iconPath")));
	strcpy(xbmcEntry.strThumbnailPath, PyString_AsString(PyDict_GetItemString(pyEntry, "thumbnailPath")));
	strcpy(xbmcEntry.strFanartPath, PyString_AsString(PyDict_GetItemString(pyEntry, "fanartPath")));
	xbmcEntry.recordingTime = PyInt_AsLong(PyDict_GetItemString(pyEntry, "recordingTime"));
	xbmcEntry.iDuration = PyInt_AsLong(PyDict_GetItemString(pyEntry, "duration"));
	xbmcEntry.iPriority = PyInt_AsLong(PyDict_GetItemString(pyEntry, "priority"));
	xbmcEntry.iLifetime = PyInt_AsLong(PyDict_GetItemString(pyEntry, "lifetime"));
	xbmcEntry.iGenreType = PyInt_AsLong(PyDict_GetItemString(pyEntry, "genreType"));
	xbmcEntry.iGenreSubType = PyInt_AsLong(PyDict_GetItemString(pyEntry, "genreSubType"));
	xbmcEntry.iPlayCount = PyInt_AsLong(PyDict_GetItemString(pyEntry, "playCount"));
	xbmcEntry.iLastPlayedPosition = PyInt_AsLong(PyDict_GetItemString(pyEntry, "lastPlayedPosition"));
	xbmcEntry.bIsDeleted = PyBool_AsBool(PyDict_GetItemString(pyEntry, "isDeleted"));
	xbmcEntry.iEpgEventId = PyInt_AsLong(PyDict_GetItemString(pyEntry, "epgEventId"));
	xbmcEntry.iChannelUid = PyInt_AsLong(PyDict_GetItemString(pyEntry, "channelUid"));
	xbmcEntry.iChannelUid = PVR_CHANNEL_INVALID_UID;
	xbmcEntry.channelType = (PVR_RECORDING_CHANNEL_TYPE) PyInt_AsLong(PyDict_GetItemString(pyEntry, "channelType"));
	
	PVR->TransferRecordingEntry(addon_handle, &xbmcEntry);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* bridge_PVR_TransferEpgEntry(PyObject* self, PyObject* args)
{
	PyObject* pyEntry = PyTuple_GetItem(args, 0);
	
	EPG_TAG xbmcEntry;
	memset(&xbmcEntry, 0, sizeof(EPG_TAG));
	
	XBMC->Log(LOG_DEBUG, "%s - ABC", __FUNCTION__);
	
	xbmcEntry.iUniqueBroadcastId = PyInt_AsLong(PyDict_GetItemString(pyEntry, "uniqueBroadcastId"));
	xbmcEntry.strTitle = PyString_AsString(PyDict_GetItemString(pyEntry, "title"));
	xbmcEntry.iChannelNumber = PyInt_AsLong(PyDict_GetItemString(pyEntry, "channelNumber"));
	xbmcEntry.startTime = PyInt_AsLong(PyDict_GetItemString(pyEntry, "startTime"));
	xbmcEntry.endTime = PyInt_AsLong(PyDict_GetItemString(pyEntry, "endTime"));
	xbmcEntry.strPlotOutline = PyString_AsString(PyDict_GetItemString(pyEntry, "plotOutline"));
	xbmcEntry.strPlot = PyString_AsString(PyDict_GetItemString(pyEntry, "plot"));
	xbmcEntry.strOriginalTitle = PyString_AsString(PyDict_GetItemString(pyEntry, "originalTitle"));
	xbmcEntry.strCast = PyString_AsString(PyDict_GetItemString(pyEntry, "cast"));
	xbmcEntry.strDirector = PyString_AsString(PyDict_GetItemString(pyEntry, "director"));
	xbmcEntry.strWriter = PyString_AsString(PyDict_GetItemString(pyEntry, "writer"));
	xbmcEntry.iYear = PyInt_AsLong(PyDict_GetItemString(pyEntry, "year"));
	xbmcEntry.strIMDBNumber = PyString_AsString(PyDict_GetItemString(pyEntry, "IMDBNumber"));
	xbmcEntry.strIconPath = PyString_AsString(PyDict_GetItemString(pyEntry, "iconPath"));
	xbmcEntry.iGenreType = PyInt_AsLong(PyDict_GetItemString(pyEntry, "genreType"));
	xbmcEntry.iGenreSubType = PyInt_AsLong(PyDict_GetItemString(pyEntry, "genreSubType"));
	xbmcEntry.strGenreDescription = PyString_AsString(PyDict_GetItemString(pyEntry, "genreDescription"));
	xbmcEntry.firstAired = PyInt_AsLong(PyDict_GetItemString(pyEntry, "firstAired"));
	xbmcEntry.iParentalRating = PyInt_AsLong(PyDict_GetItemString(pyEntry, "parentalRating"));
	xbmcEntry.iStarRating = PyInt_AsLong(PyDict_GetItemString(pyEntry, "starRating"));
	xbmcEntry.bNotify = PyBool_AsBool(PyDict_GetItemString(pyEntry, "notify"));
	xbmcEntry.iSeriesNumber = PyInt_AsLong(PyDict_GetItemString(pyEntry, "seriesNumber"));
	xbmcEntry.iEpisodeNumber = PyInt_AsLong(PyDict_GetItemString(pyEntry, "episodeNumber"));
	xbmcEntry.iEpisodePartNumber = PyInt_AsLong(PyDict_GetItemString(pyEntry, "episodePartNumber"));
	xbmcEntry.strEpisodeName = PyString_AsString(PyDict_GetItemString(pyEntry, "episodeName"));
	xbmcEntry.iFlags = PyInt_AsLong(PyDict_GetItemString(pyEntry, "flags"));
	
	PVR->TransferEpgEntry(addon_handle, &xbmcEntry);
	
	XBMC->Log(LOG_DEBUG, "%s - DEF", __FUNCTION__);
	
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef bridgeMethods[] = {
	{"XBMC_Log", bridge_XBMC_Log, METH_VARARGS, ""},
	{"PVR_TransferChannelEntry", bridge_PVR_TransferChannelEntry, METH_VARARGS, ""},
	{"PVR_TransferChannelGroup", bridge_PVR_TransferChannelGroup, METH_VARARGS, ""},
	{"PVR_TransferChannelGroupMember", bridge_PVR_TransferChannelGroupMember, METH_VARARGS, ""},
	{"PVR_TransferTimerEntry", bridge_PVR_TransferTimerEntry, METH_VARARGS, ""},
	{"PVR_TransferRecordingEntry", bridge_PVR_TransferRecordingEntry, METH_VARARGS, ""},
	{"PVR_TransferEpgEntry", bridge_PVR_TransferEpgEntry, METH_VARARGS, ""},
	{NULL, NULL, 0, NULL}
};

// BEGIN C->PYTHON HELPER FUNCTIONS

const char* pyCallString(PyObject* obj, const char* func, PyObject* args) {
	PYTHON_LOCK();
	
	PyObject* pyFunc = PyObject_GetAttrString(obj, func);
	PyObject* pyArgs = args;
	if (args == NULL) {
		pyArgs = PyTuple_New(0);
	}
	PyObject* pyReturnValue = PyObject_CallObject(pyFunc, pyArgs);
	if (PyErr_Occurred() != NULL) { PyErr_Print(); PyErr_Clear(); PYTHON_UNLOCK(); return ""; }
	char* returnValue = PyString_AsString(pyReturnValue);
	Py_DECREF(pyReturnValue);
	if (args == NULL) {
		Py_DECREF(pyArgs);
	}
	Py_DECREF(pyFunc);
	
	PYTHON_UNLOCK();
	
	return returnValue;
}

PVR_ERROR pyCallPVRError(PyObject* obj, const char* func, PyObject* args) {
	PYTHON_LOCK();
	
	PyObject* pyFunc = PyObject_GetAttrString(pvrImpl, func);
	PyObject* pyArgs = args;
	if (args == NULL) {
		pyArgs = PyTuple_New(0);
	}
	PyObject* pyReturnValue = PyObject_CallObject(pyFunc, pyArgs);
	if (PyErr_Occurred() != NULL) { PyErr_Print(); PyErr_Clear(); PYTHON_UNLOCK(); return PVR_ERROR_FAILED; }
	long returnValue = PyInt_AsLong(pyReturnValue);
	Py_DECREF(pyReturnValue);
	if (args == NULL) {
		Py_DECREF(pyArgs);
	}
	Py_DECREF(pyFunc);
	
	PYTHON_UNLOCK();
	
	return ((PVR_ERROR) returnValue);
}

int pyCallInt(PyObject* obj, const char* func, PyObject* args) {
	PYTHON_LOCK();
	
	PyObject* pyFunc = PyObject_GetAttrString(pvrImpl, func);
	PyObject* pyArgs = args;
	if (args == NULL) {
		pyArgs = PyTuple_New(0);
	}
	PyObject* pyReturnValue = PyObject_CallObject(pyFunc, pyArgs);
	if (PyErr_Occurred() != NULL) { PyErr_Print(); PyErr_Clear(); PYTHON_UNLOCK(); return -1; }
	int returnValue = PyInt_AsLong(pyReturnValue);
	Py_DECREF(pyReturnValue);
	if (args == NULL) {
		Py_DECREF(pyArgs);
	}
	Py_DECREF(pyFunc);
	
	PYTHON_UNLOCK();
	
	return returnValue;
}

// END PYTHON<->C FUNCTIONS

//void ADDON_ReadSettings(void)
//{
	//STUB
//}

ADDON_STATUS ADDON_Create(void* hdl, void* props)
{
	if (!hdl || !props)
		return ADDON_STATUS_UNKNOWN;
	
	PVR_PROPERTIES* pvrprops = (PVR_PROPERTIES*)props;
	
	XBMC = new CHelper_libXBMC_addon;
	if (!XBMC->RegisterMe(hdl))
	{
		SAFE_DELETE(XBMC);
		return ADDON_STATUS_PERMANENT_FAILURE;
	}
	
	PVR = new CHelper_libXBMC_pvr;
	if (!PVR->RegisterMe(hdl))
	{
		SAFE_DELETE(PVR);
		SAFE_DELETE(XBMC);
		return ADDON_STATUS_PERMANENT_FAILURE;
	}
	
	XBMC->Log(LOG_DEBUG, "%s - Creating the PVR demo add-on", __FUNCTION__);
	
	PyEval_AcquireLock();
	pyState = Py_NewInterpreter();
	PyThreadState_Swap(pyState);
	
	Py_InitModule("bridge", bridgeMethods);
	
	// Setup the path
	PyObject* sysPath = PySys_GetObject((char*) "path");
	PyObject* pyClientPath = PyString_FromString(pvrprops->strClientPath);
	PyList_Append(sysPath, pyClientPath);
	Py_DECREF(pyClientPath);
	XBMC->Log(LOG_DEBUG, "%s - Added '%s' to sys.path", __FUNCTION__, pvrprops->strClientPath);
	
	// Import the module
	PyObject* pyName = PyString_FromString("pvrimpl");
	PyObject* pyModule = PyImport_Import(pyName);
	Py_DECREF(pyName);
	
	if (pyModule == NULL) {
		XBMC->Log(LOG_DEBUG, "%s - Failed to import Python PVR implementation module 'pvrimpl'", __FUNCTION__);
		SAFE_DELETE(PVR);
		SAFE_DELETE(XBMC);
		return ADDON_STATUS_PERMANENT_FAILURE;
	}
	
	XBMC->Log(LOG_DEBUG, "%s - Handing over to Python", __FUNCTION__);
	
	// Get an instance
	PyObject* pyFunc = PyObject_GetAttrString(pyModule, "getInstance");
	PyObject* pyArgs = PyTuple_New(0);
	pvrImpl = PyObject_CallObject(pyFunc, pyArgs);
	if (PyErr_Occurred() != NULL) { PyErr_Print(); PyErr_Clear(); PYTHON_UNLOCK(); return ADDON_STATUS_PERMANENT_FAILURE; }
	Py_DECREF(pyArgs);
	Py_DECREF(pyFunc);
	
	// Call the ADDON_Create function
	pyFunc = PyObject_GetAttrString(pvrImpl, "ADDON_Create");
	pyArgs = Py_BuildValue("({s:s, s:s, s:i})", "userPath", pvrprops->strUserPath, "clientPath", pvrprops->strClientPath, "epgMaxDays", pvrprops->iEpgMaxDays);
	PyObject* pyReturnValue = PyObject_CallObject(pyFunc, pyArgs);
	if (PyErr_Occurred() != NULL) { PyErr_Print(); PyErr_Clear(); PYTHON_UNLOCK(); return ADDON_STATUS_PERMANENT_FAILURE; }
	long returnValue = PyInt_AsLong(pyReturnValue);
	Py_DECREF(pyReturnValue);
	Py_DECREF(pyArgs);
	Py_DECREF(pyFunc);
	
	PyThreadState_Swap(NULL);
	PyEval_ReleaseLock();
	
	// Process the return value
	// Enums take on their integer indexes as value
	return ((ADDON_STATUS) returnValue);
}

ADDON_STATUS ADDON_GetStatus()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	return (ADDON_STATUS)6;
	return m_CurStatus;
}

void ADDON_Destroy()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	PYTHON_LOCK();
	Py_EndInterpreter(pyState);
	PYTHON_UNLOCK();
	return;
	delete m_data;
	m_bCreated = false;
	m_CurStatus = ADDON_STATUS_UNKNOWN;
}

bool ADDON_HasSettings()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	return true;
}

unsigned int ADDON_GetSettings(ADDON_StructSetting ***sSet)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	return 0;
}

ADDON_STATUS ADDON_SetSetting(const char *settingName, const void *settingValue)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	return ADDON_STATUS_OK;
}

void ADDON_Stop()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
}

void ADDON_FreeSettings()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
}

/***********************************************************
 * PVR Client AddOn specific public library functions
 ***********************************************************/

PVR_ERROR GetAddonCapabilities(PVR_ADDON_CAPABILITIES* pCapabilities)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	
	PYTHON_LOCK();
	
	PyObject* pyFunc = PyObject_GetAttrString(pvrImpl, "GetAddonCapabilities");
	PyObject* pyArgs = PyTuple_New(0);
	PyObject* pyReturnValue = PyObject_CallObject(pyFunc, pyArgs);
	if (PyErr_Occurred() != NULL) { PyErr_Print(); PyErr_Clear(); PYTHON_UNLOCK(); return PVR_ERROR_FAILED; }
	
	PyObject* pyCapabilities = PyTuple_GetItem(pyReturnValue, 1);
	pCapabilities->bSupportsEPG = (PyDict_GetItemString(pyCapabilities, "supportsEPG") == Py_True);
	pCapabilities->bSupportsTV = (PyDict_GetItemString(pyCapabilities, "supportsTV") == Py_True);
	pCapabilities->bSupportsRadio = (PyDict_GetItemString(pyCapabilities, "supportsRadio") == Py_True);
	pCapabilities->bSupportsRecordings = (PyDict_GetItemString(pyCapabilities, "supportsRecordings") == Py_True);
	pCapabilities->bSupportsRecordingsUndelete = (PyDict_GetItemString(pyCapabilities, "supportsRecordingsUndelete") == Py_True);
	pCapabilities->bSupportsTimers = (PyDict_GetItemString(pyCapabilities, "supportsTimers") == Py_True);
	pCapabilities->bSupportsChannelGroups = (PyDict_GetItemString(pyCapabilities, "supportsChannelGroups") == Py_True);
	pCapabilities->bSupportsChannelScan = (PyDict_GetItemString(pyCapabilities, "supportsChannelScan") == Py_True);
	pCapabilities->bSupportsChannelSettings = (PyDict_GetItemString(pyCapabilities, "supportsChannelSettings") == Py_True);
	pCapabilities->bHandlesInputStream = (PyDict_GetItemString(pyCapabilities, "handlesInputStream") == Py_True);
	pCapabilities->bHandlesDemuxing = (PyDict_GetItemString(pyCapabilities, "handlesDemuxing") == Py_True);
	pCapabilities->bSupportsRecordingPlayCount = (PyDict_GetItemString(pyCapabilities, "supportsRecordingPlayCount") == Py_True);
	pCapabilities->bSupportsLastPlayedPosition = (PyDict_GetItemString(pyCapabilities, "supportsLastPlayedPosition") == Py_True);
	pCapabilities->bSupportsRecordingEdl = (PyDict_GetItemString(pyCapabilities, "supportsRecordingEdl") == Py_True);
	
	PyObject* pyErrorCode = PyTuple_GetItem(pyReturnValue, 0);
	long errorCode = PyInt_AsLong(pyErrorCode);
	Py_DECREF(pyReturnValue);
	Py_DECREF(pyArgs);
	Py_DECREF(pyFunc);
	
	PYTHON_UNLOCK();
	
	return ((PVR_ERROR) errorCode);
}

const char *GetBackendName(void)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	return pyCallString(pvrImpl, "GetBackendName", NULL);
}

const char *GetConnectionString(void)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	return pyCallString(pvrImpl, "GetConnectionString", NULL);
}

const char *GetBackendVersion(void)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	return pyCallString(pvrImpl, "GetBackendVersion", NULL);
}

const char *GetBackendHostname(void)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	return pyCallString(pvrImpl, "GetBackendHostname", NULL);
}

PVR_ERROR GetChannels(ADDON_HANDLE handle, bool bRadio)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	
	addon_handle = handle;
	return pyCallPVRError(pvrImpl, "GetChannels", Py_BuildValue("(b)", bRadio));
}

PVR_ERROR GetChannelGroups(ADDON_HANDLE handle, bool bRadio)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	
	addon_handle = handle;
	return pyCallPVRError(pvrImpl, "GetChannelGroups", Py_BuildValue("(b)", bRadio));
}

PVR_ERROR GetChannelGroupMembers(ADDON_HANDLE handle, const PVR_CHANNEL_GROUP &group)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	
	addon_handle = handle;
	return pyCallPVRError(pvrImpl, "GetChannelGroupMembers", Py_BuildValue("(s)", group.strGroupName));
}

PVR_ERROR GetTimerTypes(PVR_TIMER_TYPE types[], int *size)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	
	/* TODO: Implement this to get support for the timer features introduced with PVR API 1.9.7 */
	return PVR_ERROR_NOT_IMPLEMENTED;
}

PVR_ERROR GetTimers(ADDON_HANDLE handle)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	
	addon_handle = handle;
	/* TODO: Change implementation to get support for the timer features introduced with PVR API 1.9.7 */
	return pyCallPVRError(pvrImpl, "GetTimers", NULL);
}

PVR_ERROR GetRecordings(ADDON_HANDLE handle, bool deleted)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	
	addon_handle = handle;
	return pyCallPVRError(pvrImpl, "GetRecordings", Py_BuildValue("(b)", deleted));
}

PVR_ERROR GetDriveSpace(long long *iTotal, long long *iUsed)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	
	PYTHON_LOCK();
	
	PyObject* pyFunc = PyObject_GetAttrString(pvrImpl, "GetDriveSpace");
	PyObject* pyArgs = PyTuple_New(0);
	PyObject* pyReturnValue = PyObject_CallObject(pyFunc, pyArgs);
	if (PyErr_Occurred() != NULL) { PyErr_Print(); PyErr_Clear(); PYTHON_UNLOCK(); return PVR_ERROR_FAILED; }
	int errorCode = PyInt_AsLong(PyTuple_GetItem(pyReturnValue, 0));
	*iTotal = PyLong_AsLongLong(PyTuple_GetItem(pyReturnValue, 1));
	*iUsed = PyLong_AsLongLong(PyTuple_GetItem(pyReturnValue, 2));
	Py_DECREF(pyReturnValue);
	Py_DECREF(pyArgs);
	Py_DECREF(pyFunc);
	
	PYTHON_UNLOCK();
	
	return ((PVR_ERROR) errorCode);
}

int GetChannelsAmount(void)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	return pyCallInt(pvrImpl, "GetChannelsAmount", NULL);
}

int GetTimersAmount(void)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	return pyCallInt(pvrImpl, "GetTimersAmount", NULL);
}

int GetRecordingsAmount(bool deleted)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	return pyCallInt(pvrImpl, "GetRecordingsAmount", Py_BuildValue("(b)", deleted));
}

PVR_ERROR GetEPGForChannel(ADDON_HANDLE handle, const PVR_CHANNEL &channel, time_t iStart, time_t iEnd)
{
	//XBMC->Log(LOG_DEBUG, "%s - Called", __FUNCTION__);
	
	addon_handle = handle;
	return pyCallPVRError(pvrImpl, "GetEPGForChannel", Py_BuildValue("(i, i, i)", channel.iUniqueId, iStart, iEnd));
}

void OnSystemSleep()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
}

void OnSystemWake()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
}

void OnPowerSavingActivated()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
}

void OnPowerSavingDeactivated()
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
}

const char* GetPVRAPIVersion(void)
{
	static const char *strApiVersion = XBMC_PVR_API_VERSION;
	return strApiVersion;
}

const char* GetMininumPVRAPIVersion(void)
{
	static const char *strMinApiVersion = XBMC_PVR_MIN_API_VERSION;
	return strMinApiVersion;
}

const char* GetGUIAPIVersion(void)
{
	return ""; // GUI API not used
}

const char* GetMininumGUIAPIVersion(void)
{
	return ""; // GUI API not used
}

bool OpenLiveStream(const PVR_CHANNEL &channel)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	return false;
	
	if (m_data)
	{
		CloseLiveStream();
		
		if (m_data->GetChannel(channel, m_currentChannel))
		{
			m_bIsPlaying = true;
			return true;
		}
	}
	
	return false;
}

void CloseLiveStream(void)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	
	m_bIsPlaying = false;
}

bool SwitchChannel(const PVR_CHANNEL &channel)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	
	CloseLiveStream();
	
	return OpenLiveStream(channel);
}

PVR_ERROR GetStreamProperties(PVR_STREAM_PROPERTIES* pProperties)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	return PVR_ERROR_NOT_IMPLEMENTED;
}

int GetChannelGroupsAmount(void)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	return -1;
	
	if (m_data)
		return m_data->GetChannelGroupsAmount();
	
	return -1;
}

PVR_ERROR SignalStatus(PVR_SIGNAL_STATUS &signalStatus)
{
	XBMC->Log(LOG_DEBUG, "%s - NYI", __FUNCTION__);
	return PVR_ERROR_NOT_IMPLEMENTED;
	
	snprintf(signalStatus.strAdapterName, sizeof(signalStatus.strAdapterName), "pvr demo adapter 1");
	snprintf(signalStatus.strAdapterStatus, sizeof(signalStatus.strAdapterStatus), "OK");
	
	return PVR_ERROR_NO_ERROR;
}

/** UNUSED API FUNCTIONS */
PVR_ERROR OpenDialogChannelScan(void) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR CallMenuHook(const PVR_MENUHOOK &menuhook, const PVR_MENUHOOK_DATA &item) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR DeleteChannel(const PVR_CHANNEL &channel) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR RenameChannel(const PVR_CHANNEL &channel) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR MoveChannel(const PVR_CHANNEL &channel) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR OpenDialogChannelSettings(const PVR_CHANNEL &channel) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR OpenDialogChannelAdd(const PVR_CHANNEL &channel) { return PVR_ERROR_NOT_IMPLEMENTED; }
bool OpenRecordedStream(const PVR_RECORDING &recording) { return false; }
void CloseRecordedStream(void) {}
int ReadRecordedStream(unsigned char *pBuffer, unsigned int iBufferSize) { return 0; }
long long SeekRecordedStream(long long iPosition, int iWhence /* = SEEK_SET */) { return 0; }
long long PositionRecordedStream(void) { return -1; }
long long LengthRecordedStream(void) { return 0; }
void DemuxReset(void) {}
void DemuxFlush(void) {}
int ReadLiveStream(unsigned char *pBuffer, unsigned int iBufferSize) { return 0; }
long long SeekLiveStream(long long iPosition, int iWhence /* = SEEK_SET */) { return -1; }
long long PositionLiveStream(void) { return -1; }
long long LengthLiveStream(void) { return -1; }
const char * GetLiveStreamURL(const PVR_CHANNEL &channel) { return ""; }
PVR_ERROR DeleteRecording(const PVR_RECORDING &recording) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR RenameRecording(const PVR_RECORDING &recording) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR SetRecordingPlayCount(const PVR_RECORDING &recording, int count) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR SetRecordingLastPlayedPosition(const PVR_RECORDING &recording, int lastplayedposition) { return PVR_ERROR_NOT_IMPLEMENTED; }
int GetRecordingLastPlayedPosition(const PVR_RECORDING &recording) { return -1; }
PVR_ERROR GetRecordingEdl(const PVR_RECORDING&, PVR_EDL_ENTRY[], int*) { return PVR_ERROR_NOT_IMPLEMENTED; };
PVR_ERROR AddTimer(const PVR_TIMER &timer) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR DeleteTimer(const PVR_TIMER &timer, bool bForceDelete) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR UpdateTimer(const PVR_TIMER &timer) { return PVR_ERROR_NOT_IMPLEMENTED; }
void DemuxAbort(void) {}
DemuxPacket* DemuxRead(void) { return NULL; }
unsigned int GetChannelSwitchDelay(void) { return 0; }
void PauseStream(bool bPaused) {}
bool CanPauseStream(void) { return false; }
bool CanSeekStream(void) { return false; }
bool SeekTime(double,bool,double*) { return false; }
void SetSpeed(int) {};
bool IsTimeshifting(void) { return false; }
bool IsRealTimeStream(void) { return true; }
time_t GetPlayingTime() { return 0; }
time_t GetBufferTimeStart() { return 0; }
time_t GetBufferTimeEnd() { return 0; }
PVR_ERROR UndeleteRecording(const PVR_RECORDING& recording) { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR DeleteAllRecordingsFromTrash() { return PVR_ERROR_NOT_IMPLEMENTED; }
PVR_ERROR SetEPGTimeFrame(int) { return PVR_ERROR_NOT_IMPLEMENTED; }
}
