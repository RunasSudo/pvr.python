# Kodi Python PVR Client
A PVR client supporting Python scripting for [Kodi](http://kodi.tv)

## Build instructions

### Linux

1. `mkdir build && cd build`
2. `cmake -DADDONS_TO_BUILD=pvr.python -DADDON_SRC_PREFIX=../.. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=/path/to/xbmc/addons -DPACKAGE_ZIP=1 /path/to/xbmc/project/cmake/addons`
3. `make`

## Licence

Copyright © 2016  RunasSudo (Yingtong Li)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.

Limited portions of supporting code are based on code © 2011 Pulse-Eight, licensed under the GPLv2 or later.
