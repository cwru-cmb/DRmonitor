import sys
import os
import re
import pandas as pd
import warnings
# import matplotlib.pyplot as plt
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib


# Usage example
# $ python3 serve.py "Run 19 Logs"
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


    for dir in dirs:
        print(f"Parsing {dir.path}")

        day = dir.name
        # TODO: reenable this line
        # print(f'Injesting contents of folder {day}')
        datafiles = os.scandir(dir.path)
        for df in datafiles:
            # warn if the file is not named like the usual pattern
            if (not df.name.endswith(f'{day}.log')):
                warnings.warn(f'The file {df.path} is not of the form "[name] {day}.log" and will be ignored')
        
            # TODO deal with Status_ files seperately
            elif (df.name.startswith('Status_')):
                pass
            # temporarily only consider channel 1
            # elif (not df.name.startswith('CH1 T')):
            #     pass
            else:
                chnl_name = df.name[:-12].strip()
                data = pd.read_csv(df.path, header=None)

                if chnl_name not in channels:
                    channels[chnl_name] = data
                else:
                    channels[chnl_name] = pd.concat((channels[chnl_name], data))
        
    for chnl in channels:
        prep_dataframe(channels[chnl])
    
    return channels

# TODO: lakeshore, etc.

url = sys.argv[1]

print('Building Data...')

channels = concatenate_date_dirs(url)

print('Available channels:')
for ch in channels:
    print(ch)

print()
print("Serving...")

class HTTP_request_handler(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(u.query)

        # parse escaped characters (ex. '%3A' --> ':')
        channel = urllib.parse.unquote(u.path)

        # ignore the leading '/'
        channel = channel[1:]

        start = query['from'][0]
        end = query['to'][0]
        results = channels[channel][start:end]

        csv = results.to_csv()

        # TODO: error handling, file not found

        self.send_response(200)
        self.send_header('Content-Type', 'text/csv')
        self.end_headers()
        self.wfile.write(csv.encode())

if __name__ == "__main__":
    httpd = HTTPServer(('localhost', 8080), HTTP_request_handler)
    httpd.serve_forever()

# channels['CH1 T']["2023-04-22T10:36:20":"2023-04-22T15:38:59"][2].plot()
# plt.show()






