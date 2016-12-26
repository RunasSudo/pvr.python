# -*- coding: utf-8 -*-
#   pvr.python - A PVR client for Kodi using Python
#   Copyright © 2016 RunasSudo (Yingtong Li)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bridge

import time

# Classes

class PVRChannel:
	INVALID_UID = -1
	
	def __init__(self,
	             uniqueId,
	             isRadio,
	             channelNumber = 0,
	             subChannelNumber = 0,
	             channelName = '',
	             inputFormat = '',
	             streamURL = '',
	             encryptionSystem = 0,
	             iconPath = '',
	             isHidden = False
	):
		for k, v in locals().items():
			setattr(self, k, v)

class PVRChannelGroup:
	def __init__(self,
	             groupName,
	             isRadio,
	             position = 0,
	             members = [] # not part of PVR_CHANNEL_GROUP
	):
		for k, v in locals().items():
			setattr(self, k, v)

class PVRChannelGroupMember:
	def __init__(self,
	             groupName,
	             channelUniqueId,
	             channelNumber = 0
	):
		for k, v in locals().items():
			setattr(self, k, v)

def _datetimeToC(dt):
	if dt is None:
		return 0
	return time.mktime(dt.timetuple())

class EPGTag:
	INVALID_UID = 0
	
	def __init__(self,
	             uniqueBroadcastId,
	             title,
	             channelNumber,
	             startTime, #datetime.datetime
	             endTime, #datetime.datetime
	             plotOutline = '',
	             plot = '',
	             originalTitle = '',
	             cast = '',
	             director = '',
	             writer = '',
	             year = 0,
	             IMDBNumber = '',
	             iconPath = '',
	             genreType = 0,
	             genreSubType = 0,
	             genreDescription = '',
	             firstAired = None, #datetime.datetime
	             parentalRating = 0,
	             starRating = 0,
	             notify = False,
	             seriesNumber = 0,
	             episodeNumber = 0,
	             episodePartNumber = 0,
	             episodeName = '',
	             flags = 0
	):
		for k, v in locals().items():
			setattr(self, k, v)
	
	@property
	def _cstartTime(self):
		return _datetimeToC(self.startTime)
	
	@property
	def _cendTime(self):
		return _datetimeToC(self.endTime)
	
	@property
	def _cfirstAired(self):
		return _datetimeToC(self.firstAired)

class PVRTimer:
	NO_PARENT = 0
	TYPE_NONE = 0
	
	# y u no '*' in arguments list, python 2? :/
	def __init__(self,
	             clientIndex,
	             state,
	             timerType, #try PVRTimer.TYPE_NONE
	             title,
	             parentClientIndex = NO_PARENT,
	             clientChannelUid = PVRChannel.INVALID_UID,
	             startTime = None, #datetime.datetime
	             endTime = None, #datetime.datetime
	             startAnyTime = False,
	             endAnyTime = False,
	             epgSearchString = '',
	             fullTextEpgSearch = False,
	             directory = '',
	             summary = '',
	             priority = 0,
	             lifetime = 0,
	             maxRecordings = 0,
	             recordingGroup = 0,
	             firstDay = None, #datetime.datetime
	             weekdays = 0,
	             preventDuplicateEpisodes = 0,
	             epgUid = EPGTag.INVALID_UID,
	             marginStart = 0,
	             marginEnd = 0,
	             genreType = 0,
	             genreSubType = 0
	):
		for k, v in locals().items():
			setattr(self, k, v)
	
	@property
	def _cstartTime(self):
		return _datetimeToC(self.startTime)
	
	@property
	def _cendTime(self):
		return _datetimeToC(self.endTime)
	
	@property
	def _cfirstDay(self):
		return _datetimeToC(self.firstDay)

class PVRRecording:
	CHANNEL_TYPE_UNKNOWN = 0
	CHANNEL_TYPE_TV = 1
	CHANNEL_TYPE_RADIO = 2
	
	def __init__(self,
	             recordingId,
	             title,
	             streamURL,
	             episodeName = '',
	             seriesNumber = -1,
	             episodeNumber = -1,
	             year = 0,
	             directory = '',
	             plotOutline = '',
	             plot = '',
	             channelName = '',
	             iconPath = '',
	             thumbnailPath = '',
	             fanartPath = '',
	             recordingTime = None, #datetime.datetime
	             duration = 0,
	             priority = 0,
	             lifetime = 0,
	             genreType = 0,
	             genreSubType = 0,
	             playCount = 0,
	             lastPlayedPosition = 0,
	             isDeleted = False,
	             epgEventId = EPGTag.INVALID_UID,
	             channelUid = PVRChannel.INVALID_UID,
	             channelType = CHANNEL_TYPE_UNKNOWN
	):
		for k, v in locals().items():
			setattr(self, k, v)
	
	@property
	def _crecordingTime(self):
		return _datetimeToC(self.recordingTime)

# raised when the PVR_ERROR result is ready
# y u no 'return' from generators, python 2? :/
class PVRListDone(Exception):
	def __init__(self, value):
		self.value = value

def force_generator(func):
	def wrapper(*args, **kwargs):
		# y u no 'yield from', python 2? :/
		for item in func(*args, **kwargs):
			yield item
	return wrapper

class BasePVR:
	def ADDON_Create(self, props):
		self.loadData(props)
		
		return ADDON_STATUS.OK
	
	def GetAddonCapabilities(self):
		bridge.XBMC_Log('GetAddonCapabilities - NYI')
		return PVR_ERROR.NOT_IMPLEMENTED
	
	def GetBackendName(self):
		bridge.XBMC_Log('GetBackendName - NYI')
		return 'python pvr base backend'
	
	def GetConnectionString(self):
		bridge.XBMC_Log('GetConnectionString - NYI')
		return 'connected'
	
	def GetBackendVersion(self):
		bridge.XBMC_Log('GetBackendVersion - NYI')
		return '0.0.2.1'
	
	def GetBackendHostname(self):
		bridge.XBMC_Log('GetBackendHostname - NYI')
		return ''
	
	@force_generator
	def GetChannels(self, radio):
		bridge.XBMC_Log('GetChannels - NYI')
		raise PVRListDone(PVR_ERROR.NOT_IMPLEMENTED)
	
	def _cGetChannels(self, radio):
		try:
			for item in self.GetChannels(radio):
				bridge.PVR_TransferChannelEntry(item)
		except PVRListDone as ex:
			return ex.value
		
		return PVR_ERROR.UNKNOWN # This should never happen.
	
	@force_generator
	def GetChannelGroups(self, radio):
		bridge.XBMC_Log('GetChannelGroups - NYI')
		raise PVRListDone(PVR_ERROR.NOT_IMPLEMENTED)
	
	def _cGetChannelGroups(self, radio):
		try:
			for item in self.GetChannelGroups(radio):
				bridge.PVR_TransferChannelGroup(item)
		except PVRListDone as ex:
			return ex.value
	
	@force_generator
	def GetChannelGroupMembers(self, groupName):
		bridge.XBMC_Log('GetChannelGroupMembers - NYI')
		raise PVRListDone(PVR_ERROR.NOT_IMPLEMENTED)
	
	def _cGetChannelGroupMembers(self, groupName):
		try:
			for item in self.GetChannelGroupMembers(groupName):
				bridge.PVR_TransferChannelGroupMember(item)
		except PVRListDone as ex:
			return ex.value
	
	@force_generator
	def GetTimers(self):
		bridge.XBMC_Log('GetTimers - NYI')
		raise PVRListDone(PVR_ERROR.NOT_IMPLEMENTED)
	
	def _cGetTimers(self):
		try:
			for item in self.GetTimers():
				bridge.PVR_TransferTimerEntry(item)
		except PVRListDone as ex:
			return ex.value
	
	@force_generator
	def GetRecordings(self, deleted):
		bridge.XBMC_Log('GetRecordings - NYI')
		raise PVRListDone(PVR_ERROR.NOT_IMPLEMENTED)
	
	def _cGetRecordings(self, deleted):
		try:
			for item in self.GetRecordings(deleted):
				bridge.PVR_TransferRecordingEntry(item)
		except PVRListDone as ex:
			return ex.value
	
	def GetDriveSpace(self):
		bridge.XBMC_Log('GetDriveSpace - NYI')
		return PVR_ERROR.NOT_IMPLEMENTED, -1, -1
	
	def GetChannelsAmount(self):
		bridge.XBMC_Log('GetChannelsAmount - NYI')
		return -1
	
	def GetTimersAmount(self):
		bridge.XBMC_Log('GetTimersAmount - NYI')
		return -1
	
	def GetRecordingsAmount(self, deleted):
		bridge.XBMC_Log('GetRecordingsAmount - NYI')
		return -1
	
	@force_generator
	def GetEPGForChannel(self, channelId, cstartTime, cendTime):
		bridge.XBMC_Log('GetEPGForChannel - NYI')
		raise PVRListDone(PVR_ERROR.NOT_IMPLEMENTED)
	
	def _cGetEPGForChannel(self, channelId, cstartTime, cendTime):
		try:
			for item in self.GetEPGForChannel(channelId, cstartTime, cendTime):
				bridge.PVR_TransferEpgEntry(item)
		except PVRListDone as ex:
			return ex.value
	
	def OpenLiveStream(self, channelId):
		bridge.XBMC_Log('OpenLiveStream - NYI')
		return False
	
	def ReadLiveStream(self, bufferSize):
		bridge.XBMC_Log('ReadLiveStream - NYI')
		return -1, None
	
	def SeekLiveStream(self, position, whence):
		bridge.XBMC_Log('SeekLiveStream - NYI')
		return -1
	
	def PositionLiveStream(self):
		bridge.XBMC_Log('PositionLiveStream - NYI')
		return -1
	
	def LengthLiveStream(self):
		bridge.XBMC_Log('LengthLiveStream - NYI')
		return -1

# Enums

class ADDON_STATUS:
	OK = 0
	LOST_CONNECTION = 1
	NEED_RESTART = 2
	NEED_SETTINGS = 3
	UNKNOWN = 4
	NEED_SAVEDSETTINGS = 5
	PERMANENT_FAILURE = 6

class PVR_ERROR:
	NO_ERROR = 0
	UNKNOWN = -1
	NOT_IMPLEMENTED = -2
	SERVER_ERROR = -3
	SERVER_TIMEOUT = -4
	REJECTED = -5
	ALREADY_PRESENT = -6
	INVALID_PARAMETERS = -7
	RECORDING_RUNNING = -8
	FAILED = -9
