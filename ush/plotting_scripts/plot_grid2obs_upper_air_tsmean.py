#!/usr/bin/env python
'''
Program Name: plot_grid2obs_upper_air_tsmean.py
Contact(s): Mallory Row
Abstract: Reads mean forecast hour files from plot_grid2obs_upper_air_ts.py to make dieoff plots
History Log:  Initial version
Usage: 
Parameters: None
Input Files: ASCII files
Output Files: .png images
Condition codes: 0 for success, 1 for failure
'''
############################################################################
##### Import python modules
from __future__ import (print_function, division)
import os
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import warnings
import logging
#############################################################################
##### Settings
np.set_printoptions(suppress=True)
plt.rcParams['font.weight'] = 'bold'
plt.rcParams['axes.labelsize'] = 15
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['xtick.labelsize'] = 15
plt.rcParams['ytick.labelsize'] = 15
plt.rcParams['axes.titlesize'] = 15
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.formatter.useoffset'] = False
warnings.filterwarnings('ignore')
colors = ['black', 'darkgreen', 'darkred', 'indigo', 'blue', 'crimson', 'goldenrod', 'sandybrown', 'thistle']
##############################################################################
##### Read in data and set variables
#forecast dates
month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
sdate = os.environ['START_T']
syear = int(sdate[:4])
smon = int(sdate[4:6])
smonth = month_name[smon-1]
sday = int(sdate[6:8])
edate=os.environ['END_T']
eyear = int(edate[:4])
emon = int(edate[4:6])
emonth = month_name[emon-1]
eday = int(edate[6:8])
date_filter_method = os.environ['DATE_FILTER_METHOD']
#input info
model_list = os.environ['MODEL_LIST'].replace(", ", ",").split(",")
nmodels = len(model_list)
cycle = os.environ['CYCLE']
lead_list = os.environ['LEAD_LIST'].replace(", ", ",").split(",")
leads = np.asarray(lead_list).astype(float)
region = os.environ['REGION']
grid = os.environ['REGRID_TO_GRID']
plot_stats_list = os.environ['PLOT_STATS_LIST'].replace(", ", ",").split(",")
nstats = len(plot_stats_list)
fcst_var_name = os.environ['FCST_VAR_NAME']
fcst_var_levels_list = os.environ['FCST_VAR_LEVELS_LIST'].replace(", ", ",").split(",")
obs_var_name = os.environ['OBS_VAR_NAME']
obs_var_levels_list = os.environ['OBS_VAR_LEVELS_LIST'].replace(", ", ",").split(",")
nlevels = len(fcst_var_levels_list)
#ouput info
logging_filename = os.environ['LOGGING_FILENAME']
logger = logging.getLogger(logging_filename)
logger.setLevel("DEBUG")
formatter = logging.Formatter("%(asctime)s.%(msecs)03d (%(filename)s:%(lineno)d) ""%(levelname)s: %(message)s","%m/%d %H:%M:%S")
file_handler = logging.FileHandler(logging_filename, mode='a')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
ch = logging.StreamHandler()
logger.addHandler(ch)
plotting_out_dir = os.environ['PLOTTING_OUT_DIR']
####################################################################
logger.info("------> Running "+os.path.realpath(__file__))
logger.debug("----- for "+date_filter_method+" start date:"+sdate+" "+date_filter_method+" end date:"+edate+" cycle:"+cycle+"Z forecast hour means for region:"+region+" fcst var:"+fcst_var_name+" obs var:"+obs_var_name)
#############################################################################
##### Read data in data, compute statistics, and plot
#read in data
vl = 1
while vl <= nlevels:
    fcst_var_level_now = fcst_var_levels_list[vl-1]
    obs_var_level_now = obs_var_levels_list[vl-1]
    logger.debug("---- fcst level:"+fcst_var_level_now+" obs level:"+obs_var_level_now)
    s=1
    while s <= nstats: #loop over statistics
        stat_now = plot_stats_list[s-1]
        logger.debug("--- "+stat_now)
     	m=1
     	while m <= nmodels: #loop over models
             model_now = model_list[m-1]
             logger.debug(str(m)+" "+model_now)
             if stat_now == 'avg':
                 #get forecast hour mean file
                 model_now_fbar_mean_file = plotting_out_dir+"/data/"+cycle+"Z/"+model_now+"/fbar_mean_"+region+"_fcst"+fcst_var_name+fcst_var_level_now+"_obs"+obs_var_name+obs_var_level_now+".txt"
                 if os.path.exists(model_now_fbar_mean_file):
                     nrow = sum(1 for line in open(model_now_fbar_mean_file))
                     if nrow == 0: #file blank
                         logger.warning(model_now_fbar_mean_file+" was empty! Setting to NaN")
                         model_now_fbar_mean = np.ones_like(leads) * np.nan
                     else:
                         logger.debug("Found "+model_now_fbar_mean_file)
                         #read data file and put in array
                         data = list()
                         with open(model_now_fbar_mean_file) as f:
                             for line in f:
                                 line_split = line.split()
                                 data.append(line_split)
                         data_array = np.asarray(data)
                         #assign variables
                         model_now_fbar_leads = data_array[:,0].astype(float)
                         model_now_fbar_mean = data_array[:,1]
                         #check for missing data
                         for l in range(len(leads)):
                             if leads[l] == model_now_fbar_leads[l]:
                                 model_now_fbar_mean[l] = model_now_fbar_mean[l]
                             else:
                                 ll = np.where(model_now_fbar_leads == leads[l])[0]
                                 if len(ll) != 0:
                                     model_now_fbar_mean[l] = model_now_fbar_mean[ll[0]]
                                 else:
                                     model_now_fbar_mean[l] = np.nan
                 else:
                     logger.error(model_now_fbar_mean_file+" NOT FOUND! Setting to NaN")
                     model_now_fbar_mean = np.ones_like(leads) * np.nan
                 model_now_fbar_mean[model_now_fbar_mean == '--'] = np.nan
                 model_now_fbar_mean = model_now_fbar_mean.astype(float)
                 model_now_fbar_mean = np.ma.masked_array(model_now_fbar_mean, mask=model_now_fbar_mean == np.nan)
                 count_masked_fbar = np.ma.count_masked(model_now_fbar_mean)
                 #get forecast hour mean file
                 model_now_obar_mean_file = plotting_out_dir+"/data/"+cycle+"Z/"+model_now+"/obar_mean_"+region+"_fcst"+fcst_var_name+fcst_var_level_now+"_obs"+obs_var_name+obs_var_level_now+".txt"
                 if os.path.exists(model_now_obar_mean_file):
                     nrow = sum(1 for line in open(model_now_obar_mean_file))
                     if nrow == 0: #file blank
                         logger.warning(model_now_obar_mean_file+" was empty! Setting to NaN")
                         model_now_obar_mean = np.ones_like(leads) * np.nan
                     else:
                         logger.debug("Found "+model_now_obar_mean_file)
                         #read data file and put in array
                         data = list()
                         with open(model_now_obar_mean_file) as f:
                             for line in f:
                                 line_split = line.split()
                                 data.append(line_split)
                         data_array = np.asarray(data)
                         #assign variables
                         model_now_obar_leads = data_array[:,0].astype(float)
                         model_now_obar_mean = data_array[:,1]
                         #check for missing data
                         for l in range(len(leads)):
                             if leads[l] == model_now_obar_leads[l]:
                                 model_now_obar_mean[l] = model_now_obar_mean[l]
                             else:
                                 ll = np.where(model_now_obar_leads == leads[l])[0]
                                 if len(ll) != 0:
                                     model_now_obar_mean[l] = model_now_obar_mean[ll[0]]
                                 else:
                                     model_now_obar_mean[l] = np.nan
                 else:
                     logger.error(model_now_obar_mean_file+" NOT FOUND! Setting to NaN")
                     model_now_obar_mean = np.ones_like(leads) * np.nan
                 model_now_obar_mean[model_now_obar_mean == '--'] = np.nan
                 model_now_obar_mean = model_now_obar_mean.astype(float)
                 model_now_obar_mean = np.ma.masked_array(model_now_obar_mean, mask=model_now_obar_mean == np.nan)
                 count_masked_obar = np.ma.count_masked(model_now_obar_mean)
                 #create image directory if does not exist
                 if not os.path.exists(os.path.join(plotting_out_dir, "imgs", cycle+"Z")):
                    os.makedirs(os.path.join(plotting_out_dir, "imgs", cycle+"Z"))
                 #plot individual statistic forecast hour mean
                 if m == 1:
                     fig, (ax1, ax2) = plt.subplots(2,1,figsize=(10,6), sharex=True)
                     #forecast hour mean
                     if count_masked_obar != len(model_now_obar_mean):
                         logger.debug("Plotting obar lead forecast hour means for "+model_now)
                         ax1.plot(leads, model_now_obar_mean, color='dimgrey', ls='-', linewidth=2.0, marker='o', markersize=7, label='obs')
                         model_1_obar_mean = model_now_obar_mean
                     #forecast hour mean
                     if count_masked_fbar != len(model_now_fbar_mean):
                         logger.debug("Plotting fbar lead forecast hour means for "+model_now)
                         ax1.plot(leads, model_now_fbar_mean, color=colors[m-1], ls='-', linewidth=2.0, marker='o', markersize=7, label=model_now)
                         ax2.plot(leads, model_now_fbar_mean - model_1_obar_mean, color=colors[m-1], ls='-',  marker='o', markersize=7)
                     ax1.grid(True)
                     ax1.set_xticks(leads)
                     ax1.set_xlim([leads[0],leads[-1]])
                     ax1.tick_params(axis='x', pad=10)
                     ax1.tick_params(axis='y', pad=15)
                     #difference from model 1 set up
                     ax2.plot(leads, np.zeros_like(leads), color='k')
                     ax2.set_xlabel("Forecast Hour")
                     ax2.tick_params(axis='x', pad=10)
                     ax2.tick_params(axis='y', pad=15)
                     ax2.set_title("Difference with Respect to obs.")
                     ax2.grid(True)
                 else:
                     #forecast hour mean
                     if count_masked_fbar != len(model_now_fbar_mean):
                         logger.debug("Plotting fbar lead forecast hour means for "+model_now)
                         ax1.plot(leads, model_now_fbar_mean, color=colors[m-1], ls='-', marker='o', markersize=7, label=model_now)
                         ax2.plot(leads, model_now_fbar_mean - model_1_obar_mean, color=colors[m-1], ls='-',  marker='o', markersize=7)
             else:
                 #get forecast hour mean file
                 model_now_mean_file = plotting_out_dir+"/data/"+cycle+"Z/"+model_now+"/"+stat_now+"_mean_"+region+"_fcst"+fcst_var_name+fcst_var_level_now+"_obs"+obs_var_name+obs_var_level_now+".txt"
                 if os.path.exists(model_now_mean_file):
                     nrow = sum(1 for line in open(model_now_mean_file))
                     if nrow == 0: #file blank
                         logger.warning(model_now_mean_file+" was empty! Setting to NaN")
                         model_now_stat_now_mean = np.ones_like(leads) * np.nan 
                     else:
                         logger.debug("Found "+model_now_mean_file)
                         #read data file and put in array
                         data = list()
                         with open(model_now_mean_file) as f:
                             for line in f:
                                 line_split = line.split()
                                 data.append(line_split)
                         data_array = np.asarray(data)
                         #assign variables
                         model_now_leads = data_array[:,0].astype(float)
                         model_now_stat_now_mean = data_array[:,1]
                         #check for missing data
                         for l in range(len(leads)):
                             if leads[l] == model_now_leads[l]:
                                 model_now_stat_now_mean[l] = model_now_stat_now_mean[l]
                             else:
                                 ll = np.where(model_now_leads == leads[l])[0]
                                 if len(ll) != 0:
                                     model_now_stat_now_mean[l] = model_now_stat_now_mean[ll[0]]
                                 else:
                                     model_now_stat_now_mean[l] = np.nan
                 else:
                     logger.error(model_now_mean_file+" NOT FOUND! Setting to NaN")
                     model_now_stat_now_mean = np.ones_like(leads) * np.nan
                 model_now_stat_now_mean[model_now_stat_now_mean == '--'] = np.nan
                 model_now_stat_now_mean = model_now_stat_now_mean.astype(float)
                 model_now_stat_now_mean = np.ma.masked_array(model_now_stat_now_mean, mask=model_now_stat_now_mean == np.nan)
                 count_masked = np.ma.count_masked(model_now_stat_now_mean)
                 #create image directory if does not exist
                 if not os.path.exists(os.path.join(plotting_out_dir, "imgs", cycle+"Z")):
                    os.makedirs(os.path.join(plotting_out_dir, "imgs", cycle+"Z"))
                 #plot individual statistic forecast hour mean
                 if m == 1:
                     fig, (ax1, ax2) = plt.subplots(2,1,figsize=(10,6), sharex=True)
                     #forecast hour mean
                     if count_masked != len(model_now_stat_now_mean): 
                         logger.debug("Plotting "+stat_now+" lead forecast hour means for "+model_now)
                         ax1.plot(leads, model_now_stat_now_mean, color=colors[m-1], ls='-', linewidth=2.0, marker='o', markersize=7, label=model_now)
                     model_1_stat_now_mean = model_now_stat_now_mean
                     ax1.grid(True)
                     ax1.set_xticks(leads)
                     ax1.set_xlim([leads[0],leads[-1]])
                     ax1.tick_params(axis='x', pad=10)
                     ax1.tick_params(axis='y', pad=15)
                     #difference from model 1 set up
                     ax2.plot(leads, np.zeros_like(leads), color='k')
                     ax2.set_xlabel("Forecast Hour")
                     ax2.tick_params(axis='x', pad=10)
                     ax2.tick_params(axis='y', pad=15)
                     ax2.set_title("Difference with Respect to "+model_list[0])
                     ax2.grid(True)
                 else:
                     #forecast hour mean
                     if count_masked != len(model_now_stat_now_mean):
                         logger.debug("Plotting "+stat_now+" lead forecast hour means for "+model_now)
                         ax1.plot(leads, model_now_stat_now_mean, color=colors[m-1], ls='-', marker='o', markersize=7, label=model_now)
                         ax2.plot(leads, model_now_stat_now_mean - model_1_stat_now_mean, color=colors[m-1], ls='-',  marker='o', markersize=7)
             m+=1
        if stat_now == 'avg':
            ax1.legend(bbox_to_anchor=(0.0, 1.02, 1.0, .102), loc=3, ncol=nmodels+1, fontsize='13', mode="expand", borderaxespad=0.)
        else:
            ax1.legend(bbox_to_anchor=(0.0, 1.02, 1.0, .102), loc=3, ncol=nmodels, fontsize='13', mode="expand", borderaxespad=0.)
        ax1.set_title("Fcst: "+fcst_var_name+"_"+fcst_var_level_now+" Obs: "+obs_var_name+"_"+obs_var_level_now+" "+str(stat_now)+'\n'+grid+"-"+region+" "+date_filter_method+" "+cycle+"Z "+str(sday)+smonth+str(syear)+"-"+str(eday)+emonth+str(eyear)+" Means\n\n", fontsize=14, fontweight='bold')
        logger.debug("--- Saving image as "+plotting_out_dir+"/imgs/"+cycle+"Z/"+stat_now+"_fhrmeans_fcst"+fcst_var_name+fcst_var_level_now+"_obs"+obs_var_name+obs_var_level_now+"_"+grid+region+".png")
        plt.savefig(plotting_out_dir+"/imgs/"+cycle+"Z/"+stat_now+"_fhrmeans_fcst"+fcst_var_name+fcst_var_level_now+"_obs"+obs_var_name+obs_var_level_now+"_"+grid+region+".png", bbox_inches='tight')
        s+=1
    vl+=1
