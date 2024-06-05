import sys
import os
import re
import warnings
import pandas as pd

from channel import Channel
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
    """
    Used for csv data stored as:

    parent/
        ├ [day 1 as YY-MM-DD]/
        │    ├ [channel name 1] YY-MM-DD.[3-letter extension]
        │    ├ [...]
        │    └ [channel name n] YY-MM-DD.[3-letter extension]
        ├ [...]
        └ [day m as YY-MM-DD]/
             ├ [channel name 1] YY-MM-DD.log.[3-letter extension]
             ├ [...]
             └ [channel name n] YY-MM-DD.log.[3-letter extension]

    For example:
             
    Run 19 Logs/
        ├ [ contents with different naming convention ignored ]
        ├ 23-04-28/
        │   ├ CH1 T 23-04-28.log
        │   ├ CH2 T 23-04-28.log
        │   └ Flowmeter 23-04-28.log
        ├ 23-04-26/
        │   ├ CH1 T 23-04-26.log
        │   ├ CH2 T 23-04-26.log
        │   └ Flowmeter 23-04-26.log
        └ 23-04-27/
            ├ CH1 T 23-04-27.log
            ├ CH2 T 23-04-27.log
            └ Flowmeter 23-04-27.log
    """

    dirs = chldrn_labeled_with_date(parent)

    channels = {}

    for dir in dirs:
        print(f"Parsing {dir.path}")

        date = dir.name

        datafiles = os.scandir(dir.path)
        for df in datafiles:
            # warn if the file is not named in the usual way
            if (not df.name.endswith(f'{date}.log')):
                warnings.warn(f'The file {df.path} is not of the form "[name] {date}.log" and will be ignored')
        
            # TODO deal with Status_ files seperately
            elif (df.name.startswith('Status_')):
                pass
            # # temporarily only consider channel 1
            # elif (not df.name.startswith('CH1 T')):
            #     pass
            else:
                # turn "CH9 T 23-04-28.log" into "CH9 T"
                chnl_name = df.name[:-12].strip()

                data = pd.read_csv(df.path, header=None)

                # create channel if it doesn't exist
                if chnl_name not in channels:
                    channels[chnl_name] = Channel(chnl_name)
                
                channels[chnl_name].add_data(data)
                channels[chnl_name].add_path(df.path)

    for chnl in channels:
        # open the most recent file, so that we may poll it for changes
        channels[chnl].open_recent()

        prep_dataframe(channels[chnl].data)
    
    return channels


if __name__ == "__main__":

    url = sys.argv[1]

    print('Building Data...')

    channels = concatenate_date_dirs(url)
    
    print('Available channels:')

    for ch in sorted(channels.keys()):
        print(ch)

