# 📡 SNR

Server Nitro Ranker, or just SNR, is an auxiliary tool for [RNS](https://github.com/Melonai/rust-nitro-sniper) that helps you get a better understanding of the Nitro sniping value of the Discord servers you're currently in.

## Scoring System

SNR assigns a server a score taking into account multiple important factors that we've found to be important. These are for example the timings for every Nitro drop that has occurred on the server, the calculated probability of the legitimacy of said drop and even the server count.

Generally scores below 1 are bad, scores above 2 are good.

Please note that even though SNR strives to give each server the rating it deserves, you will have to use your common sense to determine whether a server is actually good for sniping or not, don't rely just on SNR to work for you.

## Installation

Use [pip](https://pip.pypa.io/en/stable/) to install the requirements.

```bash
pip3 install -r requirements.txt
```

## Running
1. Run the main script.
```bash
python3 snr.py
```

2. Input the token the guilds of which you want to scan.
```bash
Please input the token you want to scan: <PASTE_YOUR_TOKEN_HERE>
```

3. Pick the mode SNR will operate in.
```bash
Pick mode (1 - Scan All, 2 - Scan One, 3 - Live Scan): 1/2/3
```
* `Scan All` checks every server the token's account is in and creates a ranked leaderboard of the best servers.
* `Scan One` will prompt you for the guild ID of the one server you want to get the score of.
* `Live Scan` will give you a score for every new server that you join while SNR is running.

---
#### Disclaimer

We must state that any usage of this tool with your personal user account token is a breach of the Discord Terms of Service, and we, the developers of SNR, will not take responsibility for any punishment (e.g. permanent ban) your account(s) could receive for using it.

/ᐠ｡ꞈ｡ᐟ\ **Thanks for reading!**