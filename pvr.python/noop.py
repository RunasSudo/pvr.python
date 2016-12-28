# Noop script so that Kodi doesn't unload the Python shared library

import xbmc

monitor = xbmc.Monitor()

while not monitor.abortRequested():
	#print 'Hello from pvr.python noop script'
	if monitor.waitForAbort(5):
		# Abort was requested while waiting.
		break
