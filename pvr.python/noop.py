# Noop script so that Kodi doesn't unload the Python shared library

import xbmc

import time

while not xbmc.abortRequested:
	#print 'Hello from pvr.python noop script'
	time.sleep(5)
