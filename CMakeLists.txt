project(pvr.python)

cmake_minimum_required(VERSION 2.6)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${PROJECT_SOURCE_DIR})

enable_language(CXX)

find_package(Kodi REQUIRED)
find_package(kodiplatform REQUIRED)
find_package(p8-platform REQUIRED)

find_package(PythonInterp 2 REQUIRED)
find_package(PythonLibs 2 REQUIRED)

include_directories(${kodiplatform_INCLUDE_DIRS}
                    ${p8-platform_INCLUDE_DIRS}
                    ${KODI_INCLUDE_DIR}
                    ${PYTHON_INCLUDE_DIRS})

set(DEPLIBS ${kodiplatform_LIBRARIES}
            ${p8-platform_LIBRARIES}
            ${PYTHON_LIBRARIES})

set(PVRPYTHON_SOURCES src/client.cpp
                      src/PVRDemoData.cpp)

build_addon(pvr.python PVRPYTHON DEPLIBS)

include(CPack)
