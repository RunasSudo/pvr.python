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
	def cstartTime(self):
		return _datetimeToC(self.startTime)
	
	@property
	def cendTime(self):
		return _datetimeToC(self.endTime)
	
	@property
	def cfirstAired(self):
		return _datetimeToC(self.firstAired)

class PVRTimer:
	NO_PARENT = 0
	TYPE_NONE = 0
	
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
	def cstartTime(self):
		return _datetimeToC(self.startTime)
	
	@property
	def cendTime(self):
		return _datetimeToC(self.endTime)
	
	@property
	def cfirstDay(self):
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
	def crecordingTime(self):
		return _datetimeToC(self.recordingTime)

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
