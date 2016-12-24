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
		
		def textDef(tag, default):
			if tag is None:
				return default
			if tag.text is None:
				return default
			return tag.text
		
		# Channels
		self.channels = []
		for channelTag in root.find('channels').findall('channel'):
			self.channels.append({
				'uniqueId': len(self.channels) + 1,
				'isRadio': textDef(channelTag.find('radio'), 0) == '1',
				'channelNumber': int(textDef(channelTag.find('number'), 0)),
				'subChannelNumber': 0,
				'channelName': textDef(channelTag.find('name'), ''),
				'inputFormat': '',
				'streamURL': textDef(channelTag.find('stream'), ''),
				'encryptionSystem': int(textDef(channelTag.find('encryption'), 0)),
				'iconPath': textDef(channelTag.find('icon'), ''),
				'isHidden': False
			})
		
		# Channel groups
		self.channelGroups = []
		for groupTag in root.find('channelgroups').findall('group'):
			self.channelGroups.append({
				'groupName': textDef(groupTag.find('name'), ''),
				'isRadio': textDef(groupTag.find('radio'), 0) == '1',
				'position': int(textDef(groupTag.find('position'), 0)),
				'members': [
					{
						'groupName': textDef(groupTag.find('name'), ''),
						'channelUniqueId': int(textDef(memberTag, 0)),
						'channelNumber': i + 1
					} for i, memberTag in enumerate(groupTag.find('members').findall('member'))] # Not passed at group stage
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
	
	def GetChannelGroups(self, radio):
		for group in self.channelGroups:
			if group['isRadio'] == radio:
				bridge.PVR_TransferChannelGroup(group)
		
		return libpvr.PVR_ERROR.NO_ERROR
	
	def GetChannelGroupMembers(self, group):
		for theGroup in self.channelGroups:
			if theGroup['groupName'] == group['groupName']:
				for member in theGroup['members']:
					bridge.PVR_TransferChannelGroupMember(member)
		
		return libpvr.PVR_ERROR.NO_ERROR
