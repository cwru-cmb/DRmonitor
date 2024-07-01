import os
import re
import warnings
import pandas as pd
from datetime import datetime

from channel import Channel
import config

def chldrn_labeled_with_date(parent: str):
    """Returns child directories labeled with ##-##-## """

    contents = os.scandir(parent)
    p = re.compile(r'^\d\d-\d\d-\d\d$')
    return [ child for child in contents if (p.match(child.name) and child.is_dir()) ]


def _CH_handler(lines: list[list[str]]) -> pd.DataFrame:
    data = pd.DataFrame(lines)

    # parse dates
    format = f"%d-%m-%yT%H:%M:%S"
    data['datetime'] = pd.to_datetime(data[0] + 'T' + data[1], format=format)

    # set the date column as 'category' to save memory
    data[0] = data[0].astype('category')

    return data

def _Status_handler(lines: list[list[str]]) -> dict[pd.DataFrame]:
    data_groups = {}

    # line by line, field by field, parse dates and sort values
    for l in lines:
        d = datetime.strptime(l[0] + " " + l[1], "%d-%m-%y %H:%M:%S")
        i = 2
        while i < len(l):
            try: data_groups[l[i]].append([d, l[i + 1]])
            except KeyError: data_groups[l[i]] = [[d, l[i + 1]]]
            i += 2

    # turn the grouped arrays into a dictionary of dataframes
    new_channels = {}
    for group_name in data_groups:
        chnl_name = f'status/{group_name}'
        df = pd.DataFrame(data_groups[group_name])
        df.rename(columns={0:'datetime', 1:'value'}, inplace=True)
        new_channels[chnl_name] = df
    
    return new_channels

# this is it's own function so that we can use it when updating dataframes
def text_to_dfs(text: str, name: str) -> dict[pd.DataFrame]:
    lines = [s.split(',') for s in text.splitlines()]

    # Turn the array into one or multiple dataframes
    dataframes = {}
    if (name.lower().startswith('status')): dataframes = _Status_handler(lines)
    else: dataframes[name] = _CH_handler(lines)

    return dataframes


def _add_file_to_channels(entry: os.DirEntry, date: str, channels: dict[Channel]) -> None:
    # if configured for debugging, only skip all channels but CH1 T
    if (config.ONLY_LOAD_CH1_T and not entry.name.startswith('CH1 T')): pass

    # warn if the file is not named in the usual way
    elif (not entry.name.endswith(f'{date}.log')):
        warnings.warn(f'The file {entry.path} is not of the form "[name] {date}.log" and will be ignored')
    
    else:
        # turn "CH9 T 23-04-28.log" into "CH9 T"
        chnl_name = entry.name[:-12].strip()

        # read the whole file as text
        txt = ''
        with open(entry.path) as f:
            txt += f.read()
        
        dfs = text_to_dfs(txt, chnl_name)

        for data_name in dfs:
            if data_name not in channels:
                channels[data_name] = Channel(data_name)
            
            channels[data_name].add_data(dfs[data_name])
            channels[data_name].add_path(entry.path)


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

    channels = {}

    for dir in date_dirs:
        print(f"Parsing {dir.path}")
        for file in os.scandir(dir.path):
            _add_file_to_channels(file, dir.name, channels)

    print("Preparing...")

    for chnl in channels:
        # open the most recent file, so that we may poll it for changes
        channels[chnl].open_recent()

        df = channels[chnl].data

        # to reduce memory use, repeated strings are stored as type 'category'
        # for maxiguage, this is every 6th column,
        # for Channles, this is every other column
        if (chnl.startswith("maxigauge")):
            for i in range(2, len(df.columns)):
                if (((i - 1) % 6) <= 2): df[i] = df[i].astype('category')
        elif (chnl.startswith("Channels")):
            for i in range(2, len(df.columns)):
                if (((i - 1) % 2) == 0): df[i] = df[i].astype('category')

        # remove consecutive duplicate values from 'status' dataframes
        elif (chnl.startswith('status')):
            df = channels[chnl].data
            df['value'] = df['value'].astype('float')

            unique = ((df != df.shift(1)) | (df != df.shift(-1)))['value']

            channels[chnl].data = df[unique]
    return channels
