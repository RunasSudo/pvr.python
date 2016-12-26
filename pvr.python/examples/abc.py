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
import gzip
import json
import os
import re
import StringIO
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
		self.channels = [
			PVRChannel(
				uniqueId = 1,
				isRadio = False,
				channelNumber = 21,
				channelName = 'ABC 1',
				streamURL = '' # We will manage the IO ourselves
			),
			PVRChannel(
				uniqueId = 2,
				isRadio = False,
				channelNumber = 22,
				subChannelNumber = 1,
				channelName = 'ABC 2',
				streamURL = ''
			),
			PVRChannel(
				uniqueId = 3,
				isRadio = False,
				channelNumber = 22,
				subChannelNumber = 2,
				channelName = 'ABC Kids',
				streamURL = ''
			),
			PVRChannel(
				uniqueId = 4,
				isRadio = False,
				channelNumber = 23,
				channelName = 'ABC ME',
				streamURL = ''
			),
			PVRChannel(
				uniqueId = 5,
				isRadio = False,
				channelNumber = 24,
				channelName = 'ABC News 24',
				#streamURL = ''
				streamURL = 'http://iphonestreaming.abc.net.au/news24/news24.m3u8'
			)
		]
		
		self.hdsIds = {
			1: 'abc1_1@360322',
			2: 'abc2_1@17511',
			3: 'abckids_1@390083',
			4: 'abc3_1@62060',
			5: 'news24_1@321136'
		}
	
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
		return 'python pvr abc backend'
	
	def GetConnectionString(self):
		return 'connected'
	
	def GetBackendVersion(self):
		return '0.0.2.3'
	
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
	
	# http://forum.kodi.tv/showthread.php?tid=146527&pid=1250345#pid1250345
	def getGenre(self, listingEntry):
		genreNos = []
		genreOthers = []
		if 'genres' in listingEntry:
			for genre in listingEntry['genres']:
				if genre == 'Game Show':
					genreNos.append((0x30, 0x01))
				elif genre == 'Travel':
					genreNos.append((0xA0, 0x01))
				elif genre == 'Romance':
					genreNos.append((0x10, 0x06))
				elif genre == 'Music':
					genreNos.append((0x60, 0x00))
				elif genre == 'Factual':
					genreNos.append((0x90, 0x00))
				elif genre == 'Comedy':
					genreNos.append((0x10, 0x04))
				elif genre == 'Sci-fi' or genre == 'Fantasy': # Humph. They are clearly different things.
					genreNos.append((0x10, 0x03))
				elif genre == 'Talk Show':
					genreNos.append((0x30, 0x03))
				elif genre == 'Special Event':
					genreNos.append((0x40, 0x01))
				elif genre == 'Advantage':
					genreNos.append((0x10, 0x02))
				elif genre == 'News' or genre == 'Current Affairs':
					genreNos.append((0x20, 0x00))
				elif genre == 'Drama':
					genreNos.append((0x10, 0x00))
				elif genre == 'Documentary':
					genreNos.append((0x20, 0x03))
				elif genre == 'Musical':
					genreNos.append((0x60, 0x04))
				elif genre == 'Arts and Culture':
					genreNos.append((0x70, 0x00))
				elif genre == 'Soap Opera':
					genreNos.append((0x10, 0x05))
				elif genre == 'Sport':
					genreNos.append((0x40, 0x00))
				elif genre == 'Children':
					genreNos.append((0x50, 0x00))
				else:
					genreOthers.append(genre)
		
		if len(genreNos) > 0:
			return (genreNos[0][0], genreNos[0][1], '')
		elif len(genreOthers) > 0:
			return (256, 0, genreOthers[0])
		else:
			return (0, 0, '')
	
	def GetEPGForChannel(self, channelId, cstartTime, cendTime):
		startTime = datetime.datetime.fromtimestamp(cstartTime)
		endTime = datetime.datetime.fromtimestamp(cendTime)
		
		# The internal mktime() expects EPG times in local time, but ABC provides them in Sydney time (+1000/+1100)
		# If only pytz were a default library...
		def UTCIsSydneyDST(dt):
			# Times in EST->UTC:
			firstSundayInOct = dt.replace(month=10,day=1,hour=2,minute=0,second=0,microsecond=0) # DST begins
			firstSundayInOct += datetime.timedelta(days=((7 - firstSundayInOct.isoweekday()) % 7))
			firstSundayInOct -= datetime.timedelta(hours=10)
			firstSundayInApr = dt.replace(month=10,day=1,hour=2,minute=0,second=0,microsecond=0) # DST ends
			firstSundayInApr += datetime.timedelta(days=((7 - firstSundayInApr.isoweekday()) % 7))
			firstSundayInApr -= datetime.timedelta(hours=10)
			if dt > firstSundayInApr and dt < firstSundayInOct:
				return False
			return True
		timeInSydney = datetime.datetime.utcnow()
		if UTCIsSydneyDST(timeInSydney):
			timeInSydney += datetime.timedelta(hours=11)
		else:
			timeInSydney += datetime.timedelta(hours=10)
		localTZ = datetime.datetime.now() - datetime.datetime.utcnow() #UTC + how much?
		def sydneyToLocal(dt):
			# This will be wrong for one hour after DST ends, but the ABC EPG seems to give up around that period any way
			dtUtc = dt - datetime.timedelta(hours=11)
			if not UTCIsSydneyDST(dtUtc):
				dtUtc += datetime.timedelta(hours=1)
			return dtUtc + localTZ
		
		# Load the EPG pages
		date = startTime.replace(hour=0,minute=0,second=0,microsecond=0)
		while date < endTime:
			try:
				handle = urllib2.urlopen('http://epg.abctv.net.au/processed/Sydney_{}-{}-{}.json'.format(date.year, date.month, date.day))
			except Exception as ex:
				traceback.print_exc()
				raise PVRListDone(PVR_ERROR.SERVER_ERROR)
			if handle.info().get('Content-Encoding') == 'gzip':
				handle = gzip.GzipFile(fileobj=StringIO.StringIO(handle.read()))
			
			epgJson = json.load(handle)
			
			for i, channelEntry in enumerate(epgJson['schedule']):
				if ((channelId == 1 and channelEntry['channel'] == 'ABC1') or
				    (channelId == 2 and channelEntry['channel'] == 'ABC2') or
				    (channelId == 3 and channelEntry['channel'] == 'ABC4KIDS') or
				    (channelId == 4 and channelEntry['channel'] == 'ABC3') or
				    (channelId == 5 and channelEntry['channel'] == 'ABCN')):
					for listingEntry in channelEntry['listing']:
						# Sometimes the next line fails once but works immediately afterwards, and I don't know why.
						# I'm scared...
						for i in xrange(0, 5):
							try:
								epgStartTime = sydneyToLocal(datetime.datetime.strptime(listingEntry['start_time'], '%Y-%m-%dT%H:%M:%S'))
								break
							except Exception as ex:
								pass
						if i == 4:
							print 'Couldn\'t do it'
							raise Exception('Uh oh')
						epgEndTime = sydneyToLocal(datetime.datetime.strptime(listingEntry['end_time'].encode('utf-8'), '%Y-%m-%dT%H:%M:%S'))
						
						if epgStartTime <= endTime and epgEndTime >= startTime:
							# Dodgy method of generating a unique id
							epgId = date.toordinal() * 1000 + i
							genre = self.getGenre(listingEntry)
							
							yield EPGTag(
								uniqueBroadcastId = epgId,
								title = listingEntry['title'] if 'title' in listingEntry else '',
								channelNumber = channelId,
								startTime = epgStartTime,
								endTime = epgEndTime,
								plot = listingEntry['description'] if 'description' in listingEntry else '',
								originalTitle = listingEntry['onair_title'] if 'onair_title' in listingEntry else '',
								genreType = genre[0],
								genreSubType = genre[1],
								genreDescription = genre[2],
								seriesNumber = listingEntry['series_num'] if 'series_num' in listingEntry else -1,
								episodeNumber = listingEntry['episode_num'] if 'episode_num' in listingEntry else -1
							)
			
			date += datetime.timedelta(days=1)
		
		raise PVRListDone(PVR_ERROR.NO_ERROR)
	
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
			cmd = ['php', os.path.join(self.clientPath, 'examples', 'AdobeHDS.php')] + self.GetStreamOptions('http://abctvlivehds-lh.akamaihd.net/z/{}/manifest.f4m'.format(self.hdsIds[channelId]))
			
			#print "{} '{}' {} '{}' {} '{}' {} '{}' {}".format(*cmd)
			
			self.streamProc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
			
			return True
		except:
			traceback.print_exc()
		
		return False
	
	def ReadLiveStream(self, bufferSize):
		if self.streamProc is not None:
			buf = self.streamProc.stdout.read(bufferSize)
			#print 'Read {} bytes'.format(len(buf))
			#sys.stdout.write(buf)
			return len(buf), buf
		
		return 0, None
	
	def CloseLiveStream(self):
		if self.streamProc is not None:
			# Release the reference immediately, but keep a copy ourselves to kill in the background
			streamProc = self.streamProc
			self.streamProc = None
			
			streamProc.kill()
			print 'Waiting for process to exit'
			streamProc.communicate()
	
	def CanPauseStream(self):
		return True
	
	def CanSeekStream(self):
		return True
