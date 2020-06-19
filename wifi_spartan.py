#!/usr/bin/env python3

from spartan import scan
from spartan import capture
from spartan import crack
from spartan import automata
from spartan import spoof

import argparse

# Main function
def start():
    # Generate the arguments/options parser for the toolkit
    parser = argparse.ArgumentParser(description='Smart pentest toolkit for modern WPA/WPA2 networks.')
    subparsers = parser.add_subparsers(help='Available commands')

    # Option for the scan module
    parser_scan = subparsers.add_parser('scan', help='Scan the available 802.11 wireless spectrum')
    parser_scan.add_argument('-r', '--refresh', action='store_true', help='Update the scanner every few seconds')
    parser_scan.add_argument('-c', '--clients', action='store_true', help='Only show APs with clients connected')
    parser_scan.set_defaults(function=scan.start)

    # Option for the deauthentication attack module
    parser_deauth = subparsers.add_parser('deauth', help='Attempt to capture 4-way handshake given a BSSID')
    parser_deauth.add_argument('bssid', help='target BSSID')
    parser_deauth.set_defaults(function=capture.start_deauth)

    # Option for the PMKID client-less attack module
    parser_pmkid = subparsers.add_parser('pmkid', help='Attempt to capture PMKID keys of all available access points (helps to scan more APs)')
    parser_pmkid.set_defaults(function=capture.start_assoc)

    # Option for the crack module
    #parser_crack = subparsers.add_parser('crack', help='Dictionary attack to attempt to crack the PSK')
    #parser_crack.add_argument('file', help='Path to the target .hccapx or .pcap file')
    #parser_crack.add_argument('-e', '--email', help='Valid email to send results')
    #parser_crack.set_defaults(function=crack.start)

    # Option for the wardrive module
    parser_automata = subparsers.add_parser('automata', help='Automated smart wardrive session, powered by reinforcement learning')
    parser_automata.set_defaults(function=automata.start)

    # Option for the spoof/MiTM module
    parser_spoof = subparsers.add_parser('spoof', help='Man in the Middle attack with ARP spoofing')
    subparser_spoof = parser_spoof.add_subparsers(help='Commands for the Man in the Middle attack vector')

    parser_spoof_scan = subparser_spoof.add_parser('scan', help='Scan and display the hosts of the local network')
    parser_spoof_scan.set_defaults(function=spoof.start_scan)

    parser_spoof_spy = subparser_spoof.add_parser('spy', help='Start the ARP spoofing and sniff the victims traffic')
    parser_spoof_spy.add_argument('target', help='Target IP address to spoof and sniff its traffic (* to attack the whole subnet)')
    parser_spoof_spy.add_argument('-p', '--proxies', action='store_true', help='Deploy HTTP and HTTPS proxies to redirect victims traffic')
    parser_spoof_spy.add_argument('-d', '--dns', action='store_true', help='Spoof DNS queries to redirect to the custom addresses (dns.spoof.hosts file)')
    parser_spoof_spy.set_defaults(function=spoof.start_spy)

    args = parser.parse_args()
    print(args.function(args))


if __name__ == '__main__':
    start()
