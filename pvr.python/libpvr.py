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
