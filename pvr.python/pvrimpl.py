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

import libpvr
import bridge

import os
import xml.etree.ElementTree as ET

def getInstance():
	return DemoPVRImpl()

class DemoPVRImpl:
	def ADDON_Create(self, props):
		self.loadData(props)
		
		return libpvr.ADDON_STATUS.OK
	
	def loadData(self, props):
		tree = ET.parse(os.path.join(props['clientPath'], 'PVRDemoAddonSettings.xml'))
		root = tree.getroot()
		
		self.channels = []
		for channelTag in root.find('channels').findall('channel'):
			self.channels.append({
				'uniqueId': len(self.channels) + 1,
				'isRadio': channelTag.find('radio').text == '1',
				'channelNumber': int(channelTag.find('number').text or '0'),
				'subChannelNumber': 0,
				'channelName': channelTag.find('name').text or '',
				'inputFormat': '',
				'streamURL': channelTag.find('stream').text or '',
				'encryptionSystem': int(channelTag.find('encryption').text or 0),
				'iconPath': channelTag.find('icon').text or '',
				'isHidden': False
			})
	
	def GetAddonCapabilities(self):
		return libpvr.PVR_ERROR.NO_ERROR, {
			'supportsEPG': True,
			'supportsTV': True,
			'supportsRadio': True,
			'supportsRecordings': True,
			'supportsRecordingsUndelete': True,
			'supportsTimers': True,
			'supportsChannelGroups': True
		}
	
	def GetBackendName(self):
		return 'python pvr demo backend'
	
	def GetConnectionString(self):
		return 'connected'
	
	def GetBackendVersion(self):
		return '0.0.1.0'
	
	def GetBackendHostname(self):
		return ''
	
	def GetChannels(self, radio):
		for channel in self.channels:
			if channel['isRadio'] == radio:
				bridge.PVR_TransferChannelEntry(channel)
		
		return libpvr.PVR_ERROR.NO_ERROR
