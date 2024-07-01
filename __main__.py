import sys
import injest
import serve
import helpers
# import pandas as pd

def main():
    url = sys.argv[1]

    while True:
        print('Building Data...')

        date_dirs = injest.chldrn_labeled_with_date(url)

        # All data is stored in the channels dictionary
        channels = injest.injest_date_dirs(date_dirs)

        # checks to see if the number of folders has changed,
        # and if it has, throws an error 
        def check_for_new_day():
            new_date_dirs = injest.chldrn_labeled_with_date(url)
            if (len(new_date_dirs) != len(date_dirs)):
                raise helpers.FolderChangeError

        print()
        print("Starting Server...")

        # Start the server
        httpd = serve.create_server(channels, check_for_new_day)

        try:
            httpd.serve_forever()

        # When folders change, restart the whole loop
        except helpers.FolderChangeError:
            print('The number of folders changed; shutting down with the hope of restarting')
            httpd.shutdown()
            httpd.server_close()

        # On any other error, close the open files and reraise
        except:
            print('Encountered an error, closing files')
            for c in channels:
                if (channels[c].file is not None): channels[c].file.close()
                raise


if (__name__ == "__main__"): main()
