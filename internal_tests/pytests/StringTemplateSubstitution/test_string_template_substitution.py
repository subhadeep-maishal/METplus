#!/usr/bin/env python

from __future__ import print_function

import pytest
from string_template_substitution import StringSub
from string_template_substitution import StringExtract
import logging


def test_cycle_hour():
    cycle_string = "00"
    valid_string = "20180103"
    logger = logging.getLogger("dummy")
    templ = "prefix.{valid?fmt=%Y%m%d}.tm{cycle?fmt=%H}"
    ss = StringSub(logger, templ, valid=valid_string, cycle=cycle_string)
    expected_hours = int(0)
    assert (ss.cycle_time_hours == expected_hours)


def test_offset_hour():
    logger = logging.getLogger("dummy")
    expected_hour = int(3)
    offset = "03"
    templ = "prefix.{valid?fmt=%Y%m%d}.tm{offset?fmt=%H}"
    ss = StringSub(logger, templ, offset=offset)
    assert (ss.offset_hour == expected_hour)


@pytest.mark.parametrize(
    'key, value', [
        ('00', '20180103060000'),
        ('03', '20180103030000'),
        ('06', '20180103000000'),
        ('72', '20171231060000')
    ]
)
def test_calc_valid_for_prepbufr(key, value):
    # Verify that the previous day is correctly calculated when
    # the negative_offset_hour > cycle_hour
    cycle_hour = "00"
    init_string = "2018010306"
    logger = logging.getLogger("dummy")
    templ = "prefix.{valid?fmt=%Y%m%d%H}.tm{cycle?fmt=%H}z.tm{" \
        "offset?fmt=%H}.nc"

    ss = StringSub(logger, templ, init=init_string, cycle=cycle_hour,
               offset=key)
    valid_time = ss.calc_valid_for_prepbufr()
    assert (valid_time == value)


def test_gdas_substitution():
    # Test that the string template substitution works correctly for GDAS
    # prepbufr files, which do not make use of the cycle hour or the offset
    # to generate the valid time.
    valid_string = "2018010411"
    logger = logging.getLogger("testing")
    templ = "prepbufr.gdas.{valid?fmt=%Y%m%d%H}.nc"
    expected_filename = 'prepbufr.gdas.' + valid_string + '.nc'
    ss = StringSub(logger, templ, valid=valid_string)
    filename = ss.doStringSub()
    assert(filename == expected_filename)

@pytest.mark.parametrize(
    'key, value', [
        ('38', 'prepbufr.nam.2018010311.t38z.tm03.nc'),
        ('380', 'prepbufr.nam.2018011717.t380z.tm03.nc')

    ]
)
def test_nam_substitution_HH(key, value):
    # Test that the substitution works correctly when given an init time,
    # cycle hour, and negative offset hour.
    init_string = "20180102"
    cycle_string = key
    offset_string = '03'
    expected_filename = value
    logger = logging.getLogger("test")
    templ = \
        'prepbufr.nam.{valid?fmt=%Y%m%d%H}.t{cycle?fmt=%HH}z.tm{' \
        'offset?fmt=%HH}.nc'
    ss = StringSub(logger, templ, init=init_string, cycle=cycle_string,
                   offset=offset_string)
    filename = ss.doStringSub()
    # print('nam filename: ', filename)
    assert (filename == expected_filename)


@pytest.mark.parametrize(
    'key, value', [
        ('18', 'prepbufr.nam.2018010215.t018z.tm03.nc'),
        ('03', 'prepbufr.nam.2018010200.t003z.tm03.nc'),

    ]
)
def test_nam_substitution_HHH(key, value):
    # Test that the substitution works correctly when given an init time,
    # cycle hour, and negative offset hour.
    init_string = "20180102"
    cycle_string = key
    offset_string = '03'
    expected_filename = value
    logger = logging.getLogger("test")
    templ = \
        'prepbufr.nam.{valid?fmt=%Y%m%d%H}.t{cycle?fmt=%HHH}z.tm{' \
        'offset?fmt=%HH}.nc'
    ss = StringSub(logger, templ, init=init_string, cycle=cycle_string,
                   offset=offset_string)
    filename = ss.doStringSub()
    # print('nam filename: ', filename)
    assert (filename == expected_filename)


@pytest.mark.parametrize(
    'key, value', [
        ('38', 'prepbufr.nam.2018010311.t01_13_59_59z.tm03.nc'),
        ('380', 'prepbufr.nam.2018011717.t15_20_00_00z.tm03.nc')
    ]
)
def test_nam_substitution_dHMS(key, value):
        # Test that the substitution works correctly when given an init time,
        # cycle hour, and negative offset hour.
        init_string = "20180102"
        cycle_string = key
        offset_string = '03'
        expected_filename = value
        logger = logging.getLogger("test")
        templ = \
            'prepbufr.nam.{valid?fmt=%Y%m%d%H}.t{cycle?fmt=%dd%HH%M%S}z.tm{' \
            'offset?fmt=%HH}.nc'
        ss = StringSub(logger, templ, init=init_string, cycle=cycle_string,
                       offset=offset_string)
        filename = ss.doStringSub()
        # print('nam filename: ', filename)
        assert (filename == expected_filename)


def test_hh_lead():
    logger = logging.getLogger("test")
    template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%HH}h"
    filepath = "1987020103_A03h"
    se = StringExtract(logger, template,
                           filepath)
    se.parseTemplate()
    ftime = se.getValidTime("%Y%m%d%H%M")
    assert(ftime == "198702010600")


def test_hhh_lead():
    logger = logging.getLogger("test")
    template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%HHH}h"
    filepath = "1987020103_A003h"
    se = StringExtract(logger, template,
                           filepath)
    se.parseTemplate()
    ftime = se.getValidTime("%Y%m%d%H%M")
    assert(ftime == "198702010600")


def test_2h_lead():
    logger = logging.getLogger("test")
    template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%.2H}h"
    filepath = "1987020103_A03h"
    se = StringExtract(logger, template,
                           filepath)
    se.parseTemplate()
    ftime = se.getValidTime("%Y%m%d%H%M")
    assert(ftime == "198702010600")


def test_3h_lead():
    logger = logging.getLogger("test")
    template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%.3H}h"
    filepath = "1987020103_A003h"
    se = StringExtract(logger, template,
                           filepath)
    se.parseTemplate()
    ftime = se.getValidTime("%Y%m%d%H%M")
    assert(ftime == "198702010600")


def test_h_lead_no_pad_1_digit():
    logger = logging.getLogger("test")
    template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%H}h"
    filepath = "1987020103_A3h"
    se = StringExtract(logger, template,
                           filepath)
    se.parseTemplate()
    ftime = se.getValidTime("%Y%m%d%H%M")
    assert(ftime == "198702010600")


def test_h_lead_no_pad_2_digit():
    logger = logging.getLogger("test")
    template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%H}h"
    filepath = "1987020103_A12h"
    se = StringExtract(logger, template,
                           filepath)
    se.parseTemplate()
    ftime = se.getValidTime("%Y%m%d%H%M")
    assert(ftime == "198702011500")


def test_h_lead_no_pad_3_digit():
    logger = logging.getLogger("test")
    template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%H}h"
    filepath = "1987020103_A102h"
    se = StringExtract(logger, template,
                           filepath)
    se.parseTemplate()
    ftime = se.getValidTime("%Y%m%d%H%M")
    assert(ftime == "198702050900")


def test_h_lead_no_pad_1_digit_sub():
    logger = logging.getLogger("test")
    file_template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%H}h"
    init_time = "1987020103"
    lead_time = "3"
    fSts = StringSub(logger,
                     file_template,
                     init=init_time,
                     lead=lead_time)
    out_string = fSts.doStringSub()
    assert(out_string == "1987020103_A3h")


def test_h_lead_no_pad_2_digit_sub():
    logger = logging.getLogger("test")
    file_template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%H}h"
    init_time = "1987020103"
    lead_time = "12"
    fSts = StringSub(logger,
                     file_template,
                     init=init_time,
                     lead=lead_time)
    out_string = fSts.doStringSub()
    assert(out_string == "1987020103_A12h")


def test_h_lead_no_pad_3_digit_sub():
    logger = logging.getLogger("test")
    file_template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%H}h"
    init_time = "1987020103"
    lead_time = "102"
    fSts = StringSub(logger,
                     file_template,
                     init=init_time,
                     lead=lead_time)
    out_string = fSts.doStringSub()
    assert(out_string == "1987020103_A102h")


def test_h_lead_pad_1_digit_sub():
    logger = logging.getLogger("test")
    file_template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%.1H}h"
    init_time = "1987020103"
    lead_time = "3"
    fSts = StringSub(logger,
                     file_template,
                     init=init_time,
                     lead=lead_time)
    out_string = fSts.doStringSub()
    assert(out_string == "1987020103_A3h")


def test_h_lead_pad_2_digit_sub():
    logger = logging.getLogger("test")
    file_template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%.2H}h"
    init_time = "1987020103"
    lead_time = "3"
    fSts = StringSub(logger,
                     file_template,
                     init=init_time,
                     lead=lead_time)
    out_string = fSts.doStringSub()
    assert(out_string == "1987020103_A03h")


def test_h_lead_pad_2_digit_sub():
    logger = logging.getLogger("test")
    file_template = "{init?fmt=%Y%m%d%H}_A{lead?fmt=%.3H}h"
    init_time = "1987020103"
    lead_time = "3"
    fSts = StringSub(logger,
                     file_template,
                     init=init_time,
                     lead=lead_time)
    out_string = fSts.doStringSub()
    assert(out_string == "1987020103_A003h")


def test_ym_date_dir_init():
    # Test that the ym directory can be read in and does substitution correctly
    logger = logging.getLogger("test")
    # e.g. /d1/METplus_TC/adeck_orig/201708/atcfunix.gfs.2017080100
    init_str = '2017080100'
    date_str = '201708'
    templ = '/d1/METplus_TC/adeck_orig/{date?fmt=%s}/' \
            'atcfunix.gfs.{init?fmt=%Y%m%d%H}.dat'
    ss = StringSub(logger, templ, date=date_str, init=init_str)
    filename = ss.doStringSub()
    expected_filename = '/d1/METplus_TC/adeck_orig/201708/' \
                        'atcfunix.gfs.2017080100.dat'
    assert filename == expected_filename


def test_ym_date_dir():
    # Test that the ym directory can be read in and does substitution correctly
    logger = logging.getLogger("test")
    # e.g. /d1/METplus_TC/adeck_orig/201708/atcfunix.gfs.2017080100
    date_str = '201708'
    templ = '/d1/METplus_TC/adeck_orig/{date?fmt=%s}/' \
            'atcfunix.gfs.2017080100.dat'
    ss = StringSub(logger, templ, date=date_str)
    filename = ss.doStringSub()
    expected_filename = '/d1/METplus_TC/adeck_orig/201708/' \
                        'atcfunix.gfs.2017080100.dat'
    assert filename == expected_filename


def test_ymd_date_dir():
    # Test that the ymd directory can be read in and does substitution correctly
    logger = logging.getLogger("test")
    # e.g. /d1/METplus_TC/adeck_orig/20170811/atcfunix.gfs.2017080100
    init_str = '2017081118'
    date_str = '20170811'
    templ = '/d1/METplus_TC/adeck_orig/{date?fmt=%s}/atcfunix.gfs.' \
            '{init?fmt=%Y%m%d%H}.dat'
    ss = StringSub(logger, templ, date=date_str, init=init_str)
    filename = ss.doStringSub()
    expected_filename = '/d1/METplus_TC/adeck_orig/20170811/' \
                        'atcfunix.gfs.2017081118.dat'
    assert filename == expected_filename


def test_ymd_region_cyclone():
    # Test that we can recreate the full file path with a date,
    # region, and cyclone
    logger = logging.getLogger("test")
    # /d1/METplus_TC/bdeck_orig/20170811/bal052017.dat
    date_str = '201708'
    region_str = 'al'
    cyclone_str = '05'
    year_str = '2017'
    # templ = '/d1/METplus_TC/bdeck/{date?fmt=%Y%m}/bal{region?fmt=%s}.dat'
    templ = '/d1/METplus_TC/bdeck/{date?fmt=%s}/b{region?fmt=%s}' \
            '{cyclone?fmt=%s}{misc?fmt=%s}.dat'
    ss = StringSub(logger, templ, date=date_str, region=region_str,
                   cyclone=cyclone_str, misc=year_str)
    full_file = ss.doStringSub()
    expected_full_file = '/d1/METplus_TC/bdeck/201708/bal052017.dat'
    assert full_file == expected_full_file


def test_create_cyclone_regex():
    # Test that the regex created from a template is what is expected
    logger = logging.getLogger("test")
    templ = '/d1/METplus_TC/bdeck/{date?fmt=%s}/b{region?fmt=%s}' \
            '{cyclone?fmt=%s}{misc?fmt=%s}.dat'
    date_str = '201708'
    region_str = 'al'
    cyclone_str = '05'
    year_str = '2017'
    ss = StringSub(logger, templ, date=date_str, region=region_str,
                   cyclone=cyclone_str, misc=year_str)
    actual_regex = ss.create_cyclone_regex()
    expected_regex = '/d1/METplus_TC/bdeck/([0-9]{4,10})/b([a-zA-Z]{2})([0-9]' \
                     '{2,3})([a-zA-Z0-9-_.]+).dat'
    assert actual_regex == expected_regex


def test_crow_variable_hour():
    # Test that StringSub's doStringSub() correctly creates the valid hour
    # without any zero-padding when given the following as input:
    # pgbf{lead?fmt=%H}.gfs.{valid?fmt=%Y%M%D%H}
    # pgbf([0-9]{1,3}).gfs.(2[0-9]{9})
    logger = logging.getLogger("crow_data")

    # crow input files with 3, 2, and 1-digit lead times:
    crow_input_file_3 = 'pgbf219.gfs.2017060418'
    crow_input_file_2 = 'pgbf18.gfs.2017062000'
    crow_input_file_1 = 'pgbf3.gfs.2017060418'
    lead_1 = '3'
    lead_2 = '18'
    lead_3 = '219'
    valid_2 = '2017062000'
    valid_1 = valid_3 = '2017060418'
    templ = 'pgbf{lead?fmt=%H}.gfs.{valid?fmt=%Y%m%d%H}'
    ss_1 = StringSub(logger, templ, valid=valid_1, lead=lead_1)
    ss_2 = StringSub(logger, templ, valid=valid_2, lead=lead_2)
    ss_3 = StringSub(logger, templ, valid=valid_3, lead=lead_3)
    crow_1_output = ss_1.doStringSub()
    crow_2_output = ss_2.doStringSub()
    crow_3_output = ss_3.doStringSub()
    # print("crow_1 output: ", crow_1_output)
    # print("crow_2 output: ", crow_2_output)
    # print("crow_3 output: ", crow_3_output)
    assert(crow_1_output == crow_input_file_1 and
           crow_2_output == crow_input_file_2 and
           crow_3_output == crow_input_file_3)


def test_create_grid2obs_regex_gfs():
    # Test that the regex created from a template is what is expected
    logger = logging.getLogger("test")
    templ = '/path/to/gfs/pgbf{lead?fmt=%H}.gfs.{valid?fmt=%Y%m%d%HH}'

    # variables to pass into StringSub
    valid_str = '2017081118'
    lead_str = '00'

    ss = StringSub(logger, templ, valid=valid_str, lead=lead_str)
    actual_regex = ss.create_grid2obs_regex()
    expected_regex = '/path/to/gfs/pgbf([0-9]{1,3}).gfs.([0-9]{10})'
    assert actual_regex == expected_regex


def test_create_grid2obs_regex_nam():
    # Test that the regex created from a template is what is expected
    logger = logging.getLogger("test")
    templ = \
        '/path/to/nam.20170811/nam.t{cycle?' \
        'fmt=%HH}z.prepbufr.tm{offset?fmt=%HH}'

    # variables to set for StringSub
    cycle_str = '18'
    offset_str = '03'

    ss = StringSub(logger, templ, cycle=cycle_str, offset=offset_str)
    actual_regex = ss.create_grid2obs_regex()
    expected_regex = \
        '/path/to/nam.20170811/nam.t([0-9]{2,3})z.prepbufr.tm([0-9]{2,3})'
    assert actual_regex == expected_regex


def test_create_grid2obs_regex_gdas():
    # Test that the regex created from a template is what is expected
    logger = logging.getLogger("test")
    templ = \
        '/path/to/gdas/prepbufr.gdas.{valid?fmt=%Y%m%d%HH}'
    # '/path/to/nam.20170611/nam.t[cycle?fmt=%HH}z.prepbufr.tm{offset?fmt=%HH}'
    # templ_hrrr ='/path/to/hrrr.t{cycle?fmt=%HH}z.wrfprsf{lead?fmt=%HH}.grib2'
    # tmpl_gdas = 'prepbufr.gdas.{valid?fmt=%Y%m%d%HH}'

    # variables to set for StringSub
    valid_str = '2017063018'

    ss = StringSub(logger, templ, valid=valid_str)
    actual_regex = ss.create_grid2obs_regex()
    expected_regex = '/path/to/gdas/prepbufr.gdas.([0-9]{10})'
    assert actual_regex == expected_regex

def test_create_grid2obs_regex_hrrr():
    # Test that the regex created from a template is what is expected
    logger = logging.getLogger("test")
    templ = \
    '/path/to/hrrr/hrrr.t{cycle?fmt=%HH}z.wrfprsf{lead?fmt=%HH}.grib2'

    # variables to set for StringSub
    cycle_str = '15'
    lead_str = '12'

    ss = StringSub(logger, templ, cycle=cycle_str, lead=lead_str)
    actual_regex = ss.create_grid2obs_regex()
    expected_regex = \
        '/path/to/hrrr/hrrr.t([0-9]{2,3})z.wrfprsf([0-9]{1,3}).grib2'
    assert actual_regex == expected_regex


def test_create_grid2obs_regex_all():
    # Test that the regex created from the template that has valid
    # cycle, lead and offset is correct (expected).
    logger = logging.getLogger("test")
    templ = \
        '/path/to/nam.{init?fmt=%Y%m%d}/rap.t{cycle?fmt=%HH}z.awphys{lead?fmt=%H}.' \
        'tm{offset?fmt=%H}.grib2'

    # variables to set for StringSub
    init_str = "20180815"
    cycle_str = '00'
    lead_str = '60'
    offset_str = '00'

    ss = StringSub(logger, templ, init=init_str, cycle=cycle_str,
                   lead=lead_str, offset=offset_str)
    actual_regex = ss.create_grid2obs_regex()
    expected_regex = '/path/to/nam.([0-9]{8})/rap.t([0-9]{2,3})z.' \
                     'awphys([0-9]{1,3}).tm([0-9]{2,3}).grib2'
    assert actual_regex == expected_regex
