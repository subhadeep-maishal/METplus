#!/usr/bin/env python

"""!@namespace ExtraTropicalCyclonePlotter
A Python class that generates plots of extra tropical cyclone forecast data,
 replicating the NCEP tropical and extra tropical cyclone tracks and
 verification plots http://www.emc.ncep.noaa.gov/mmb/gplou/emchurr/glblgen/
"""

from __future__ import print_function
import os
import time
import datetime
import re
import sys
import collections
# pylint:disable=import-error
# numpy, matplotlib and mpl_toolkits are not part of the standard Python
# library
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import met_util as util
import produtil.setup
import config_metplus
from command_builder import CommandBuilder


class CyclonePlotterWrapper(CommandBuilder):
    """! Generate plots of extra tropical storm forecast tracks.
        Reads input from ATCF files generated from MET TC-Pairs
    """

    def __init__(self, p, logger):
        # pylint:disable=redefined-outer-name
        super(CyclonePlotterWrapper, self).__init__(p, logger)
        if logger is None:
            self.logger = util.get_logger(self.p)
        else:
            self.logger = logger
        self.app_path = os.path.join(p.getdir('MET_INSTALL_DIR'),
                                     'bin/tc_pairs')
        self.app_name = os.path.basename(self.app_path)
        self.input_data = p.getdir('CYCLONE_INPUT_DIR')
        self.output_dir = p.getdir('CYCLONE_OUT_DIR')
        self.init_date = p.getstr('config', 'CYCLONE_INIT_DATE')
        self.init_hr = p.getstr('config', 'CYCLONE_INIT_HR')
        self.projection = p.getstr('config', 'CYCLONE_PROJECTION')
        self.model = p.getstr('config', 'CYCLONE_MODEL')
        self.title = p.getstr('config', 'CYCLONE_PLOT_TITLE')
        self.gen_ascii = p.getbool('config', 'GENERATE_TRACK_ASCII')
        # Create a set to keep track of unique storm_ids for each track file.
        self.unique_storm_id = set()
        # Data structure to separate data based on storm id.
        self.storm_id_dict = {}
        # Data/info which we want to retrieve from the track files.
        self.columns_of_interest = ['AMODEL', 'STORM_ID', 'BASIN', 'INIT',
                                    'LEAD', 'VALID', 'ALAT', 'ALON', 'BLAT',
                                    'BLON', 'AMSLP', 'BMSLP']
        self.llcrnrlat = p.getfloat('config', 'CYCLONE_LLCRNRLAT')
        self.llcrnrlon = p.getfloat('config', 'CYCLONE_LLCRNRLON')
        self.urcrnrlat = p.getfloat('config', 'CYCLONE_URCRNRLAT')
        self.urcrnrlon = p.getfloat('config', 'CYCLONE_URCRNRLON')
        self.resolution = p.getstr('config', 'CYCLONE_RESOLUTION')
        self.circle_marker = p.getint('config', 'CIRCLE_MARKER_SIZE')
        self.cross_marker = p.getint('config', 'CROSS_MARKER_SIZE')

    def run_all_times(self):
        """! Calls the defs needed to create the cyclone plots
             run_all_times() is required by CommandBuilder.

        """
        self.retrieve_data()
        self.create_plot()

    def retrieve_data(self):
        """! Retrieve data from track files and return the min and max lon.
            Returns:
               None
        """
        self.logger.debug("Begin retrieving data...")
        all_tracks_list = []

        # Store the data in the track list.
        if os.path.isdir(self.input_data):
            self.logger.debug("Generate plot for all files in the directory" +
                              self.input_data)
            # Get the list of all files (full file path) in this directory
            all_init_files = util.get_files(self.input_data, ".*.tcst",
                                            self.logger)

            for init_file in all_init_files:
                # Ignore empty files
                if os.stat(init_file).st_size == 0:
                    self.logger.info("Empty file")
                    continue

                # logger.info("Consider all files under directory" +
                #  init_file + " with " + " init time (ymd): " +
                # self.init_date + " and lead time (hh):" + self.lead_hr)
                with open(init_file, 'r') as infile:
                    self.logger.debug("Parsing file " + init_file)

                    # Extract information from the header, which is
                    # the first line.
                    header = infile.readline()
                    # print("header: {}".format(header))
                    column_indices = self.get_columns_and_indices(header)

                    # For the remaining lines of this file,
                    # retrieve information from each row:
                    # lon, lat, init time, lead hour, valid time,
                    # model name, mslp, and basin.
                    # NOTE: Some of these aren't used until we fully
                    # emulate Guang Ping's plots.
                    for line in infile:
                        track_dict = {}
                        col = line.split()
                        lat = col[column_indices['ALAT']]
                        lon = col[column_indices['ALON']]
                        init_time = col[column_indices['INIT']]
                        fcst_lead_hh = \
                            str(col[column_indices['LEAD']]).zfill(3)
                        model_name = col[column_indices['AMODEL']]
                        valid_time = col[column_indices['VALID']]
                        storm_id = col[column_indices['STORM_ID']]

                        # Not needed until support for regional plots
                        # is implemented.
                        # mslp = col[column_indices['AMSLP']]
                        # basin = col[column_indices['BASIN']]

                        # Check for NA values in lon and lat, skip to
                        # next line in file if 'NA' is encountered.
                        if lon == 'NA' or lat == 'NA':
                            continue
                        else:
                            track_dict['lon'] = float(lon)
                            track_dict['lat'] = float(lat)

                        # If the lead hour is 'NA', skip to next line.
                        # The track data was very likely generated with
                        # TC-Stat set to match-pairs set to True.
                        lead_hr = self.extract_lead_hr(fcst_lead_hh)
                        if lead_hr == 'NA':
                            continue

                        # Check that the init date, init hour
                        # and model name are what the user requested.
                        init_ymd, init_hh = \
                            self.extract_date_and_time_from_init(init_time)

                        if init_ymd == self.init_date and \
                                init_hh == self.init_hr:
                            if model_name == self.model:
                                # Check for the requested model,
                                # if the model matches the requested
                                # model name, then we have all the
                                # necessary information to continue.
                                # Store all data in dictionary
                                track_dict['fcst_lead_hh'] = fcst_lead_hh
                                track_dict['init_time'] = init_time
                                track_dict['model_name'] = model_name
                                track_dict['valid_time'] = valid_time
                                track_dict['storm_id'] = storm_id

                                # Identify the 'first' point of the
                                # storm track.  If the storm id is novel, then
                                # retrieve the date and hh from the valid time
                                if storm_id in self.unique_storm_id:
                                    track_dict['first_point'] = False
                                    track_dict['valid_dd'] = ''
                                    track_dict['valid_hh'] = ''
                                else:
                                    self.unique_storm_id.add(storm_id)
                                    # Since this is the first storm_id with
                                    # a valid value for lat and lon (ie not
                                    # 'NA'), this is the first track point
                                    # in the storm track and will be
                                    # labelled with the corresponding
                                    # date/hh z on the plot.
                                    valid_match = \
                                        re.match(r'[0-9]{6}([0-9]{2})_' +
                                                 '([0-9]{2})[0-9]{4}',
                                                 track_dict['valid_time'])
                                    if valid_match:
                                        valid_dd = valid_match.group(1)
                                        valid_hh = valid_match.group(2)
                                    else:
                                        # Shouldn't get here if this is
                                        # the first point of the track.
                                        valid_dd = ''
                                        valid_hh = ''
                                    track_dict['first_point'] = True
                                    track_dict['valid_dd'] = valid_dd
                                    track_dict['valid_hh'] = valid_hh

                                # Identify points based on valid time (hh).
                                # Useful for plotting later on.
                                valid_match = \
                                    re.match(r'[0-9]{8}_([0-9]{2})[0-9]{4}',
                                             track_dict['valid_time'])
                                if valid_match:
                                    # Since we are only interested in 00,
                                    # 06, 12, and 18 hr times...
                                    valid_hh = valid_match.group(1)

                                if valid_hh == '00' or valid_hh == '12':
                                    track_dict['lead_group'] = '0'
                                elif valid_hh == '06' or valid_hh == '18':
                                    track_dict['lead_group'] = '6'
                                else:
                                    # To gracefully handle any hours other
                                    # than 0, 6, 12, or 18
                                    track_dict['lead_group'] = ''

                                all_tracks_list.append(track_dict)

                                # For future work, support for MSLP when
                                # generating regional plots-
                                # implementation goes here...
                                # Finishing up, do any cleaning up,
                                # logging, etc.
                                self.logger.info("INFO: All criteria met, " +
                                                 "saving track data init " +
                                                 track_dict['init_time'] +
                                                 " lead " +
                                                 track_dict['fcst_lead_hh'] +
                                                 " lon " +
                                                 str(track_dict['lon']) +
                                                 " lat " +
                                                 str(track_dict['lat']))

                            else:
                                # Not the requested model, move to next
                                # row of data
                                continue

                        else:
                            # Not the requested init ymd move to next
                            # row of data
                            continue

                # Now separate the data based on storm id.
                for cur_unique in self.unique_storm_id:
                    cur_storm_list = []
                    for cur_line in all_tracks_list:
                        if cur_line['storm_id'] == cur_unique:
                            cur_storm_list.append(cur_line)
                        else:
                            # Continue to next line in all_tracks_list
                            continue

                    # Create the storm_id_dict, which is the data
                    # structure used to separate the storm data based on
                    # storm id.
                    self.storm_id_dict[cur_unique] = cur_storm_list

        else:
            self.logger.error("Input directory expected, check " +
                              "configuration file and try again.")
            sys.exit(1)

    def get_columns_and_indices(self, header):
        """ Parse the header for the columns of interest and store the
            information in a dictionary where the key is the column name
            and value is the index/column number.
            Returns:
                column_dict:  A dictionary containing the column name
                              and its index
        """

        all_columns = header.split()
        column_dict = {}

        # Retrieve the index number of the column of interest in the header.
        for col in self.columns_of_interest:
            index = all_columns.index(col)
            column_dict[col] = index
        return column_dict

    @staticmethod
    def extract_date_and_time_from_init(init_time_str):
        """ Extract and return the YYYYMMDD portion and the
            hh portion from the init time taken from the .tcst file.
        """
        match_ymd = re.match(r'([0-9]{8}).*', init_time_str)
        match_hh = re.match(r'[0-9]{8}_([0-9]{2,3})[0-9]{4}', init_time_str)
        # pylint:disable=no-else-return
        # Explicitly return None if no match is found
        if match_ymd and match_hh:
            return match_ymd.group(1), match_hh.group(1)
        else:
            return None

    @staticmethod
    def extract_lead_hr(lead_str):
        """ Extract and return the lead hours from the hhmmss lead string.
        """
        match = re.match(r'([0-9]{2,3})[0-9]{4}', str(lead_str))
        if match:
            return match.group(1)

    def create_plot(self):
        """! Create the plot, using Cartopy.

        """

        # Use PlateCarree projection for now
        #use central meridian for central longitude
        cm_lon = 180
        ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=cm_lon))
        # ax = plt.axes(projection=ccrs.LambertCylindrical(central_longitude=0.0))

        # Add land, coastlines, and ocean
        ax.add_feature(cfeature.LAND)
        ax.coastlines()
        ax.add_feature(cfeature.OCEAN)

        # Add grid lines for longitude and latitude
        ax.gridlines(draw_labels=False, xlocs=[180, -180])
        gl = ax.gridlines(crs=ccrs.PlateCarree(central_longitude=0.0),
                          draw_labels=True, linewidth=1, color='gray',
                          alpha=0.5, linestyle='--')
        gl.xlabels_top = False
        gl.ylabels_left = False
        gl.xlines = True
        gl.xlocator = mticker.FixedLocator(
            [ -180,-140, -100, -60, -20, 20, 60, 100, 140, 180])
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = {'size': 9, 'color': 'blue'}
        gl.xlabel_style = {'color': 'black', 'weight': 'normal'}

        # Plot title
        plt.title(self.title + "\nFor forecast with initial time = " +
                  self.init_date)

        # Create the NCAR watermark with a timestamp
        # This will appear in the bottom left corner of the plot, below
        # the legend.  NOTE: The timestamp is in the user's local time zone
        # and not in UTC time.
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime(
            '%Y-%m-%d %H:%M:%S')
        watermark = 'DTC METplus\nplot created at: ' + st
        # plt.text(1, -180, watermark, fontsize=8, alpha=0.25)
        plt.text(-180, -170, watermark, fontsize=5, alpha=0.25)

        # Make sure the output directory exists, and create it if it doesn't.
        util.mkdir_p(self.output_dir)

        # Iterate over each unique storm id in self.storm_id_dict and
        # set the marker, marker size, and annotation
        # before drawing the line and scatter plots.

        # If requested, create an ASCII file with the tracks that are going to
        # be plotted.  This is useful to debug or verify that what you
        # see on the plot is what is expected.
        ascii_track_parts = [self.init_date, '_', self.projection, '.txt']
        ascii_track_output_name = ''.join(ascii_track_parts)
        plot_filename = os.path.join(self.output_dir, ascii_track_output_name)
        ascii_track_file = open(plot_filename, 'w')

        # Use counters to set the labels for the legend. Since we don't
        # want repetitions in the legend, do this for a select number
        # of points.
        circle_counter = 0
        plus_counter = 0
        dummy_counter = 0

        # If requested, create an ASCII file with the tracks that are going to
        # be plotted.  This is useful to debug or verify that what you
        # see on the plot is what is expected.
        ascii_track_parts = [self.init_date, '_', self.projection, '.txt']
        ascii_track_output_name = ''.join(ascii_track_parts)
        plot_filename = os.path.join(self.output_dir, ascii_track_output_name)
        ascii_track_file = open(plot_filename, 'w')

        for cur_storm_id in self.unique_storm_id:
            # Lists used in creating each storm track.
            cyclone_points = []
            lon = []
            lat = []
            marker_list = []
            size_list = []
            anno_list = []

            # For this storm id, get a list of all data (corresponding
            # to lines/rows in the tcst data file).
            track_info_list = self.storm_id_dict[cur_storm_id]
            # pylint:disable=len-as-condition
            # if len(track_info_list) == 0:
            if not track_info_list:
                self.logger.error("Empty track list, no data extracted " +
                                  "from track files, exiting.")
                sys.exit(1)

            for track in track_info_list:
                # For now, all the marker symbols will be one color.
                color_list = ['red' for _ in range(0, len(track_info_list))]

                lon.append(float(track['lon']))
                lat.append(float(track['lat']))

                # Differentiate between the forecast lead "groups",
                # i.e. 0/12 vs 6/18 hr and
                # assign the marker symbol and size.
                if track['lead_group'] == '0':
                    marker = 'o'
                    marker_list.append(marker)
                    marker_size = self.circle_marker
                    size_list.append(marker_size)
                    label = "Indicates a position at 00 or 12 UTC"

                elif track['lead_group'] == '6':
                    marker = '+'
                    marker_list.append(marker)
                    marker_size = self.cross_marker
                    size_list.append(marker_size)
                    label = "\nIndicates a position at 06 or 18 UTC\n"

                # Determine the first point, needed later to annotate.
                # pylint:disable=invalid-name
                dd = track['valid_dd']
                hh = track['valid_hh']
                if dd and hh:
                    date_hr_str = dd + '/' + hh + 'z'
                    anno_list.append(date_hr_str)
                else:
                    date_hr_str = ''
                    anno_list.append(date_hr_str)

                # Write to the ASCII track file, if requested
                if self.gen_ascii:
                    line_parts = ['model_name: ', track['model_name'], '   ',
                                  'storm_id: ', track['storm_id'], '   ',
                                  'init_time: ', track['init_time'], '   ',
                                  'valid_time: ', track['valid_time'], '   ',
                                  'lat: ', str(track['lat']), '   ',
                                  'lon: ', str(track['lon']), '   ',
                                  'lead_group: ', track['lead_group'], '   ',
                                  'first_point:', str(track['first_point'])]
                    line = ''.join(line_parts)
                    ascii_track_file.write(line)
                    ascii_track_file.write('\n')

            # Create ascatter plot to add
            # the appropriate marker symbol to the forecast
            # hours corresponding to 6/18 hours.

            # map.plot(x, y, color='red', linestyle='-')

            # Annotate the first point of the storm track
            for anno, adj_lon, adj_lat in zip(anno_list, lon, lat):
                # x, y = map(adj_lon, adj_lat)
                # Annotate the first point of the storm track by
                # overlaying the annotation text over all points (all but
                # one will have text).
                plt.annotate(anno, xy=(adj_lon, adj_lat), xytext=(2, 2),
                             textcoords='offset points', fontsize=11,
                             color='red')

            # Generate the scatterplot, where the 6/18 Z forecast times
            # are labelled with a '+'
            for adj_lon, adj_lat, symbol, sz, colours in zip(lon, lat,
                                                             marker_list,
                                                             size_list,
                                                             color_list):
                # red line, red +, red o, marker sizes are recognized,
                # no outline color of black for 'o'
                # plt.scatter(x, y, s=sz, c=colours, edgecolors=colours,
                # facecolors='none', marker=symbol, zorder=2)
                # Solid circle, just like the EMC NCEP plots
                # Separate the first two points so we can generate the legend
                if circle_counter == 0 or plus_counter == 0:
                    if symbol == 'o':
                        plt.scatter(adj_lon, adj_lat, s=sz, c=colours,
                                    edgecolors=colours, facecolors=colours,
                                    marker='o', zorder=2,
                                    label="Indicates a position " +
                                    "at 00 or 12 UTC")
                        plt.plot(adj_lon, adj_lat, linestyle='-')
                        circle_counter += 1
                    elif symbol == '+':
                        plt.scatter(adj_lon, adj_lat, s=sz, c=colours,
                                    edgecolors=colours, facecolors=colours,
                                    marker='+', zorder=2,
                                    label="\nIndicates a position at 06 or " +
                                    "18 UTC\n")
                        plus_counter += 1

                else:
                    # Set the legend for additional text using a
                    # dummy scatter point
                    if dummy_counter == 0:
                        plt.scatter(0, 0, zorder=2, marker=None, c='',
                                    label="Date (dd/hhz) is the first " +
                                    "time storm was able to be tracked " +
                                    "in model")
                        dummy_counter += 1
                    plt.scatter(adj_lon, adj_lat, s=sz, c=colours, edgecolors=colours,
                                facecolors=colours, marker=symbol, zorder=2)


        # Draw the legend on the plot
        # If you wish to have the legend within the plot:
        # plt.legend(loc='lower left', prop={'size':5}, scatterpoints=1)
        # The legend is outside the plot, below the x-axis to
        # avoid obscuring any storm tracks in the Southern
        # Hemisphere.
        # ax.legend(loc='lower left', bbox_to_anchor=(-0.03, -0.5),
        #           fancybox=True, shadow=True, scatterpoints=1,
        #           prop={'size': 6})
        ax.legend(loc='lower left', bbox_to_anchor=(-0.01, -0.4),
                  fancybox=True, shadow=True, scatterpoints=1,
                  prop={'size': 6})

        # Write the plot to the output directory
        out_filename_parts = [self.init_date, '_', self.projection, '.png']
        output_plot_name = ''.join(out_filename_parts)
        plot_filename = os.path.join(self.output_dir, output_plot_name)
        plt.savefig(plot_filename)

        # Close the ASCII track file, if generated
        if self.gen_ascii:
            ascii_track_file.close()

        # Plot data onto axes
        plt.show()


    @staticmethod
    def set_lead_group(track_dict, init_hh):
        """! Sets the position indicator key to 0 if init hour is 0 or 12,
        and 6 if init hour is 6 or 18.  This is used to determine which
        symbol to use, a '+' or 'o' when plotting track points."""
        if init_hh == '00' or init_hh == '12':
            track_dict['position_indicator'] = '0'
        elif init_hh == '06' or init_hh == '18':
            track_dict['position_indicator'] = '6'

    @staticmethod
    def rescale_lon(lon):
        """! Rescales longitude, using the same logic employed by MET."""
        if float(lon) < 0.:
            adj_lon = lon + 360.
        elif float(lon) > 180.:
            adj_lon = lon - 360.
        else:
            adj_lon = lon

        return adj_lon


if __name__ == "__main__":
    try:
        if 'JLOGFILE' in os.environ:
            produtil.setup.setup(send_dbn=False,
                                 jobname='CyclonePlotter',
                                 jlogfile=os.environ['JLOGFILE'])
        else:
            produtil.setup.setup(send_dbn=False,
                                 jobname='CyclonePlotter')
        produtil.log.postmsg('CyclonePlotter is starting')
        # pylint:disable=invalid-name
        p = config_metplus.setup()
        if 'MET_BASE' not in os.environ:
            os.environ['MET_BASE'] = p.getdir('MET_BASE')

        # Request data extraction and plot generation.
        # pylint:disable=invalid-name
        cyclone = CyclonePlotterWrapper(p, None)
        cyclone.run_all_times()
        produtil.log.postmsg('CyclonePlotter completed')

    except Exception as e:
        produtil.log.jlogger.critical('CyclonePlotter failed: %s'
                                      % (str(e),), exc_info=True)
        sys.exit(2)
