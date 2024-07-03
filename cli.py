import argparse

def get_arguments() -> argparse.Namespace:
    description = "Reads the logs from a Bluefors fridge and serves them for querying"

    parser = argparse.ArgumentParser(description=description,
                                        prog='DRmonitor',)
    parser.add_argument('path',
                        metavar='PATH',
                        help="The path to the directory containing the logs")

    parser.add_argument('--host', '--hostname',
                    help="The hostname or IP address to bind to",
                    default='localhost',
                    type=str,
                    dest='hostname',
                    metavar='HOSTNAME',
                    required=False)

    parser.add_argument('-p', '--port',
                        help="The port to serve from",
                        default=8080,
                        type=int,
                        dest='port',
                        required=False)

    parser.add_argument('-l', '--point_limit',
                        metavar="N",
                        help="""Approximate upper limit of entries in a response
                        before points start to be sampled. Change this to change
                        the server performance""",
                        type=int,
                        default=4000,
                        dest='sample_threshold',
                        required=False)
    
    return parser.parse_args()