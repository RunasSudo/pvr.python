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

import base64
import datetime
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import traceback
import urllib, urllib2
import urlparse
import zlib

def getInstance():
	return ABCPVRImpl()

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0'
AKAMAIHD_PV_KEY = bytearray.fromhex('bd938d5ee6d9f42016f9c56577b6fdcf415fe4b184932b785ab32bcadc9bb592')

class ABCPVRImpl(BasePVR):
	def loadData(self, props):
		self.clientPath = props['clientPath']
		self.streamProc = None
		
		# Channels
		self.channels = [PVRChannel(
			uniqueId = 23,
			isRadio = False,
			channelName = 'ABC ME',
			streamURL = '' # We will manage the IO ourselves
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
		return 'python pvr abc backend'
	
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
	
	def GetStreamOptions(self, manifestBase):
		# Fetch the verification swf
		handle = urllib2.urlopen(urllib2.Request('http://iview.abc.net.au/assets/swf/CineramaWrapper_Acc_022.swf?version=0.2', headers={'User-Agent': USER_AGENT}))
		data = handle.read()
		# Decompress it
		if data[:3] == b'CWS':
			data = b'F' + data[1:8] + zlib.decompress(data[8:])
		# Hash it
		hashf = hashlib.sha256()
		hashf.update(data)
		swfhash = base64.b64encode(hashf.digest()).decode('ascii')
		
		# Get token
		handle = urllib2.urlopen(urllib2.Request('http://iview.abc.net.au/auth/flash/?1', headers={'User-Agent': USER_AGENT}))
		tokenhd = re.search('<tokenhd>(.*)</tokenhd>', handle.read().decode('utf-8')).group(1)
		
		# Get manifest
		manifestUrl = manifestBase + '?' + urllib.urlencode({'hdcore': 'true', 'hdnea': tokenhd})
		handle = urllib2.urlopen(urllib2.Request(manifestUrl, headers={'User-Agent': USER_AGENT}))
		# Compute pvtoken
		pv = re.search('<pv-2.0>(.*)</pv-2.0>', handle.read().decode('utf-8')).group(1)
		data, hdntl = pv.split(';')
		msg = 'st=0~exp=9999999999~acl=*~data={}!{}'.format(data, swfhash)
		auth = hmac.new(AKAMAIHD_PV_KEY, msg.encode('ascii'), hashlib.sha256)
		pvtoken = '{}~hmac={}'.format(msg, auth.hexdigest())
		
		return ['--manifest', manifestUrl, '--auth', urllib.urlencode({'pvtoken': pvtoken, 'hdcore': '2.11.3', 'hdntl': hdntl[6:]}), '--useragent', USER_AGENT, '--play']
	
	def OpenLiveStream(self, channelId):
		try:
			cmd = ['php', os.path.join(self.clientPath, 'examples', 'AdobeHDS.php')] + self.GetStreamOptions('http://abctvlivehds-lh.akamaihd.net/z/abc3_1@62060/manifest.f4m')
			
			#print "{} '{}' {} '{}' {} '{}' {} '{}' {}".format(*cmd)
			
			self.streamProc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
			
			return True
		except:
			traceback.print_exc()
		
		return False
	
	def ReadLiveStream(self, bufferSize):
		buf = self.streamProc.stdout.read(bufferSize)
		#print 'Read {} bytes'.format(len(buf))
		#sys.stdout.write(buf)
		return len(buf), buf
	
	def CloseLiveStream(self):
		if self.streamProc is not None:
			self.streamProc.kill()
			print 'Waiting for process to exit'
			self.streamProc.communicate()
		
		self.streamProc = None
