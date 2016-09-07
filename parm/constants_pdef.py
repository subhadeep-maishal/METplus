#!/usr/bin/env python

from __future__ import (print_function)
from ConfigMaster import ConfigMaster

class Params(ConfigMaster):
  defaultParams = """

import os

#
# Logging
#

#Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "DEBUG1"
LOG_DIR = "/d1/SBU_util/out/logs"
LOG_FILENAME = "extract_tiles.log"

#
# Executables
#

TC_STAT = "/d1/CODE/MET/MET_releases/met-5.2_beta2/bin/tc_stat"
WGRIB2 = "/d1/CODE/wgrib2"
SERIES_ANALYSIS = "/d1/CODE/MET/MET_releases/met-5.2_beta2/bin/series_analysis"
PLOT_DATA_PLANE = "/d1/CODE/MET/MET_releases/met-5.2_beta2/bin/plot_data_plane"
RM_EXE = "/bin/rm -rf"

#
# Project Directories
#

PROJ_DIR = "/d1/SBU/GFS"
GFS_DIR = os.path.join(PROJ_DIR, "model_data")

#
# Output Directories
# 
OUT_DIR = "/d1/SBU_util/out/series_analysis"

#
# Lists
#

# Used for performing series analysis both for lead time and init time
VAR_LIST = ["HGT/P500", "PRMSL/Z0", "TMP/Z2", "PWAT/L0"]
STAT_LIST = ["FBAR", "OBAR", "ME", "MAE", "RMSE"]
INIT_LIST = ["20150126_00", "20150126_06", "20150126_12", "20150126_18", "20150127_00", "20150127_06", "20150127_12", "20150127_18"]

# Used for performing series analysis based on lead time
FHR_BEG = 0
FHR_END = 138 
FHR_INC = 6


#
# Constants used in creating the tile grid
#
NLAT = 60
NLON = 60
# Resolution of data in degrees
DLAT = 0.5
DLON = 0.5
# Degrees to subtract to get center of 30 x 30 grid
LON_SUBTR = 15
LAT_SUBTR = 15

# 
# Constants used in performing the series analysis
#
CONFIG_BY_LEAD = "SeriesAnalysisConfig_by_lead"
CONFIG_BY_INIT = "SeriesAnalysisConfig"

#
# Testing
#
TEST_DIR = "/tmp/python_test"
TEST_FILENAME="extract_tiles_test.txt"

"""    
 