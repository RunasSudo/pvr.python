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

import json
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
			'supportsEPG': False,
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
		return '0.0.2.0'
	
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
