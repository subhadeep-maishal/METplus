#!/usr/bin/env python

'''
Program Name: grid_stat_wrapper.py
Contact(s): George McCabe
Abstract:
History Log:  Initial version
Usage: 
Parameters: None
Input Files:
Output Files:
Condition codes: 0 for success, 1 for failure
'''

from __future__ import (print_function, division)

import logging
import os
import sys
import met_util as util
import re
import csv
import subprocess
from command_builder import CommandBuilder
from task_info import TaskInfo
import string_template_substitution as sts


class GridStatWrapper(CommandBuilder):

    def __init__(self, p, logger):
        super(GridStatWrapper, self).__init__(p, logger)
        met_install_dir = p.getdir('MET_INSTALL_DIR')
        self.app_path = os.path.join(met_install_dir, 'bin/grid_stat')
        self.app_name = os.path.basename(self.app_path)

    def set_output_dir(self, outdir):
        self.outdir = "-outdir "+outdir

    def get_command(self):
        if self.app_path is None:
            self.logger.error(self.app_name + ": No app path specified. \
                              You must use a subclass")
            return None

        cmd = self.app_path + " "
        for a in self.args:
            cmd += a + " "

        if len(self.infiles) == 0:
            self.logger.error(self.app_name+": No input filenames specified")
            return None

        for f in self.infiles:
            cmd += f + " "

        if self.param != "":
            cmd += self.param + " "

        if self.outdir == "":
            self.logger.error(self.app_name+": No output directory specified")
            return None

        cmd += self.outdir
        return cmd

    def check_model(self, model_templates, model_types, max_forecasts):
        dsize = len(model_templates)
        if len(model_types) != dsize:
            print("ERROR: Number of model types != number of model templates")
            exit()
        if len(max_forecasts) != dsize:
            if len(max_forecasts) == 1:
                max_forecasts.extend(max_forecasts*(dsize-1))
            else:
                print("ERROR: Number of max forecasts != number of model templates or 1")
                exit()
        return

    def find_model(self, lead, init_time, level, cur_model):
        model_dir = self.p.getstr('config', 'FCST_GRID_STAT_INPUT_DIR')
        #max_forecast = self.p.getint('config', 'FCST_MAX_FORECAST')
        max_forecast = cur_model[2]
        init_interval = self.p.getint('config', 'FCST_INIT_INTERVAL')
        lead_check = lead
        time_check = init_time
        time_offset = 0
        found = False
        while lead_check <= max_forecast:
            #model_template = self.p.getraw('filename_templates',
            #                               'FCST_GRID_STAT_INPUT_TEMPLATE')
            model_template = cur_model[0]
            # split by - to handle a level that is a range, such as 0-10
            model_ss = sts.StringSub(self.logger, model_template,
                                     init=time_check,
                                     lead=str(lead_check).zfill(2),
                                     level=str(level.split('-')[0]).zfill(2))
            model_file = model_ss.doStringSub()
            model_path = os.path.join(model_dir, model_file)
            if os.path.exists(model_path):
                found = True
                break
            elif os.path.exists(model_path+".gz"):
                with gzip.open(model_path+".gz", 'rb') as infile:
                    with open(model_path, 'wb') as outfile:
                        outfile.write(infile.read())
                        infile.close()
                        outfile.close()
                        # TODO: change model_path to path without gz
                        # set found to true and break
            time_check = util.shift_time(time_check, -init_interval)
            lead_check = lead_check + init_interval            

        if found:
            return model_path
        else:
            return ''

    def run_at_time(self, init_time, valid_time):
        task_info = TaskInfo()
        task_info.init_time = init_time
        task_info.valid_time = valid_time        
        var_list = util.parse_var_list(self.p)
        
        model_templates = util.getlist(self.p.getraw('filename_templates','FCST_GRID_STAT_INPUT_TEMPLATE'))
        model_types = util.getlist(self.p.getraw('config','MODEL_TYPE'))
        max_forecasts = util.getlist(self.p.getraw('config','FCST_MAX_FORECAST'))
        self.check_model(model_templates, model_types, max_forecasts)

        lead_seq = util.getlistint(self.p.getstr('config', 'LEAD_SEQ'))
        for md in range(len(model_templates)):
            cur_model = [model_templates[md],model_types[md],max_forecasts[md]]
            for lead in lead_seq:
                task_info.lead = lead
                for var_info in var_list:
                    self.run_at_time_once(task_info, var_info, cur_model)


    def run_at_time_once(self, ti, v, cur_model):
        valid_time = ti.getValidTime()
        init_time = ti.getInitTime()
        grid_stat_base_dir = self.p.getstr('config', 'GRID_STAT_OUT_DIR')
        if self.p.getbool('config', 'LOOP_BY_INIT'):
            grid_stat_out_dir = os.path.join(grid_stat_base_dir,
                                     init_time, "grid_stat")
        else:
            grid_stat_out_dir = os.path.join(grid_stat_base_dir,
                                     valid_time, "grid_stat")
        fcst_level = v.fcst_level
        fcst_level_type = ""
        if(fcst_level[0].isalpha()):
            fcst_level_type = fcst_level[0]
            fcst_level = fcst_level[1:]
        obs_level = v.obs_level
        obs_level_type = ""
        if(obs_level[0].isalpha()):
            obs_level_type = obs_level[0]
            obs_level = obs_level[1:]            
        #model_type = self.p.getstr('config', 'MODEL_TYPE')
        model_type = cur_model[1]
        obs_dir = self.p.getstr('config', 'OBS_GRID_STAT_INPUT_DIR')
        obs_template = self.p.getraw('filename_templates',
                                     'OBS_GRID_STAT_INPUT_TEMPLATE')
        model_dir = self.p.getstr('config', 'FCST_GRID_STAT_INPUT_DIR')        
        config_dir = self.p.getstr('config', 'CONFIG_DIR')

        ymd_v = valid_time[0:8]
        if not os.path.exists(grid_stat_out_dir):
            os.makedirs(grid_stat_out_dir)

        # get model to compare
        model_path = self.find_model(ti.lead, init_time, fcst_level, cur_model)

        if model_path == "":
            print("ERROR: COULD NOT FIND FILE IN "+model_dir)
            return
        self.add_input_file(model_path)
        # TODO: Handle range of levels
        obsSts = sts.StringSub(self.logger,
                                  obs_template,
                                  valid=valid_time,
                                  init=init_time,
                                  level=str(obs_level.split('-')[0]).zfill(2))
        obs_file = obsSts.doStringSub()

        obs_path = os.path.join(obs_dir, obs_file)
        self.add_input_file(obs_path)
        self.set_param_file(self.p.getstr('config', 'GRID_STAT_CONFIG'))
        self.set_output_dir(grid_stat_out_dir)

        # set up environment variables for each grid_stat run
        # get fcst and obs thresh parameters
        # verify they are the same size

        fcst_str = "FCST_"+v.fcst_name+"_"+fcst_level+"_THRESH"
        obs_str = "OBS_"+v.obs_name+"_"+obs_level+"_THRESH"
        fcst_cat_thresh = ""
        obs_cat_thresh = ""
        fcst_threshs = []
        obs_threshs = []
        
        if self.p.has_option('config', fcst_str):
            fcst_threshs = util.getlistfloat(self.p.getstr('config', fcst_str))
            fcst_cat_thresh = "cat_thresh=[ "
            for fcst_thresh in fcst_threshs:
                fcst_cat_thresh += "gt"+str(fcst_thresh)+", "
            fcst_cat_thresh = fcst_cat_thresh[0:-2]+" ];"
            
        if self.p.has_option('config', obs_str):
            obs_threshs = util.getlistfloat(self.p.getstr('config', obs_str))
            obs_cat_thresh = "cat_thresh=[ "
            for obs_thresh in obs_threshs:
                obs_cat_thresh += "gt"+str(obs_thresh)+", "
            obs_cat_thresh = obs_cat_thresh[0:-2]+" ];"

        if len(fcst_threshs) != len(obs_threshs):
            self.logger.error("run_example: Number of forecast and "\
                              "observation thresholds must be the same")
            exit(1)

        # TODO: Allow NetCDF level with more than 2 dimensions i.e. (1,*,*)
        # TODO: Need to check data type for PROB fcst? non PROB obs?

        fcst_field = ""
        obs_field = ""
# TODO: change PROB mode to put all cat thresh values in 1 item        
        if self.p.getbool('config', 'FCST_IS_PROB'):
            for fcst_thresh in fcst_threshs:
                fcst_field += "{ name=\"PROB\"; level=\""+fcst_level_type + \
                              fcst_level.zfill(2) + "\"; prob={ name=\"" + \
                              v.fcst_name + \
                              "\"; thresh_lo="+str(fcst_thresh)+"; } },"
            for obs_thresh in obs_threshs:
                obs_field += "{ name=\""+v.obs_name+"_"+obs_level.zfill(2) + \
                             "\"; level=\"(*,*)\"; cat_thresh=[ gt" + \
                             str(obs_thresh)+" ]; },"
        else:
#            data_type = self.p.getstr('config', 'OBS_NATIVE_DATA_TYPE')
            obs_data_type = util.get_filetype(obs_path)
            model_data_type = util.get_filetype(model_path)
            if obs_data_type == "NETCDF":

              obs_field += "{ name=\"" + v.obs_name+"_" + obs_level.zfill(2) + \
                           "\"; level=\"(*,*)\"; "

            else:
              obs_field += "{ name=\""+v.obs_name + \
                            "\"; level=\"["+obs_level_type + \
                            obs_level.zfill(2)+"]\"; "

            if model_data_type == "NETCDF":
                fcst_field += "{ name=\""+v.fcst_name+"_"+fcst_level.zfill(2) + \
                              "\"; level=\"(*,*)\"; "
            else:
                fcst_field += "{ name=\""+v.fcst_name + \
                              "\"; level=\"["+fcst_level_type + \
                              fcst_level.zfill(2)+"]\"; "

            fcst_field += fcst_cat_thresh+" },"

#            obs_field += "{ name=\"" + v.obs_name+"_" + obs_level.zfill(2) + \
#                         "\"; level=\"(*,*)\"; "
            obs_field += obs_cat_thresh+ " },"

        # remove last comma and } to be added back after extra options
        fcst_field = fcst_field[0:-2]
        obs_field = obs_field[0:-2]

        fcst_field += v.fcst_extra+"}"
        obs_field += v.obs_extra+"}"

        ob_type = self.p.getstr('config', "OB_TYPE")
        verif_polys = util.getlist(self.p.getstr('config',"VERIFICATION_POLY"))
        verif_poly = "["
        for vp in verif_polys:
            verif_poly += "\""+vp+"\", "
        verif_poly = os.path.expandvars(verif_poly[0:-2]+"]")

        self.add_env_var("MODEL", model_type)
        self.add_env_var("FCST_VAR", v.fcst_name)
        self.add_env_var("OBS_VAR", v.obs_name)
        # TODO: Change ACCUM to LEVEL in GridStatConfig_MEAN/PROB and here
        self.add_env_var("ACCUM", v.fcst_level)
        self.add_env_var("OBTYPE", ob_type)
        self.add_env_var("CONFIG_DIR", config_dir)
        self.add_env_var("FCST_FIELD", fcst_field)
        self.add_env_var("OBS_FIELD", obs_field)
        self.add_env_var("MET_VALID_HHMM", valid_time[4:8])
        self.add_env_var("VERIF_POLY",verif_poly)
        cmd = self.get_command()

        self.logger.debug("")
        self.logger.debug("ENVIRONMENT FOR NEXT COMMAND: ")
        self.print_env_item("MODEL")
        self.print_env_item("FCST_VAR")
        self.print_env_item("OBS_VAR")
        self.print_env_item("ACCUM")
        self.print_env_item("OBTYPE")
        self.print_env_item("CONFIG_DIR")
        self.print_env_item("FCST_FIELD")
        self.print_env_item("OBS_FIELD")
        self.print_env_item("MET_VALID_HHMM")  
        self.print_env_item("VERIF_POLY")
        self.logger.debug("")
        self.logger.debug("COPYABLE ENVIRONMENT FOR NEXT COMMAND: ")
        self.print_env_copy(["MODEL", "FCST_VAR", "OBS_VAR",
                             "ACCUM", "OBTYPE", "CONFIG_DIR",
                             "FCST_FIELD", "OBS_FIELD",
                             "MET_VALID_HHMM"])
        self.logger.debug("")
        cmd = self.get_command()
        if cmd is None:
            print("ERROR: grid_stat could not generate command")
            return
        self.logger.info("")
        self.build()
        self.clear()
