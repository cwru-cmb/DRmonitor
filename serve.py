import sys
import os
import re

# Usage example
# $ python3 serve.py "Run 19 Logs"


url = sys.argv[1]

contents = os.scandir(url)


def chldrn_labeled_with_date(dir_contents):
    # dir_contents: results of os.scandir(path)
    # returns the only directories labeled with ##-##-##

    p = re.compile('^\d\d-\d\d-\d\d$')
    return [ child for child in dir_contents if (p.match(child.name) and child.is_dir()) ]


def concatenate_chnl_runs(dir_contents):
    # dir_contents: results of os.scandir(path)
    # 

    dirs = chldrn_labeled_with_date(dir_contents)

    for dir in dirs:
        day = dir.name
        datafiles = os.scandir(dir.path)
        for df in datafiles:
            print(df.name)
            # WORKING ON: using pandas to concatinate the data
            # We'll see if this uses too much memory and speed or is ok



concatenate_chnl_runs(contents)