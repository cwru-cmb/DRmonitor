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

    data = pd.read_csv(entry.path, header=None, low_memory=False)

    # create channel if it doesn't exist
    if chnl_name not in channels:
        channels[chnl_name] = Channel(chnl_name)
    
    channels[chnl_name].add_data(data)
    channels[chnl_name].add_path(entry.path)

# def _injest_status(entry: os.DirEntry, channels: dict[Channel]):
#     status_name = entry.name[:-12].strip() # most likely 'Status_'
    
#     with open(entry.path) as f:
#         for line in f:
#             data = line.split(',')
#             end = len(data)
#             i = 2

#             while i < end:
#                 chnl_name = f'{status_name}/{data[i]}'

#                 if chnl_name not in channels:
#                     channels[chnl_name] = Channel(chnl_name)

#                 channels[chnl_name].add_data([data[0],data[1],data[i+1]])
#                 i += 2

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
            # deal with Status_ files seperately
            elif (df.name.startswith('Status_')):
                # _injest_status(df, channels)
                pass
            # if configured, only consider channel 1
            elif (config.ONLY_LOAD_CH1_T and not df.name.startswith('CH1 T')): pass
            else:
                _injest_file(df, channels)
    
    return channels


def build_dates(df: pd.DataFrame, date_column: int | str, date_fmt: str, time_column: int | str, time_fmt: str):
    """
    Sets index of df to datetime (in place), then sorts. Date and time formats follow the datetime specification: https://docs.python.org/3/library/datetime.html#format-codes
    
    Parameters
        df: DataFrame to sort
        date_column: the column which contains the dates
        date_fmt: the format that the dates are in (ex. %d-%m-%y)
        time_column: the column which contains the times
        time_fmt: the format that the times are in (ex. %H:%M:%S)
        cache: TODO
    """

    format = f"{date_fmt}T{time_fmt}"
    df['datetime'] = pd.to_datetime(df[date_column] + 'T' + df[time_column], format=format)

    df.set_index('datetime', inplace=True)
    df.sort_values('datetime', inplace=True)

    # print('df', df)


# def extract_status(df: pd.DataFrame):

#     subset = df.columns[2:]
#     print(df[subset])

#         # print(line)
#     # print('df.columns', df.columns)
#     # d = df.duplicated(subset=subset, keep='first')
#     # d = df.duplicated(subset=subset, keep='first') & df.duplicated(subset=subset, keep='last')
#     # print(d)

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

    # TODO: move this to config somehow
    # TODO: test adding new data

    for chnl in channels:
        # open the most recent file, so that we may poll it for changes
        channels[chnl].open_recent()

        df = channels[chnl].data

        # sort data and prep indeces
        build_dates(df, 0, "%d-%m-%y", 1, "%H:%M:%S")

        df[0] = df[0].astype('category')

        if (chnl.startswith("maxigauge")):
            for i in range(2, len(df.columns)):
                if (((i - 1) % 6) <= 2): df[i] = df[i].astype('category')
        elif (chnl.startswith("Channels")):
            for i in range(2, len(df.columns)):
                if (((i - 1) % 2) == 0): df[i] = df[i].astype('category')

    return channels


if __name__ == "__main__":

    url = sys.argv[1]

    print('Building Data...')

    channels = injest_date_dirs(url)
    
    print('Available channels:')

    for ch in sorted(channels.keys()):
        print(ch)

