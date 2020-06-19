# Wi-Fi Spartan ⚔️
Smart pentesting toolkit for modern WPA/WPA2 networks ⚔️📡

![alt text](https://github.com/javiln8/wifi_spartan/blob/master/images/logo.png?raw=true)

### Requirements
The toolkit uses `bettercap` as its backend framework for attacking networks. Can be installed with any packet manager.

### Usage
Run `python3 wifi_spartan.py --help` to see all available commands and options. To see all available options of a function, run `python3 wifi_spartan.py <module> --help`.

Wi-Fi spartan modules:
- [x] `scan`: wireless spectrum scanner
- [x] `deauth`: deauthentication attack to attempt to capture the 4-way handshake
- [x] `pmkid`: PMKID client-less attack
- [x] `spoof scan`: local network hosts scanner
- [x] `spoof spy`: MiTM attack with ARP spoofing
- [x] `automata`: wardriving automation with deep reinforcement learning techniques.


### Future implementations
- [ ] `jam`: WiFi jamming with packet flooding
- [ ] `rogue`: Evil Twin attack
- [ ] `crack`: dictionary attack to attempt to crack the PSK

### References

- Deep learning model applied to wardriving inspired by [evilsocket/pwnagotchi](https://github.com/evilsocket/pwnagotchi).
