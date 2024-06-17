# approximate upper limit of entries in a response
# before points start to be sampled.
# Change this to change the server performance
SAMPLE_THRESHOLD = 4000

# Format for date queries, in spec with
# https://docs.python.org/3/library/datetime.html#format-codes
# should match what you've configured grafana to use
QUERY_FMT = "%Y-%m-%dT%H:%M:%S"

# Port on which to serve
PORT = 8080

# Enable to only load files called 'CH1 T',
# to speed up data parsing while debugging
ONLY_LOAD_CH1_T = False
