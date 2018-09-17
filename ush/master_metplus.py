#!/usr/bin/env python
from __future__ import print_function

'''!@namespace master_metplus
Main script the processes all the tasks in the PROCESS_LIST
'''

import os
import sys
import logging
import getopt
import config_launcher
import time
import datetime
import calendar
import produtil.setup
# from produtil.run import run
import met_util as util
import config_metplus

from pcp_combine_wrapper import PcpCombineWrapper
from grid_stat_wrapper import GridStatWrapper
from regrid_data_plane_wrapper import RegridDataPlaneWrapper
from tc_pairs_wrapper import TcPairsWrapper
from extract_tiles_wrapper import ExtractTilesWrapper
from series_by_lead_wrapper import SeriesByLeadWrapper
from series_by_init_wrapper import SeriesByInitWrapper
from stat_analysis_wrapper import StatAnalysisWrapper
from make_plots_wrapper import MakePlotsWrapper
from mode_wrapper import ModeWrapper
from usage_wrapper import UsageWrapper
from command_builder import CommandBuilder
from tcmpr_plotter_wrapper import TCMPRPlotterWrapper
# cyclone plotter should be commented out when committed
from cyclone_plotter_wrapper import CyclonePlotterWrapper
from pb2nc_wrapper import PB2NCWrapper
from point_stat_wrapper import PointStatWrapper
from tc_stat_wrapper import TcStatWrapper
from gempak_to_cf_wrapper import GempakToCFWrapper

'''!@var logger
The logging.Logger for log messages
'''
logger = None


def main():
    """!Main program.

    Master MET+ script that invokes the necessary Python scripts
    to perform various activities, such as series analysis."""

    # Job Logger
    produtil.log.jlogger.info('Top of master_metplus')

    # Used for logging and usage statment
    cur_filename = sys._getframe().f_code.co_filename
    cur_function = sys._getframe().f_code.co_name

    # Setup Task logger, Until Conf object is created, Task logger is
    # only logging to tty, not a file.
    logger = logging.getLogger('master_metplus')
    logger.info('logger Top of master_metplus.')

    # Parse arguments, options and return a config instance.
    p = config_metplus.setup(filename=cur_filename)

    # NOW we have a conf object p, we can now get the logger
    # and set the handler to write to the LOG_METPLUS
    # TODO: Frimel setting up logger file handler.
    # Setting up handler i.e util.get_logger should be moved to
    # the setup wrapper and encapsulated in the config object.
    # than you would get it this way logger=p.log(). The config
    # object has-a logger we want.
    logger = util.get_logger(p)
    # logger.info('Top of master_metplus after conf file setup.')

    # This is available in each subprocess from os.system BUT
    # we also set it in each process since they may be called stand alone.
    os.environ['MET_BASE'] = p.getdir('MET_BASE')

    # Use config object to get the list of processes to call
    process_list = util.getlist(p.getstr('config', 'PROCESS_LIST'))

    # Keep this comment.
    # When running commands in the process_list, reprocess the
    # original command line using (item))[sys.argv[1:]].
    #
    # You could call each task (ie. run_tc_pairs.py) without any args since
    # the final METPLUS_CONF file was just created from config_metplus.setup,
    # and each task, also calls setup, which use an existing final conf
    # file over command line args.
    #
    # both work ...
    # Note: Using (item))sys.argv[1:], is preferable since
    # it doesn't depend on the conf file existing.
    processes = []
    for item in process_list:
        try:
            logger = p.log(item)
            command_builder = getattr(sys.modules[__name__], item + "Wrapper")(
                p, logger)
        except AttributeError:
            raise NameError("Process %s doesn't exist" % item)
            exit()

        processes.append(command_builder)

    if p.getstr('config', 'LOOP_METHOD') == "processes":
        for process in processes:
            # referencing using repr(process.app_name) in
            # log since it may be None,
            # if not set in the command builder subclass' contsructor,
            # and no need to generate an exception because of that.
            produtil.log.postmsg('master_metplus Calling run_all_times '
                                 'in: %s wrapper.' % repr(process.app_name))
            process.run_all_times()

    elif p.getstr('config', 'LOOP_METHOD') == "times":
        use_init = p.getbool('config', 'LOOP_BY_INIT', True)
        if use_init:
            time_format = p.getstr('config', 'INIT_TIME_FMT')
            start_t = p.getstr('config', 'INIT_BEG')
            end_t = p.getstr('config', 'INIT_END')
            time_interval = p.getint('config', 'INIT_INC')
        else:
            time_format = p.getstr('config', 'VALID_TIME_FMT')
            start_t = p.getstr('config', 'VALID_BEG')
            end_t = p.getstr('config', 'VALID_END')
            time_interval = p.getint('config', 'VALID_INC')

        if time_interval < 60:
            print("ERROR: time_interval parameter must be "
                  "greater than 60 seconds")
            exit(1)

        loop_time = calendar.timegm(time.strptime(start_t, time_format))
        end_time = calendar.timegm(time.strptime(end_t, time_format))
        while loop_time <= end_time:
            run_time = time.strftime("%Y%m%d%H%M", time.gmtime(loop_time))
            logger.info("****************************************")
            logger.info("* RUNNING MET+")
            if use_init:
                logger.info("*  at init time: " + run_time)
            else:
                logger.info("*  at valid time: " + run_time)
            logger.info("****************************************")
            for process in processes:
                # Set valid time to -1 if using init and vice versa
                if use_init:
                    process.run_at_time(run_time, -1)
                else:
                    process.run_at_time(-1, run_time)
                process.clear()

            loop_time += time_interval

    else:
        print("ERROR: Invalid LOOP_METHOD defined. " + \
              "Options are processes, times")
        exit()
    exit()

    # TODO - remove this, I don't think this is being used.
    # If removing, also remove import produtil.run
    # If using ... than the run(cmd) will need to be correctly called.
    # for item in process_list:
    #
    #     cmd_shell = cmd.to_shell()
    #     logger.info("INFO | [" + cur_filename + ":" +
    #                 cur_function + "] | " + "Running: " + cmd_shell)
    #     ret = run(cmd)
    #     if ret != 0:
    #         logger.error("ERROR | [" + cur_filename + ":" +
    #                     cur_function + "] | " + "Problem executing: " +
    #                     cmd_shell)
    #         exit(0)


if __name__ == "__main__":
    try:
        # If jobname is not defined, in log it is 'NO-NAME'
        if 'JLOGFILE' in os.environ:
            produtil.setup.setup(send_dbn=False, jobname='run-METplus',
                                 jlogfile=os.environ['JLOGFILE'])
        else:
            produtil.setup.setup(send_dbn=False, jobname='run-METplus')
        produtil.log.postmsg('master_metplus is starting')

        main()
        produtil.log.postmsg('master_metplus completed')
    except Exception as e:
        produtil.log.jlogger.critical(
            'master_metplus  failed: %s' % (str(e),), exc_info=True)
        sys.exit(2)
