import sys
import os
import re
import warnings
import pandas as pd
from datetime import datetime
# import matplotlib.pyplot as plt

# TODO: lakeshore, etc.

def chldrn_labeled_with_date(parent):
    # parent: path of parent
    # returns only child directories labeled with ##-##-##

    contents = os.scandir(parent)
    p = re.compile(r'^\d\d-\d\d-\d\d$')
    return [ child for child in contents if (p.match(child.name) and child.is_dir()) ]


def prep_dataframe(df):
    # df: dataframe
    # sets index to datetime in place

    df['datetime'] = pd.to_datetime(df[0] + ' ' + df[1], format="%d-%m-%y %H:%M:%S")
    df.set_index('datetime', inplace=True)
    df.sort_values('datetime', inplace=True)


def concatenate_date_dirs(parent):
    # parent: path of parent

    dirs = chldrn_labeled_with_date(parent)

    channels = {}

    def d(date): return datetime.strptime(date, "%y-%m-%d")

    for dir in dirs:
        print(f"Parsing {dir.path}")

        date = dir.name

        datafiles = os.scandir(dir.path)
        for df in datafiles:
            # warn if the file is not named like the usual pattern
            if (not df.name.endswith(f'{date}.log')):
                warnings.warn(f'The file {df.path} is not of the form "[name] {date}.log" and will be ignored')
        
            # TODO deal with Status_ files seperately
            elif (df.name.startswith('Status_')):
                pass
            # temporarily only consider channel 1
            elif (not df.name.startswith('CH1 T')):
                pass
            else:
                chnl_name = df.name[:-12].strip() # turn "CH9 T 23-04-28.log" into "CH9 T"
                data = pd.read_csv(df.path, header=None)

                if chnl_name not in channels:
                    channels[chnl_name] = { 'data': data }
                    channels[chnl_name]['recent_path'] = df.path
                else:
                    channels[chnl_name]['data'] = pd.concat((channels[chnl_name]['data'], data))

                    # The most recent file will be polled for updates,
                    # so we need to keep track of which those are
                    prev_recent_date = channels[chnl_name]['recent_path'][-12:-4]
                    if (d(date) > d(prev_recent_date)):
                        channels[chnl_name]['recent_path'] = df.path

    for chnl in channels:
        # open the most recent file, so that we may poll it for changes
        channels[chnl]['file'] = open(channels[chnl]['recent_path'], 'r')
        # place the current read head at the end of the file
        channels[chnl]['file'].seek(0, os.SEEK_END)

        prep_dataframe(channels[chnl]['data'])
    
    return channels


if __name__ == "__main__":

    url = sys.argv[1]

    print('Building Data...')

    channels = concatenate_date_dirs(url)
    
    print('Available channels:')

    for ch in sorted(channels.keys()):
        print(ch)

