import sys
import os
import re
import pandas as pd
import warnings

# Usage example
# $ python3 serve.py "Run 19 Logs"


url = sys.argv[1]

contents = os.scandir(url)


def chldrn_labeled_with_date(dir_contents):
    # dir_contents: results of os.scandir(path)
    # returns the only directories labeled with ##-##-##

    p = re.compile(r'^\d\d-\d\d-\d\d$')
    return [ child for child in dir_contents if (p.match(child.name) and child.is_dir()) ]


def concatenate_chnl_runs(dir_contents):
    # dir_contents: results of os.scandir(path)

    dirs = chldrn_labeled_with_date(dir_contents)

    channels = {}

    for dir in dirs:
        day = dir.name
        datafiles = os.scandir(dir.path)
        for df in datafiles:
            # warn if the file is not named like the usual pattern
            if (not df.name.endswith(f'{day}.log')):
                warnings.warn(f'The file {df.path} is not of the form "[name] {day}.log" and will be ignored')
            elif (df.name.startswith('Status_')):
                print('ignoring status file for now')
            else:
                chnl_name = df.name[:-12]
                data = pd.read_csv(df.path, header=None)

                if chnl_name not in channels:
                    channels[chnl_name] = data
                else:
                    channels[chnl_name] = pd.concat((channels[chnl_name], data))
    
    return channels

concatenate_chnl_runs(contents)