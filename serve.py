import math
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib
import pandas as pd
import io
import types
import traceback
import sys
import argparse

import injest
from channel import Channel
import helpers


def update_channel(chnl_to_update: str, channels: dict[str, Channel]):
    new_txt = channels[chnl_to_update].file.read()

    if (len(new_txt) != 0):
        dfs = injest.text_to_dfs(new_txt, chnl_to_update)

        for name in dfs:
            # create a new channel if it doesn't already exist
            if name not in channels:
                channels[name] = Channel(name)
                channels[name].file = channels[chnl_to_update].file

            channels[name].add_data(dfs[name])

            if (name.startswith('status')):
                channels[name].data = injest.remove_status_duplicates(
                    channels[name].data)


# Usual HTTPServer class, modified to let certain errors through
class Server(HTTPServer):
    def handle_error(self, request, client_address):
        # Get the current error
        e = sys.exception()

        # Reraise FolderChangeError, which ultimatly restarts the server
        if isinstance(e, helpers.FolderChangeError):
            raise e

        # Otherwise do the default behavior and keep serving
        print('-'*40, file=sys.stderr)
        print('Exception occurred during processing of request from',
              client_address, file=sys.stderr)
        traceback.print_exception(e)
        print('-'*40, file=sys.stderr)


def create_server(channels: dict[str, Channel],
                  args: argparse.Namespace,
                  request_callback: types.FunctionType | None = None,):
    class HTTP_request_handler(BaseHTTPRequestHandler):

        def do_GET(self):
            if (request_callback is not None):
                request_callback()

            request = urllib.parse.urlparse(self.path)

            # parse escaped characters (ex. '%3A' becomes ':')
            channel = urllib.parse.unquote(request.path)

            # ignore the leading '/'
            channel = channel.strip('/')

            # check to see if there is new data
            update_channel(channel, channels)

            full_df = channels[channel].data
            results = full_df

            # If there were query parameters, limit the search
            query = urllib.parse.parse_qs(request.query)
            if (query):
                start = query['from'][0]
                end = query['to'][0]

                results = results[start:end]

            # if there is nothing to show in the given time range,
            # return the entire range of data so that grafana still
            # has something to work with and can show the "zoom to data" button
            if (results.size == 0):
                results = full_df

            # include the one point before and after the range
            first_dt = results.index[0]
            last_dt = results.index[-1]
            s = max(full_df.index.get_loc(first_dt) - 1, 0)
            e = min(full_df.index.get_loc(last_dt) + 1, len(full_df.index) - 1)
            results = full_df[s:e + 1]

            # For large time scales, we can't return all the points
            # and still be performant. For now, we naïvely sample entries
            if (results.size > args.sample_threshold):
                interval = math.floor(
                    len(results.index) / args.sample_threshold)
                results = results[::interval]

            # make sure that the last point didn't get removed in the sampling
            new_last_dt = results.index[-1]
            desired_last_dt = full_df.index[e]
            if (new_last_dt != desired_last_dt):
                results = pd.concat((results, full_df[e:e+1]))

            # send results
            csv = results.to_csv()

            self.send_response(200)
            self.send_header('Content-Type', 'text/csv')
            self.end_headers()
            self.wfile.write(csv.encode())

    print(f"Serving at http://{args.hostname}:{args.port}/")
    print("Available endpoints:")
    for ch in sorted(channels.keys()):
        print(ch)
    print()

    return Server((args.hostname, args.port), HTTP_request_handler)


if __name__ == "__main__":
    print("""Example usage:
    import serve
    import injest

    channels = injest._dirs('url/to/data')
    
    serve.serve(channels)""")
