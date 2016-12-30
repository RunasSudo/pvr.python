project(pvr.python)

cmake_minimum_required(VERSION 2.6)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${PROJECT_SOURCE_DIR})

enable_language(CXX)

find_package(Kodi REQUIRED)
find_package(p8-platform REQUIRED)

find_package(PythonInterp 2 REQUIRED)
find_package(PythonLibs 2 REQUIRED)

include_directories(${p8-platform_INCLUDE_DIRS}
                    ${KODI_INCLUDE_DIR}
                    ${PYTHON_INCLUDE_DIRS})

set(DEPLIBS ${p8-platform_LIBRARIES}
            ${PYTHON_LIBRARIES})

set(PVRPYTHON_SOURCES src/client.cpp)

build_addon(pvr.python PVRPYTHON DEPLIBS)

include(CPack)
