import sys
import injest
import serve

url = sys.argv[1]

print('Building Data...')

# All data is listed in the channels object
# TODO: channels should have their own class
channels = injest.injest_date_dirs(url)

print()
print("Starting Server...")

serve.serve(channels)
