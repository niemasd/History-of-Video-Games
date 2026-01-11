#! /usr/bin/env python3
'''
Build the OER in various formats from the data files
'''

# imports
from json import load as jload
from pathlib import Path
from sys import argv, stderr
import argparse

# constants
DEFAULT_DATA_PATH = Path(argv[0]).resolve().parent.parent / 'data'
MONTHS_FULL = [None, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
MONTHS_ABBR = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# print error message and exit
def error(s, file=stderr, exitcode=1):
    print("ERROR: %s" % s, file=file); exit(exitcode)

# convert a list of strings to a properly-comma-separated string
def comma_separated(vals):
    if len(vals) == 0:
        return ''
    elif len(vals) == 1:
        return vals[0]
    elif len(vals) == 2:
        return vals[0] + ' and ' + vals[1]
    else:
        return ', '.join(vals[:-1]) + ', and ' + vals[-1]

# parse user args
def parse_args():
    # parse args
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--data', required=False, type=str, default=DEFAULT_DATA_PATH, help="Input Data Path")
    parser.add_argument('-o', '--output', required=True, type=str, help="Output Directory")
    args = parser.parse_args()

    # check args before returning
    if isinstance(args.data, str):
        args.data = Path(args.data)
    if not args.data.is_dir():
        error("Directory not found: %s" % args.data)
    if isinstance(args.output, str):
        args.output = Path(args.output)
    if args.output.exists():
        error("Output already exists: %s" % args.output)
    if not args.output.parent.is_dir():
        error("Invalid output path: %s" % args.output)
    return args

# parse all dates in `data` as (year, month, day) `tuple` objects (`None` = missing)
def parse_dates(data):
    for data_dicts in data.values():
        for data_dict in data_dicts:
            to_fix = dict()
            for k, v in data_dict.items():
                if k.startswith('date_'):
                    parts = [int(part) for part in v.split('-')]
                    parts += ([None]*(3-len(parts)))
                    to_fix[k] = tuple(parts)
            for k, v_fixed in to_fix.items():
                data_dict[k] = v_fixed

# convert a date tuple to some other date format ("yyyy-mm-dd", "text_full", or "text_abbr")
def convert_date_tuple(date_tuple, date_format):
    if date_tuple[1] is None: # just a year
        return str(date_tuple[0])
    date_format = date_format.strip().lower()
    if date_format == 'yyyy-mm-dd':
        out = str(date_tuple[0]) + '-' + str(date_tuple[1]).zfill(2)
        if date_tuple[2] is not None:
            out += ('-' + str(date_tuple[2]).zfill(2))
        return out
    elif date_format.startswith('text'):
        if date_format.endswith('_abbr'):
            out = MONTHS_ABBR[date_tuple[1]]
        else:
            out = MONTHS_FULL[date_tuple[1]]
        if date_tuple[2] is not None:
            out += (' ' + str(date_tuple[2]) + ',')
        return out + ' ' + str(date_tuple[0])
    else:
        error("Invalid date format: %s" % date_format)

# load data
def load_data(data_path):
    # load data from JSON files
    data = dict()
    for data_sub_path in data_path.glob('*'):
        if data_sub_path.is_dir():
            curr_data_entries = list()
            for json_path in data_sub_path.rglob('*.json'):
                with open(json_path, 'rt') as json_f:
                    curr_data_entries.append(jload(json_f))
            data[data_sub_path.name] = curr_data_entries

    # preprocess data
    parse_dates(data)
    return data

# build markdown output
def build_markdown(data, out_file_path):
    # set things up
    companies_sorted = sorted(data['companies'], key=lambda x: x['name'])

    # create markdown output
    with open(out_file_path, 'wt') as md_f:
        for company_data in companies_sorted:
            # company header
            md_f.write('# %s {#%s}\n' % (company_data['name'], company_data['name_safe']))

            # company description
            md_f.write('%s is a company founded' % company_data['name'])
            if 'location_start' in company_data:
                md_f.write(' in %s' % company_data['location_start'])
            if 'founders' in company_data:
                founders = comma_separated(company_data['founders'])
                if len(founders) != 0:
                    md_f.write(' by ' + founders)
            if company_data['date_start'].count(None) == 0:
                md_f.write(' on ')
            else:
                md_f.write(' in ')
            md_f.write(convert_date_tuple(company_data['date_start'], date_format='text'))
            md_f.write('.\n')
            md_f.write('\n')

# main program logic
def main():
    # set things up
    args = parse_args()
    data = load_data(args.data)
    args.output.mkdir()

    # build pages from loaded data
    build_markdown(data, args.output / 'index.md')

# run tool
if __name__ == "__main__":
    main()
