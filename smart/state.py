# Reward function of the reinforcement learning process
class RewardFunction(object):
    def __call__(self, total_states, state_data):
        total_interactions = max(state_data['deauths'], state_data['handshakes']) + 1e-20
        total_channels = 140

        shakes = state_data['handshakes'] / total_interactions
        hops   = 0.1 * (state_data['hops'] / total_channels)
        misses = -0.3 * (state_data['misses'] / total_interactions)
        #new_aps = +0.3 * (state_data['new_aps'] / total_interactions)

        return shakes + hops + misses #+ new_aps

# Information about each wardrive state (state = one loop of wardrive session)
class State(object):
    def __init__(self, parameters):
        self.state = 0
        self.parameters = parameters

        self.did_deauth = False
        self.deauths = 0
        self.misses = 0
        self.new_aps = 0
        self.handshakes = 0
        self.hops = 0

        self.reward = RewardFunction()
        self.state_data = {}

    # Track usefuel state statistics
    def track(self, deauth=False, handshake=False, hop=False, miss=False, new=False, increment=1):
        if deauth:
            self.deauths += increment
            self.did_deauth = True
        if miss:
            self.misses += increment
        if hop:
            self.hops += increment
        if handshake:
            self.handshakes += increment
        if new:
            self.new_aps += increment

    # Rotate the state
    def next_state(self):
        self.state_data = {
            'hops': self.hops,
            'deauths': self.deauths,
            'handshakes': self.handshakes,
            'misses': self.misses,
            #'new_aps': self.new_aps,
        }

        self.state_data['reward'] = self.reward(self.state + 1, self.state_data)

        print('\nSTATE:' + str(self.state))
        print('Number of channel hops: ' + str(self.hops))
        print('Number of deauths: ' + str(self.deauths))
        print('Number of captured handshakes: ' + str(self.handshakes))
        print('Number of missed APs: ' + str(self.misses))
        print('Number of discovered new APs: ' + str(self.new_aps))
        print('Reward: ' + str(self.state_data['reward']) + '\n')

        self.state += 1
        self.did_deauth = False
        self.deauths = 0
        self.misses = 0
        self.new_aps = 0
        self.handshakes = 0
        self.hops = 0
