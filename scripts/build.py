#! /usr/bin/env python3
'''
Build the OER in various formats from the data files
'''

# imports
from datetime import datetime
from json import load as jload
from pathlib import Path
from subprocess import run
from sys import argv, stderr
from zoneinfo import ZoneInfo
import argparse

# constants
BUILD_TIME = datetime.now(ZoneInfo("America/Los_Angeles"))
DEFAULT_DATA_PATH = Path(argv[0]).resolve().parent.parent / 'data'
DEFAULT_REFS_PATH = Path(argv[0]).resolve().parent.parent / 'refs' / 'refs.bib'
DEFAULT_CSL_PATH = Path(argv[0]).resolve().parent.parent / 'style' / 'ieee.csl'
MONTHS_ABBR = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MONTHS_FULL = [None, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# return the current time as a string
def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# print a log message
def print_log(s='', end='\n', file=stderr):
    print('[%s] %s' % (get_time(), s), end=end, file=file)

# print error message and exit
def error(s, file=stderr, exitcode=1):
    print_log("ERROR: %s" % s, file=file); exit(exitcode)

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

# convert a list of citations from a `_cite` attribute to a semicolon-separated string
def semicolon_separated_cites(citations):
    return '; '.join('@%s' % cite for cite in citations)

# parse user args
def parse_args():
    # parse args
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--data', required=False, type=str, default=DEFAULT_DATA_PATH, help="Input Data Path")
    parser.add_argument('-r', '--refs', required=False, type=str, default=DEFAULT_REFS_PATH, help="Input References (BIB)")
    parser.add_argument('-rs', '--refs_style', required=False, type=str, default=DEFAULT_CSL_PATH, help="References Style (CSL)")
    parser.add_argument('-o', '--output', required=True, type=str, help="Output Directory")
    parser.add_argument('--pandoc_path', required=False, type=str, default='pandoc', help="Path to 'pandoc' Executable")
    args = parser.parse_args()

    # check args before returning
    if isinstance(args.data, str):
        args.data = Path(args.data)
    if not args.data.is_dir():
        error("Directory not found: %s" % args.data)
    if isinstance(args.refs, str):
        args.refs = Path(args.refs)
    if isinstance(args.refs_style, str):
        args.refs_style = Path(args.refs_style)
    for p in [args.refs, args.refs_style]:
        if not p.is_file():
            error("File not found: %s" % p)
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
        for data_dict in data_dicts.values():
            to_fix = dict()
            for k, v in data_dict.items():
                if k.startswith('date_') and not k.endswith('_cite'):
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
            curr_data_entries = dict()
            for json_path in data_sub_path.rglob('*.json'):
                with open(json_path, 'rt') as json_f:
                    try:
                        curr_json_data = jload(json_f)
                    except Exception as e:
                        error("Failed to load JSON: %s\n%s" % (json_path, e))
                    curr_json_data['name_safe'] = json_path.name.replace('.json','')
                    curr_data_entries[curr_json_data['name']] = curr_json_data
            data[data_sub_path.name] = curr_data_entries

    # preprocess data
    parse_dates(data)
    return data

# build markdown output
def build_markdown(data, md_path, md_title="History of Video Games", md_author="Niema Moshiri", md_date=BUILD_TIME.strftime("%B %d, %Y"), verbose=True):
    # set things up
    companies_sorted = sorted(data['companies'].values(), key=lambda x: x['name'])
    people_sorted = sorted(data['people'].values(), key=lambda x: x['name'])

    # precompute timeline
    events = dict() # events[decade][year][(year,month,day)] = list of event descriptions
    events_list = list() # temporary holder before adding to `events`
    for company_data in companies_sorted:
        if 'date_start' in company_data:
            event_desc = '[%s](#%s) was founded.' % (company_data['name'], company_data['name_safe'])
            if 'date_start_cite' in company_data:
                event_desc += (' [%s]' % semicolon_separated_cites(company_data['date_start_cite']))
            events_list.append((company_data['date_start'], event_desc))
        if 'date_end' in company_data:
            event_desc = '[%s](#%s) was closed.' % (company_data['name'], company_data['name_safe'])
            if 'date_end_cite' in company_data:
                event_desc += (' [%s]' % semicolon_separated_cites(company_data['date_end_cite']))
            events_list.append((company_data['date_end'], event_desc))
    for person_data in people_sorted:
        if 'date_birth' in person_data:
            event_desc = '[%s](#%s) was born.' % (person_data['name'], person_data['name_safe'])
            if 'date_birth_cite' in person_data:
                event_desc += (' [%s]' % semicolon_separated_cites(person_data['date_birth_cite']))
            events_list.append((person_data['date_birth'], event_desc))
        if 'date_death' in person_data:
            event_desc = '[%s](#%s) passed away.' % (person_data['name'], person_data['name_safe'])
            if 'date_death_cite' in person_data:
                event_desc += (' [%s]' % semicolon_separated_cites(person_data['date_death_cite']))
            events_list.append((person_data['date_death'], event_desc))
    for curr_date, curr_desc in events_list:
        curr_decade = str(curr_date[0])[:3] + '0s'
        if curr_decade not in events:
            events[curr_decade] = dict()
        if curr_date[0] not in events[curr_decade]:
            events[curr_decade][curr_date[0]] = dict()
        if curr_date not in events[curr_decade][curr_date[0]]:
            events[curr_decade][curr_date[0]][curr_date] = list()
        events[curr_decade][curr_date[0]][curr_date].append(curr_desc)

    # create markdown output
    with open(md_path, 'wt') as md_f:
        # write title block
        md_f.write('%% %s\n' % md_title)
        md_f.write('%% %s\n' % md_author)
        md_f.write('%% %s\n' % md_date)
        md_f.write('\n')

        # write "Companies" section
        md_f.write('# Companies {#companies}\n')
        md_f.write('This section will describe video game companies and the consoles they produced.\n')
        md_f.write('\n')
        for company_data in companies_sorted:
            md_f.write('## %s {#%s}\n' % (company_data['name'], company_data['name_safe']))
            md_f.write('[%s](#%s)' % (company_data['name'], company_data['name_safe']))
            if 'name_orig' in company_data:
                md_f.write(' (%s)' % company_data['name_orig'])
            md_f.write(' is a company founded')
            if 'location_start' in company_data:
                md_f.write(' in %s' % company_data['location_start'])
                if 'location_start_cite' in company_data:
                    md_f.write(' [%s]' % semicolon_separated_cites(company_data['location_start_cite']))
            if 'founders' in company_data:
                founders = comma_separated(['[%s](#%s)' % (data['people'][founder]['name'], data['people'][founder]['name_safe']) for founder in company_data['founders']])
                if len(founders) != 0:
                    md_f.write(' by ' + founders)
                    if 'founders_cite' in company_data:
                        md_f.write(' [%s]' % semicolon_separated_cites(company_data['founders_cite']))
            if company_data['date_start'].count(None) == 0:
                md_f.write(' on ')
            else:
                md_f.write(' in ')
            md_f.write('[%s](#%s)' % (convert_date_tuple(company_data['date_start'],'text'), convert_date_tuple(company_data['date_start'],'yyyy-mm-dd')))
            if 'date_start_cite' in company_data:
                md_f.write(' [%s]' % semicolon_separated_cites(company_data['date_start_cite']))
            md_f.write('.\n')
            md_f.write('\n')
        md_f.write('\n')

        # write "People" section
        md_f.write('# People {#people}\n')
        md_f.write('This section will describe important people in video game history.\n')
        md_f.write('\n')
        for person_data in people_sorted:
            md_f.write('## %s {#%s}\n' % (person_data['name'], person_data['name_safe']))
            md_f.write('[%s](#%s)' % (person_data['name'], person_data['name_safe']))
            if 'name_orig' in person_data:
                md_f.write(' (%s)' % person_data['name_orig'])
            md_f.write(' was born')
            if 'location_birth' in person_data:
                md_f.write(' in %s' % person_data['location_birth'])
                if 'location_birth_cite' in person_data:
                    md_f.write(' [%s]' % semicolon_separated_cites(person_data['location_birth_cite']))
            if person_data['date_birth'].count(None) == 0:
                md_f.write(' on ')
            else:
                md_f.write(' in ')
            md_f.write('[%s](#%s)' % (convert_date_tuple(person_data['date_birth'],'text'), convert_date_tuple(person_data['date_birth'],'yyyy-mm-dd')))
            if 'date_birth_cite' in person_data:
                md_f.write(' [%s]' % semicolon_separated_cites(person_data['date_birth_cite']))
            if 'date_death' in person_data:
                md_f.write(', and passed away')
                if 'location_death' in person_data:
                    md_f.write(' in %s' % person_data['location_death'])
                    if 'location_death_cite' in person_data:
                        md_f.write(' [%s]' % semicolon_separated_cites(person_data['location_death_cite']))
                if person_data['date_death'].count(None) == 0:
                    md_f.write(' on ')
                else:
                    md_f.write(' in ')
                md_f.write('[%s](#%s)' % (convert_date_tuple(person_data['date_death'],'text'), convert_date_tuple(person_data['date_death'],'yyyy-mm-dd')))
                if 'date_death_cite' in person_data:
                    md_f.write(' [%s]' % semicolon_separated_cites(person_data['date_death_cite']))
            md_f.write('.\n')
            md_f.write('\n')
        md_f.write('\n')

        # write "Timeline" section
        md_f.write('# Timeline {#timeline}\n')
        md_f.write('This section contains a timeline of important events in video game history.\n')
        md_f.write('\n')
        for decade, decade_dict in sorted(events.items()):
            md_f.write('## %s {#%s}\n' % (decade, decade))
            md_f.write('\n')
            for year, year_dict in sorted(decade_dict.items()):
                md_f.write('### %s {#%s}\n' % (year, year))
                md_f.write('\n')
                for event_date, event_descs in sorted(year_dict.items()):
                    md_f.write('#### %s {#%s}\n' % (convert_date_tuple(event_date,'text'), convert_date_tuple(event_date,'yyyy-mm-dd')))
                    for event_desc in sorted(event_descs):
                        md_f.write('* %s\n' % event_desc)
                    md_f.write('\n')
        md_f.write('\n')

# run pandoc to convert Markdown to all other formats
def run_pandoc(md_path, refs_path, refs_style_path, pandoc_path='pandoc', verbose=True):
    html_path = md_path.parent / (md_path.stem + '.html')
    command_base = ['pandoc', '-s', '--toc', '--citeproc', md_path, '--bibliography', refs_path, '--csl', refs_style_path, '-M', 'reference-section-title=Bibliography', '--metadata', 'link-citations:true']
    command_html = command_base + ['-o', html_path]
    if verbose:
        print_log("HTML Command: %s" % ' '.join(str(s) for s in command_html))
    run(command_html)

# main program logic
def main(verbose=True):
    # set things up
    args = parse_args()
    if verbose:
        print_log("Loading data from: %s" % args.data)
    data = load_data(args.data)
    if verbose:
        print_log("Output Directory: %s" % args.output)
    args.output.mkdir()

    # build pages from loaded data
    md_path = args.output / 'index.md'
    if verbose:
        print_log("Building Markdown output...")
    build_markdown(data, md_path, verbose=verbose)
    if verbose:
        print_log("Running Pandoc to build other outputs...")
    run_pandoc(md_path, args.refs, args.refs_style, pandoc_path=args.pandoc_path, verbose=verbose)

# run tool
if __name__ == "__main__":
    main()
