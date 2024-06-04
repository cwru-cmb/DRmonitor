import sys
import injest
import serve

url = sys.argv[1]

print('Building Data...')

# All data is listed in the channels object
# TODO: channels should have their own class
channels = injest.concatenate_date_dirs(url)

print('Available channels:')
for ch in sorted(channels.keys()):
    print(ch)

print()
print("Serving...")

serve.serve(channels)
