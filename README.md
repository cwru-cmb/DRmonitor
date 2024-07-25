# README
This library is used to view the log files from BLUEFORS using tools like Grafana.

![hero](https://github.com/user-attachments/assets/2d49d38f-06b1-455d-a379-05de45fdfe83)

## Installation
It is recommended to install and activate a virtual environment. Make a copy of this repository and inside run:
```bash
% python -m venv .venv
% source ./.venv/bin/activate
```
Then install the required packages.
```bash
% python -m pip install -r requirements.txt
```
After packages are installed, the server is ready to start. Run the contents of this folder (either with `python .` or by moving up in hirarchy and calling the entire folder) with the relative or absolute path to the BLUEFORS logs as an argument.
```bash
% cd ..
% python DRmonitor "../Run 19 Logs"
```
The output should be something like:
```
Building Data...
Parsing ../Run 19 Logs/23-04-18
Parsing ../Run 19 Logs/23-04-16
Parsing ../Run 19 Logs/23-04-17
[...]
Preparing...

Starting Server...
Serving at http://localhost:8080/
Available endpoints:
CH1 P
CH1 R
CH1 T
Channels
Flowmeter
Heaters
maxigauge
[...]
```

## Usage
This library automatically reads all data saved in the pattern
```
Run 19 Logs/
 ├─ 23-04-28/
 │   ├─ CH1 T 23-04-28.log
 │   ├─ CH2 T 23-04-28.log
 │   └─ Flowmeter 23-04-28.log
 ├─ 23-04-26/
 │   ├─ CH1 T 23-04-26.log
 │   ├─ CH2 T 23-04-26.log
 │   └─ Flowmeter 23-04-26.log
 └─ 23-04-27/
     ├─ CH1 T 23-04-27.log
     ├─ CH2 T 23-04-27.log
     └─ Flowmeter 23-04-27.log
```
Where `.log` files are CSVs with the first two colunms being dates (DD-MM-YY) and times (HH:mm:ss). For example, in `CH1 T 23-04-26.log` is:
```
28-04-23,00:00:04,2.915210e+02
28-04-23,00:00:14,2.915210e+02
28-04-23,00:00:24,2.915210e+02
[...]
```
`.log` files may have more columns, so long as the first two are date and time.

After building the data, this library starts a server on whichever port is configured in [`config.py`](config.py) (default 8080).

To read data, send a `GET` request to the server with the appropiate endpoint for the files you want.

> [!WARNING]
> By default, requests that return too many rows are naively downsampled. This could obfuscate or completely hide important features on anything but the smallest timescales. The row threshold is set in [`config.py`](config.py), and defaults to 4000.

> Ex. To get all the data from files named 'CH1 T [DD-MM-YY].log' from a server on the default port, the endpoint would be `CH1 T`, and the full url (with proper url encoding) would be `http://localhost:8080/CH1%20T`. 

To only get data within a certain time range, use the query parameters `from` and `to` with datetimes formatted as configured in [`config.py`](config.py) (default YY-MM-DDTHH:mm:ss)

> Ex. If you wanted CH1 T data between April 24, 2023 01:35:27 and April 27, 2023 00:09:24, `from` would be `2023-04-24T01:35:27`, `to` would be `2023-04-27T00:09:24`, and the full url (properly encoded) would be `http://localhost:8080/CH1%20T?from=2023-04-24T01%3A35%3A27&to=2023-04-27T00%3A09%3A24`

If no data is available for a given query, data over the entire time range is returned.

Data is returned as a CSV with the same columns as the original, plus an additional 'datetime' column.


## Integration with Grafana
### Installing Grafana
To install a self-hosted version of grafana, follow [the instructions on the Grafana website](https://grafana.com/docs/grafana/latest/setup-grafana/installation/), then open grafana's local site (defaults to http://localhost:3000/) in a browser. If prompted for a username and password, use `admin` and `admin`. Skip any password changes.
