import requests
import json
import subprocess
import os
import time
import signal
import columnar

from spartan.utils import post, get

BASE_URL = 'http://127.0.0.1:8081'
API_SETUP = 1
API_COOLDOWN = 5

# Generate a JSON dump with all access points info
def request_aps():
    # Start the Bettercap WiFi module
    post('wifi.recon on')

    # JSON with the APs information
    aps_request = get('session/wifi')
    aps_json = json.loads(aps_request.text)['aps']

    return aps_json

# Generate a table with the available access points
def show_aps(args):
    print('\nScanning the available wireless spectrum...')
    aps_json = request_aps()

    # Generate a columnar table to show the APs info
    headers = ['rssi', 'essid', 'bssid', 'clients', 'encryption', 'auth', 'cipher']
    ap_data = []
    for ap in aps_json:
        n_clients = len(ap['clients'])
        if not args.clients:
            ap_data.append([str(ap['rssi']) + ' dBm', ap['hostname'], ap['mac'], n_clients, ap['encryption'], ap['authentication'], ap['cipher']])
        elif args.clients and (n_clients > 0):
            ap_data.append([str(ap['rssi']) + ' dBm', ap['hostname'], ap['mac'], n_clients, ap['encryption'], ap['authentication'], ap['cipher']])

    if ap_data:
        ap_data.sort()
        ap_table = columnar.columnar(ap_data, headers, no_borders=True)
        print(ap_table)


# Start scanning the available wireless spectrum
def start(args):
    # Deploy the Bettercap API
    bettercap = subprocess.Popen(['bettercap', '-caplet', 'http-ui'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(API_SETUP) # Time needed to start requesting data without errors

    try:
        if args.refresh:
            # Refresh the scanner indefinitely
            while(True):
                show_aps(args)
                time.sleep(API_COOLDOWN)
        else:
            show_aps(args)

    except Exception as e:
        print(e)

    # Stop the Bettercap API
    finally:
        try:
            os.killpg(os.getpgid(bettercap.pid), signal.SIGTERM)
        except ProcessLookupError:
            exit()
