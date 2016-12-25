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

from libpvr import *

import datetime
import json
import re
import traceback
import urllib, urllib2
import urlparse

def getInstance():
	return CCTVPVRImpl()

class CCTVPVRImpl(BasePVR):
	def loadData(self, props):
		# Channels
		self.channels = [PVRChannel(
			uniqueId = 1,
			isRadio = False,
			channelName = 'CCTV English',
			#streamURL = '' # Defer loading URL until OpenLiveStream
			streamURL = self.OpenLiveStream(None)[1]
		)]
	
	def GetAddonCapabilities(self):
		return PVR_ERROR.NO_ERROR, {
			'supportsEPG': True,
			'supportsTV': True,
			'supportsRadio': False,
			'supportsRecordings': False,
			'supportsRecordingsUndelete': False,
			'supportsTimers': False,
			'supportsChannelGroups': False
		}
	
	def GetBackendName(self):
		return 'python pvr cctv-en backend'
	
	def GetConnectionString(self):
		return 'connected'
	
	def GetBackendVersion(self):
		return '0.0.2.1'
	
	def GetBackendHostname(self):
		return ''
	
	def GetChannels(self, radio):
		for channel in self.channels:
			if channel.isRadio == radio:
				yield channel
		
		raise PVRListDone(PVR_ERROR.NO_ERROR)
	
	def GetDriveSpace(self):
		return PVR_ERROR.NO_ERROR, 0, 0
	
	def GetChannelsAmount(self):
		return len(self.channels)
	
	def GetEPGForChannel(self, channelId, cstartTime, cendTime):
		startTime = datetime.datetime.fromtimestamp(cstartTime)
		endTime = datetime.datetime.fromtimestamp(cendTime)
		
		def firstDTAfter(weekday, dtTime, dtAfter):
			dt = datetime.datetime.combine(dtAfter.date(), dtTime.timetz())
			dt += datetime.timedelta(days=((weekday - dt.isoweekday()) % 7))
			if dt < dtAfter:
				dt += datetime.timedelta(days=7)
			return dt
		
		def lastDTBefore(weekday, dtTime, dtBefore):
			dt = datetime.datetime.combine(dtBefore.date(), dtTime.timetz())
			dt += datetime.timedelta(days=((weekday - dt.isoweekday()) % 7))
			if dt > dtBefore:
				dt -= datetime.timedelta(days=7)
			return dt
		
		# The internal mktime() expects EPG times in local time, but CCTV provides them in CST (+0800)
		timeInChina = datetime.datetime.utcnow() + datetime.timedelta(hours=8) #UTC +0800
		localTZ = datetime.datetime.now() - datetime.datetime.utcnow() #UTC + how much?
		tzOffset = localTZ - datetime.timedelta(hours=8) #how much ahead of China
		def chinaToLocal(weekday, dtTime):
			dt = datetime.datetime.combine(timeInChina, dtTime.timetz())
			dt += datetime.timedelta(days=((weekday - dt.isoweekday()) % 7))
			dt += tzOffset
			return dt.isoweekday(), dt
		
		try:
			handle = urllib2.urlopen('http://p2.img.cctvpic.com/photoAlbum/templet/common/DEPA1394789726596678/new_jiemudan.js')
			data = handle.read().decode('utf-8')
			
			programmes = []
			
			# Store the data
			matches = re.findall(r'new schedule_array\("(.*?)", "(.*?)", "(.*?)", "(.*?)"\)', data)
			for match in matches:
				#0 = start weekday/start time, 1 = end weekday/end time, 2 = name, 3 = next start time, 4 = next end time
				startTimeChina = (int(match[0]), datetime.datetime.strptime(match[1], '%H%M'))
				programmes.append([chinaToLocal(*startTimeChina), None, match[2], None, None])
			
			# Fill in the end times
			for i in xrange(0, len(programmes)):
				nextProgramme = programmes[(i + 1) % len(programmes)]
				# End time is next programme's start time
				programmes[i][1] = nextProgramme[0]
			
			# Calculate next start/end times
			for i in xrange(0, len(programmes)):
				# End time is first end time after startTime
				programmes[i][4] = firstDTAfter(programmes[i][1][0], programmes[i][1][1], startTime)
				# Start time is corresponding start time
				programmes[i][3] = lastDTBefore(programmes[i][0][0], programmes[i][0][1], programmes[i][4])
				
				if programmes[i][3] <= endTime:
					yield EPGTag(
						uniqueBroadcastId = i + 1,
						title = programmes[i][2],
						channelNumber = 1,
						startTime = programmes[i][3],
						endTime = programmes[i][4],
						genreType = 32
					)
					
		except:
			traceback.print_exc()
			raise PVRListDone(PVR_ERROR.SERVER_ERROR)
		
		raise PVRListDone(PVR_ERROR.NO_ERROR)
	
	def OpenLiveStream(self, channelId):
		try:
			handle = urllib2.urlopen('http://vdn.live.cntv.cn/api2/live.do?channel=pa://cctv_p2p_hdcctv9&client=flash')
			
			data = json.load(handle)
			url = data['hls_url']['hls1']
			
			auth = urlparse.parse_qs(urlparse.urlparse(url)[4])['AUTH'][0]
			fullUrl = url + '|' + urllib.urlencode( { 'Cookie' : 'AUTH=' + auth } )
			
			return True, fullUrl
		except:
			traceback.print_exc()
		
		return False
	
	def CloseLiveStream(self):
		# This will only be called if no file is currently playing
		pass
