import math
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib
from datetime import datetime
import pandas as pd
import io
import injest
from channel import Channel
# import matplotlib.pyplot as plt

# approximate upper limit of entries in a response
# before points start to be sampled.
# Change this to change the server performance
SAMPLE_THRESHOLD = 4000

# Format for date queries, in spec with
# https://docs.python.org/3/library/datetime.html#format-codes
# should match what you've configured grafana to use
QUERY_FMT = "%Y-%m-%dT%H:%M:%S"

# Port of localhost on which to serve
PORT = 8080

def update_channel(channel: Channel):
    new_data = channel.file.read()

    if (len(new_data) != 0):
        new_df = pd.read_csv(io.StringIO(new_data), header=None)
        injest.prep_dataframe(new_df)
        channel.add_data(new_df)


def serve(channels: dict[Channel]):
    class HTTP_request_handler(BaseHTTPRequestHandler):
        def do_GET(self):
            request = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(request.query)

            # parse escaped characters (ex. '%3A' becomes ':')
            channel = urllib.parse.unquote(request.path)

            # ignore the leading '/'
            channel = channel.strip('/')

            start = query['from'][0]
            end = query['to'][0]

            # if the request extends past the current end to the data,
            # check to see if there is new data
            end_dt = datetime.strptime(end, QUERY_FMT)
            most_recent_entry = channels[channel].data.index[-1]

            if (end_dt > most_recent_entry): update_channel(channels[channel])

            results = channels[channel].data[start:end]

            # if there is nothing to show in the given time range,
            # return the entire range of data so that grafana still
            # has something to work with and can show the "zoom to data" button
            if (results.size == 0): results = channels[channel].data

            # For large time scales, we can't return all the points
            # and still be performant. For now, we naïvely sample entries
            if (results.size > SAMPLE_THRESHOLD):
                interval = math.floor(results.size / SAMPLE_THRESHOLD)
                results = results[::interval]

            csv = results.to_csv()

            # TODO: error handling, file not found

            self.send_response(200)
            self.send_header('Content-Type', 'text/csv')
            self.end_headers()
            self.wfile.write(csv.encode())
    

    httpd = HTTPServer(('localhost', PORT), HTTP_request_handler)

    print(f"Serving at http://localhost:{PORT}/")
    print("Available endpoints:")
    for ch in sorted(channels.keys()):
        print(ch)
    print()

    httpd.serve_forever()


if __name__ == "__main__":
    print("""Example usage:
    import serve
    import injest

    channels = injest._dirs('url/to/data')
    
    serve.serve(channels)""")

