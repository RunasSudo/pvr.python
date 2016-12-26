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
		self.channels = (ABCHelper(self).getChannels() +
		                 SevenHelper(self).getChannels())
		
		# EPG IDs:
		# ~1-367000: ABC
		# 500000+: Seven
	
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
	
	def GetEPGForChannel(self, channelId, cstartTime, cendTime):
		channel = next(x for x in self.channels if x.uniqueId == channelId)
		startTime = datetime.datetime.fromtimestamp(cstartTime)
		endTime = datetime.datetime.fromtimestamp(cendTime)
		
		for item in channel._data['helper'].GetEPGForChannel(channel, startTime, endTime):
			yield item
	
	def OpenLiveStream(self, channelId):
		channel = next(x for x in self.channels if x.uniqueId == channelId)
		return channel._data['helper'].OpenLiveStream(channel)
	
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


# Do the hard yakka
class ABCHelper:
	def __init__(self, pvrImpl):
		self.pvrImpl = pvrImpl
		
		self.swfhash = None
		self.epgCache = {}
	
	def getChannels(self):
		return [
			PVRChannel(
				uniqueId = 1,
				isRadio = False,
				channelNumber = 21,
				channelName = 'ABC 1',
				streamURL = '', # We will manage the IO ourselves
				_data = { 'helper': self, 'hdsId': 'abc1_1@360322', 'epgChannel': 'ABC1' }
			),
			PVRChannel(
				uniqueId = 2,
				isRadio = False,
				channelNumber = 22,
				subChannelNumber = 1,
				channelName = 'ABC 2',
				streamURL = '',
				_data = { 'helper': self, 'hdsId': 'abc2_1@17511', 'epgChannel': 'ABC2' }
			),
			PVRChannel(
				uniqueId = 3,
				isRadio = False,
				channelNumber = 22,
				subChannelNumber = 2,
				channelName = 'ABC Kids',
				streamURL = '',
				_data = { 'helper': self, 'hdsId': 'abckids_1@390083', 'epgChannel': 'ABC4KIDS' }
			),
			PVRChannel(
				uniqueId = 4,
				isRadio = False,
				channelNumber = 23,
				channelName = 'ABC ME',
				streamURL = '',
				_data = { 'helper': self, 'hdsId': 'abc3_1@62060', 'epgChannel': 'ABC3' }
			),
			PVRChannel(
				uniqueId = 5,
				isRadio = False,
				channelNumber = 24,
				channelName = 'ABC News 24',
				#streamURL = '',
				streamURL = 'http://iphonestreaming.abc.net.au/news24/news24.m3u8',
				_data = { 'helper': self, 'hdsId': 'news24_1@321136', 'epgChannel': 'ABCN' }
			)
		]
	
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
	
	def GetEPGForChannel(self, channel, startTime, endTime):
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
			epgUrl = 'http://epg.abctv.net.au/processed/Sydney_{}-{}-{}.json'.format(date.year, date.month, date.day)
			
			# We don't want to fetch the file once per channel
			if epgUrl in self.epgCache:
				epgJson = self.epgCache[epgUrl]
			else:
				try:
					handle = urllib2.urlopen(epgUrl)
				except Exception as ex:
					traceback.print_exc()
					raise PVRListDone(PVR_ERROR.SERVER_ERROR)
				if handle.info().get('Content-Encoding') == 'gzip':
					handle = gzip.GzipFile(fileobj=StringIO.StringIO(handle.read()))
				
				epgJson = json.load(handle)
				self.epgCache[epgUrl] = epgJson
			
			for i, channelEntry in enumerate(epgJson['schedule']):
				if channelEntry['channel'] == channel._data['epgChannel']:
					for listingEntry in channelEntry['listing']:
						epgStartTime = sydneyToLocal(datetime.datetime.strptime(listingEntry['start_time'], '%Y-%m-%dT%H:%M:%S'))
						epgEndTime = sydneyToLocal(datetime.datetime.strptime(listingEntry['end_time'], '%Y-%m-%dT%H:%M:%S'))
						
						if epgStartTime <= endTime and epgEndTime >= startTime:
							# Dodgy method of generating a unique id
							epgId = date.toordinal() * 1000 + i
							genre = self.getGenre(listingEntry)
							
							yield EPGTag(
								uniqueBroadcastId = epgId,
								title = listingEntry['title'] if 'title' in listingEntry else '',
								channelNumber = channel.uniqueId,
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
		if self.swfhash is None:
			# Fetch the verification swf
			handle = urllib2.urlopen(urllib2.Request('http://iview.abc.net.au/assets/swf/CineramaWrapper_Acc_022.swf?version=0.2', headers={'User-Agent': USER_AGENT}))
			data = handle.read()
			# Decompress it
			if data[:3] == b'CWS':
				data = b'F' + data[1:8] + zlib.decompress(data[8:])
			# Hash it
			hashf = hashlib.sha256()
			hashf.update(data)
			self.swfhash = base64.b64encode(hashf.digest()).decode('ascii')
		
		# Get token
		handle = urllib2.urlopen(urllib2.Request('http://iview.abc.net.au/auth/flash/?1', headers={'User-Agent': USER_AGENT}))
		tokenhd = re.search('<tokenhd>(.*)</tokenhd>', handle.read().decode('utf-8')).group(1)
		
		# Get manifest
		manifestUrl = manifestBase + '?' + urllib.urlencode({'hdcore': 'true', 'hdnea': tokenhd})
		handle = urllib2.urlopen(urllib2.Request(manifestUrl, headers={'User-Agent': USER_AGENT}))
		# Compute pvtoken
		pv = re.search('<pv-2.0>(.*)</pv-2.0>', handle.read().decode('utf-8')).group(1)
		data, hdntl = pv.split(';')
		msg = 'st=0~exp=9999999999~acl=*~data={}!{}'.format(data, self.swfhash)
		auth = hmac.new(AKAMAIHD_PV_KEY, msg.encode('ascii'), hashlib.sha256)
		pvtoken = '{}~hmac={}'.format(msg, auth.hexdigest())
		
		return ['--manifest', manifestUrl, '--auth', urllib.urlencode({'pvtoken': pvtoken, 'hdcore': '2.11.3', 'hdntl': hdntl[6:]}), '--useragent', USER_AGENT, '--play']
	
	def OpenLiveStream(channel):
		try:
			cmd = ['php', os.path.join(pvrImpl.clientPath, 'examples', 'AdobeHDS.php')] + self.GetStreamOptions('http://abctvlivehds-lh.akamaihd.net/z/{}/manifest.f4m'.format(channel._data['hdsId']))
			
			pvrImpl.streamProc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
			
			return True
		except:
			traceback.print_exc()
		
		return False

class SevenHelper:
	def __init__(self, pvrImpl):
		self.pvrImpl = pvrImpl
		
		self.epgCache = {}
	
	def getChannels(self):
		return [
			PVRChannel(
				uniqueId = 11,
				isRadio = False,
				channelNumber = 71,
				channelName = 'Seven Adelaide',
				streamURL = 'https://sevenwestmedia01-i.akamaihd.net/hls/live/224816/ADE1/master_high.m3u8',
				_data = { 'helper': self, 'epgId': '7' }
			),
			PVRChannel(
				uniqueId = 12,
				isRadio = False,
				channelNumber = 72,
				channelName = '7TWO Adelaide',
				streamURL = 'https://sevenwestmedia01-i.akamaihd.net/hls/live/224829/ADE2/master_high.m3u8',
				_data = { 'helper': self, 'epgId': '8' }
			),
			PVRChannel(
				uniqueId = 13,
				isRadio = False,
				channelNumber = 73,
				channelName = '7mate Adelaide',
				streamURL = 'https://sevenwestmedia01-i.akamaihd.net/hls/live/224842/ADE3/master_high.m3u8',
				_data = { 'helper': self, 'epgId': '9' }
			),
			PVRChannel(
				uniqueId = 14,
				isRadio = False,
				channelNumber = 76,
				channelName = '7flix Adelaide',
				streamURL = 'https://sevenwestmedia01-i.akamaihd.net/hls/live/224859/ADE6/master_high.m3u8',
				_data = { 'helper': self, 'epgId': '42' }
			)
		]
	
	def getGenre(self, item):
		genreNos = []
		genreOthers = []
		genre = item['program_genre']
		if genre == 'GAME SHOW':
			genreNos.append((0x30, 0x01))
		elif genre == 'OTHER NEWS/CURRENT AFFAIRS' or genre == 'NEWS' or genre == 'CURRENT AFFAIRS':
			genreNos.append((0x20, 0x00))
		elif genre == 'OTHER DRAMA SERIES' or genre == 'DRAMA MOVIE' or genre == 'OTHER MOVIE' or genre == 'DRAMA SERIAL':
			genreNos.append((0x10, 0x00))
		elif genre == 'COMEDY MOVIE' or genre == 'SITUATION COMEDY' or genre == 'SKETCH COMEDY':
			genreNos.append((0x10, 0x04))
		elif genre == 'THRILLER MOVIE':
			genreNos.append((0x10, 0x01))
		elif genre == 'SITUATIONAL COMEDY':
			genreNos.append((0x10, 0x03))
		elif genre == 'ANIMALS':
			genreNos.append((0x90, 0x01))
		elif genre == 'RELIGIOUS PROGRAMS':
			genreNos.append((0x70, 0x03))
		elif genre == 'HEALTH':
			genreNos.append((0xA0, 0x04))
		elif genre == 'CHILDREN\'S ANIMATED' or genre == 'OTHER CHILDREN\'S PROGRAM':
			genreNos.append((0x50, 0x00))
		elif genre == 'PRE-SCHOOL PROGRAM':
			genreNos.append((0x50, 0x01))
		elif genre == 'COOKING':
			genreNos.append((0xA0, 0x05))
		elif genre == 'OTHER DOCUMENTARY SERIES' or genre == 'DOCUMENTARY ONE-OFF':
			genreNos.append((0x20, 0x03))
		elif genre == 'OTHER INFORMATION':
			genreNos.append((0x90, 0x00))
		elif genre == 'TRAVEL':
			genreNos.append((0xA0, 0x01))
		elif genre == 'OTHER PROGRAM':
			genreNos.append((0x00, 0x00))
		elif genre == 'SPORTS OTHER':
			genreNos.append((0x40, 0x00))
		elif genre == 'MUSIC PERFORMANCE':
			genreNos.append((0x60, 0x00))
		else:
			genreOthers.append(genre.title())
		
		if len(genreNos) > 0:
			return (genreNos[0][0], genreNos[0][1], '')
		elif len(genreOthers) > 0:
			return (256, 0, genreOthers[0])
		else:
			return (0, 0, '')
	
	def GetEPGForChannel(self, channel, startTime, endTime):
		localTZ = datetime.datetime.now() - datetime.datetime.utcnow() #UTC + how much?
		
		epgUrl = 'https://7live.com.au/tvapi/v1/services/schedule/' + channel._data['epgId'] + '/list/?' + urllib.urlencode({'starttime': startTime.strftime('%Y-%m-%dT%H:%M:%S.000Z'), 'minutes': (endTime - startTime).total_seconds() // 60})
		
		# Probably no need to cache, since the url is different for each channel
		try:
			handle = urllib2.urlopen(epgUrl)
		except Exception as ex:
			traceback.print_exc()
			raise PVRListDone(PVR_ERROR.SERVER_ERROR)
		
		epgJson = json.load(handle)
		
		for programme in epgJson['schedule']:
			epgId = 500000 + programme['content_id']
			genre = self.getGenre(programme)
			pStartTime = programme['start_time']
			epgStartTime = datetime.datetime.strptime(pStartTime[:pStartTime.index('.')], '%Y-%m-%dT%H:%M:%S') + localTZ
			epgEndTime = epgStartTime + datetime.timedelta(minutes=programme['duration'])
			
			yield EPGTag(
				uniqueBroadcastId = epgId,
				title = programme['epg_title'] if 'epg_title' in programme else '',
				channelNumber = channel.uniqueId,
				startTime = epgStartTime,
				endTime = epgEndTime,
				plotOutline = programme['epg_synopsis'] if 'epg_synopsis' in programme else '',
				plot = programme['synopsis'] if 'synopsis' in programme else '',
				originalTitle = programme['program_title'] if 'program_title' in programme else '',
				cast = programme['cast'] if 'cast' in programme else '',
				year = programme['year_released'] if 'year_released' in programme else 0,
				genreType = genre[0],
				genreSubType = genre[1],
				genreDescription = genre[2],
				episodeName = programme['episode_title'] if 'episode_title' in programme else ''
			)
		
		#NYI
		raise PVRListDone(PVR_ERROR.NO_ERROR)
