import math
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib
from datetime import datetime
import pandas as pd
import io
import types
import traceback
import sys

import injest
from channel import Channel
import helpers
import config


def update_channel(channel: Channel):
    new_data = channel.file.read()

    if (len(new_data) != 0):
        new_df = pd.read_csv(io.StringIO(new_data), header=None)
        injest.prep_dataframe(new_df, 0, "%d-%m-%y", 1, "%H:%M:%S")
        channel.add_data(new_df)


# Usual HTTPServer class, modified to let certain errors through
class Server(HTTPServer):
    def handle_error(self, request, client_address):
        # Get the current error
        e = sys.exception()

        # Reraise FolderChangeError, which ultimatly restarts the server
        if isinstance(e, helpers.FolderChangeError): raise e

        # Otherwise do the default behavior and keep serving
        print('-'*40, file=sys.stderr)
        print('Exception occurred during processing of request from',
            client_address, file=sys.stderr)
        traceback.print_exception(e)
        print('-'*40, file=sys.stderr)


def create_server(channels: dict[Channel], request_callback: types.FunctionType | None = None):
    class HTTP_request_handler(BaseHTTPRequestHandler):

        def do_GET(self):
            if (request_callback is not None): request_callback()

            request = urllib.parse.urlparse(self.path)

            # parse escaped characters (ex. '%3A' becomes ':')
            channel = urllib.parse.unquote(request.path)

            # ignore the leading '/'
            channel = channel.strip('/')

            # check to see if there is new data
            update_channel(channels[channel])

            results = channels[channel].data

            # If there were query parameters, limit the search
            query = urllib.parse.parse_qs(request.query)
            if (query):
                start = query['from'][0]
                end = query['to'][0]
                
                results = results[start:end]

            # if there is nothing to show in the given time range,
            # return the entire range of data so that grafana still
            # has something to work with and can show the "zoom to data" button
            if (results.size == 0): results = channels[channel].data

            # For large time scales, we can't return all the points
            # and still be performant. For now, we naïvely sample entries
            if (results.size > config.SAMPLE_THRESHOLD):
                interval = math.floor(results.size / config.SAMPLE_THRESHOLD)
                results = results[::interval]

            csv = results.to_csv()

            # TODO: error handling, file not found

            self.send_response(200)
            self.send_header('Content-Type', 'text/csv')
            self.end_headers()
            self.wfile.write(csv.encode())
    

    print(f"Serving at http://localhost:{config.PORT}/")
    print("Available endpoints:")
    for ch in sorted(channels.keys()):
        print(ch)
    print()

    return Server(('localhost', config.PORT), HTTP_request_handler)


if __name__ == "__main__":
    print("""Example usage:
    import serve
    import injest

    channels = injest._dirs('url/to/data')
    
    serve.serve(channels)""")

