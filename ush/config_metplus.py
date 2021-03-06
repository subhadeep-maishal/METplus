#!/usr/bin/env python
from __future__ import print_function

# This would become the exmetplus_launcher

##@namespace config_metplus
# The initial METplus configure script for parsing the command line
# options, arguments and setting up the METPLUS_CONF file.  
#
# This module setup() function should be called at the start of each task to 
# setup a configuration object used by all the processing tasks.
# Each task that calls this MUST have run produtil.setup

# This module can be called directly as a  command on the command line as well.
import os
import sys
import logging

import produtil.setup
import getopt
import config_launcher

##@var __all__
# All symbols exported by "from config_metplus import *"
__all__ = ['usage', 'setup']

##@var logger
# The logging.Logger for log messages
logger = None


def usage(filename=None,logger=None):
    """! How to call this function.
    @param filename the filename of the calling module.
    @param logger a logging.logger for log messages"""

    if filename:
        filename=os.path.basename(filename)

    if logger:
        logger.critical('Invalid arguments to %s.  Exiting.'%(filename))

    # Note: runtime option is not being used. remove it ?
    # -r|--runtime <arg0>     Specify initialization time to process
    print ('''
Usage: %s [ -c /path/to/additional/conf_file]...[] [options]
    -c|--config <arg0>      Specify custom configuration file to use
    -h|--help               Display this usage statement
    
Optional arguments: [options]
section.option=value -- override conf options on the command line
/path/to/parmfile.conf -- additional conf files to parse

'''%(filename))
    sys.exit(2)

def setup(filename=None,logger=None):
    """!The METplus setup function.
    @param filename the filename of the calling module.
    @param logger a logging.logger for log messages

    The setup function that process command line options
    and arguements and returns a configuration object."""

    # Used for logging and usage statment
    if filename is None:
        cur_filename = sys._getframe().f_code.co_filename
        cur_function = sys._getframe().f_code.co_name
        filename = cur_filename

    # Setup Task logger, Until a Conf object is created, Task logger is
    # only logging to tty, not a file.
    if logger is None:
        logger = logging.getLogger('metplus')

    logger.info('Starting METplus configuration setup.')

    # Currently METplus command line options are for additional conf file.
    # Note options are NOT arguments. ie. -c opt arg arg arg
    # command line options. -c <conf_file_X>.
    # We will handle them the way produtil handles conf files
    # which are ultimately passed as arguments.

    # if option is followed by : or = indicates option requires an argument
    short_opts = "c:r:h"
    # Note: r: runtime= option is not being used. remove it ?
    long_opts = ["config=",
                 "runtime=",
                 "help"]

    # All command line input, get options and arguments
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as err:
        #usage('SCRIPT IS EXITING DUE TO UNRECOGNIZED COMMAND LINE OPTION'
        print(str(err))        
        usage(filename,logger)

    logger.info('All OPTS and ARGS: %s %s',opts, args)

    # notice -h does not require an argument so its argument is ''
    # opts=[('-h',''),('-c','path/to/file.conf')]

    opts_conf_files = list()
    opts_conf_file = None
    for k, v in opts:
        if k in ('-c', '--config'):
            opts_conf_files.extend(v.split(","))
        elif k in ('-r', '--runtime'):
            # If using these they should be added to conf file
            # via additional options on the command line
            # config.end_time= and than accessed via the config object.
            start_time = v
            end_time = v
        elif k in ('-h', '--help'):
            if logger:
                logger.info('Help, printing Usage statement')
            usage(filename=filename)
        else:
            assert False, "UNHANDLED OPTION"

    opts_conf_list = list()
    for opts_conf_file in opts_conf_files:
        opts_conf_list.append(config_launcher.set_conf_file_path(opts_conf_file))
    # append args to opts conf_list, to maintain the same conf
    # file order from command line, when confs may be space seperated.
    # ie. -c conf1 -c conf2 conf3 would become
    # args=[conf3] and opts=[conf1, conf2]
    # opts_conf_list = [conf1, conf2, conf3]
    opts_conf_list.extend(args)
    args = opts_conf_list

    # parm, is path to parm directory
    # infiles, list of input conf files to be read and processed
    # moreopt, dictionary of conf file settings, passed in from command line.
    if not args:
        args = None
    (parm, infiles, moreopt) = \
        config_launcher.parse_launch_args(args, usage, filename, logger)

    # Currently metplus is not handling cycle.
    # Therefore can not use conf.timestrinterp and
    # some conf file settings ie. {[a|f]YMDH} time settings.
    cycle = None
    conf = config_launcher.launch(infiles, moreopt, cycle=cycle)
    #conf.sanity_check()

    logger.info('Completed METplus configuration setup.')

    return conf


# You can run this module from the command line, that is  __main__
# However, this module is intended to be imported and run via setup function.
if __name__ == "__main__":
    try:
        # If jobname is not defined, in log it is 'NO-NAME'
        if 'JLOGFILE' in os.environ:
            produtil.setup.setup(send_dbn=False, jobname='run-config_metplus',
                                 jlogfile=os.environ['JLOGFILE'])
        else:
            produtil.setup.setup(send_dbn=False, jobname='run-config_metplus')
        produtil.log.postmsg('config_metplus is starting')

        setup()
        produtil.log.postmsg('config_metplus completed')
    except Exception as e:
        produtil.log.jlogger.critical(
            'config_metplusfailed: %s' % (str(e),), exc_info=True)
        sys.exit(2)

