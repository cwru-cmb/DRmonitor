import sys
import os
import re
import warnings
import pandas as pd

from channel import Channel
import config

def chldrn_labeled_with_date(parent: str):
    """Returns child directories labeled with ##-##-## """

    contents = os.scandir(parent)
    p = re.compile(r'^\d\d-\d\d-\d\d$')
    return [ child for child in contents if (p.match(child.name) and child.is_dir()) ]


def _injest_file(entry: os.DirEntry, channels: dict[Channel]):
    """Adds data from entry into channels, creating a new one if none exists"""

    # turn "CH9 T 23-04-28.log" into "CH9 T"
    chnl_name = entry.name[:-12].strip()

    data = pd.read_csv(entry.path, header=None)

    # create channel if it doesn't exist
    if chnl_name not in channels:
        channels[chnl_name] = Channel(chnl_name)
    
    channels[chnl_name].add_data(data)
    channels[chnl_name].add_path(entry.path)


def _concatenate_into_channels(entries: list[os.DirEntry]) -> dict[Channel]:
    channels = {}

    for dir in entries:
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
            # only consider channel 1 if configured
            elif (config.ONLY_LOAD_CH1_T and not df.name.startswith('CH1 T')):
                pass
            else:
                _injest_file(df, channels)
    
    return channels

def prep_dataframe(df: pd.DataFrame, date_column: int | str, date_fmt: str, time_column: int | str, time_fmt: str):
    """
    Sets index of df to datetime (in place), then sorts. Date and time formats follow the datetime specification: https://docs.python.org/3/library/datetime.html#format-codes
    
    Parameters
        df: DataFrame to sort
        date_column: the column which contains the dates
        date_fmt: the format that the dates are in (ex. %d-%m-%y)
        time_column: the column which contains the times
        time_fmt: the format that the times are in (ex. %H:%M:%S)
    """

    format = f"{date_fmt}T{time_fmt}"
    df['datetime'] = pd.to_datetime(df[date_column] + 'T' + df[time_column], format=format)
    df.set_index('datetime', inplace=True)
    df.sort_values('datetime', inplace=True)


def injest_date_dirs(date_dirs: list[os.DirEntry]) -> dict[Channel]:
    """
    Used for csv data stored as:
             
    Run 19 Logs/
    ├─ [ contents with different naming convention ignored ]
    ├─ 23-04-28/
    │  ├─ CH1 T 23-04-28.log
    │  ├─ CH2 T 23-04-28.log
    │  └─ Flowmeter 23-04-28.log
    ├─ 23-04-26/
    │  ├─ CH1 T 23-04-26.log
    │  ├─ CH2 T 23-04-26.log
    │  └─ Flowmeter 23-04-26.log
    └─ 23-04-27/
       ├─ CH1 T 23-04-27.log
       ├─ CH2 T 23-04-27.log
       └─ Flowmeter 23-04-27.log
    """

    channels = _concatenate_into_channels(date_dirs)

    print("Preparing...")
    for chnl in channels:
        # open the most recent file, so that we may poll it for changes
        channels[chnl].open_recent()
        # sort data and prep indeces
        prep_dataframe(channels[chnl].data, 0, "%d-%m-%y", 1, "%H:%M:%S")
    
    return channels


if __name__ == "__main__":

    url = sys.argv[1]

    print('Building Data...')

    channels = injest_date_dirs(url)
    
    print('Available channels:')

    for ch in sorted(channels.keys()):
        print(ch)

