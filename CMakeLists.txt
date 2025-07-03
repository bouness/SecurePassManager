# CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(securepass)

include(InstallRequiredSystemLibraries)

set(CPACK_PACKAGE_NAME "securepass")
set(CPACK_PACKAGE_VERSION "1.0.0")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "bouness")
set(CPACK_PACKAGING_INSTALL_PREFIX "/opt/securepass")
include(CPack)