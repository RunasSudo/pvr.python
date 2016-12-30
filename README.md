# Kodi Python PVR Client
A PVR client supporting Python scripting for [Kodi](http://kodi.tv)

## Build instructions

### Linux (Full Kodi source)

1. `mkdir build && cd build`
2. `cmake -DADDONS_TO_BUILD=pvr.python -DADDON_SRC_PREFIX=../.. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=/path/to/xbmc/addons /home/packages/src/xbmc/project/cmake/addons
3. `make`

The addon will be found in the */path/to/xbmc/addons* folder.

### Linux (Kodi dev kit)

1. `mkdir build && cd build`
2. `cmake -DADDONS_TO_BUILD=pvr.python -DADDON_SRC_PREFIX=../.. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=out ..`
3. `make`
4. `make install`

The addon will be found in the *build/out* folder.

### Setting up Python

To use, name the Python PVR implementation *pvrimpl.py* and place it in the addon directory, e.g. *~/.kodi/addons/pvr.python/pvrimpl.py* or */usr/share/kodi/addons/pvr.python/pvrimpl.py*. The default *pvrimpl.py* is a re-implementation of the Demo PVR backend. Other examples are located in the *examples* directory.

## Developer notes

* As the Python scripts are executed by the pvr.python addon, there is no direct access to the usual Kodi modules (`xbmc`, `xbmcgui` and so on). Access to a limited range of the Kodi functions available to the addon is provided through the `bridge` module (e.g. `bridge.XBMC_Log`).
* The interface to the PVR API has been Python-ified. Multiple return values are used instead of pass-by-reference, Hungarian notation type prefixes are dropped, enums have their own namespace, generators are used instead of callbacks, and so on. Camel case, however, has generally been retained. When in doubt, check the implementation in *client.cpp*, or the reference implementation.
* This addon is currently in its infancy. The Python API is likely to undergo significant compatibility-breaking changes in future. The first nonzero component of the version code will be incremented to indicate a backwards-incompatible API change (e.g. 0.0.1.0 to 0.0.2.0; 0.1.4 to 0.2.0).
* Error handling is currently not very robust. Like, at all. No, seriously, error handling was *literally* an afterthought. [Double-check your damn ~~pointers!~~types!](https://xkcd.com/371/) Pull requests would be much appreciated!

### Implementation details

* Python functions beginning with `_c` are called to convert the Python attributes or processes to their C equivalents. For example, `_cstartTime` converts the `startTime` datetime.datetime object to a C timestamp; `_cGetChannels` passes the results from the iterator-based `GetChannels` to the native callback-based C API. Ideally, it should not be necessary to override these functions: the Python-based interface (without the `_c`) should be sufficient.

## Licence

Copyright © 2016  RunasSudo (Yingtong Li)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.

Limited portions of supporting code are based on code © 2011 Pulse-Eight, licensed under the GPLv2 or later.
