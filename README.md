# AXS - RON Transmitter

*AXS Claiming is not included*

**Requirements**
- python 3.11

**Installation**
``pip install -r requirements.txt``

**Functionalities**
- Send RON to manager's axie accounts
- Collect the claimed AXS's from the axie accounts and put it in manager's designated addresses for each scholar

Sending RON to manager's axie accounts incase there are no remaining RON left in the axie account. It will send a .1 RON to the address
``python3 send_token.py json_configs/axieaccounts.json RON``
	

Collect the claimed AXS's from the axie accounts and put it in manager's designated addresses for each scholar
``python3 send_token.py json_configs/axieaccounts.json AXS``

