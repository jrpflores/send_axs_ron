from web3 import Web3
from dotenv import load_dotenv
import os
import json
from collections import namedtuple 
import sys
from pprint import pprint
import asyncio
load_dotenv()

WALLET_ADDRESS = os.getenv("MANAGER_USER_ADDRESS")
PRIV_KEY = os.getenv("MANAGER_PRIVATE_KEY")
RONIN_RPC_URL = os.getenv("RONIN_RPC") 
SKIP_ACCOUNTS = []

web3 = Web3(Web3.HTTPProvider(RONIN_RPC_URL))
AXS_CONTRACT_ADDRESS = Web3.to_checksum_address("0x97a9107C1793BC407d6F527b77e7fff4D812bece")
#  ERC-20 ABI for AXS
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
    "constant": False,
    "inputs": [
      {
        "internalType": "address",
        "name": "_to",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "_value",
        "type": "uint256"
      }
    ],
    "name": "transfer",
    "outputs": [
      {
        "internalType": "bool",
        "name": "_success",
        "type": "bool"
      }
    ],
    "payable": False,
    "stateMutability": "nonpayable",
    "type": "function"
  }
]
axs_contract = web3.eth.contract(address=Web3.to_checksum_address(AXS_CONTRACT_ADDRESS), abi=ERC20_ABI)
if not web3.is_connected():
    raise Exception("Unable to connect to the Ronin network")

def get_ron_balance(address):
    # Ensure the address is a valid checksum address
    checksum_address = Web3.to_checksum_address(address)
    
    # Get the balance in Wei (1 RON = 10^18 Wei)
    balance_wei = web3.eth.get_balance(checksum_address)
    
    # Convert Wei to RON (1 RON = 10^18 Wei)
    balance_ron = web3.from_wei(balance_wei, 'ether')
    
    return balance_ron
async def send_RON(name, recipient_address, amount = 0.1):
    print(f"Sending RON to {name} ({recipient_address}")
    # Amount to send in Wei (1 RON = 10^18 Wei)
    amount_in_wei = web3.to_wei(amount, 'ether')
    nonce = web3.eth.get_transaction_count(Web3.to_checksum_address(WALLET_ADDRESS), 'pending')

    # Transaction details
    gas_price = web3.eth.gas_price
    tx = {
        'nonce': nonce,
        'to': recipient_address,
        'value': amount_in_wei,
        'gas': 21000,  # Standard gas limit for transfers
        'gasPrice': gas_price,  # Adjust gas price based on network conditions
        'chainId': 2020  # Ronin mainnet chain ID
    }

    # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(tx, PRIV_KEY)
    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    # Print the transaction hash
    print(f"Transaction sent successfully to {name}! Tx hash: {web3.to_hex(tx_hash)}")

async def process_RON(accounts, skipped_accounts):
   for index, account in enumerate(accounts):
        account_name = account["Name"]
        account_address = Web3.to_checksum_address(account["AccountAddress"])
        ron_balance = float(get_ron_balance(account_address))
        print(f"Balance: {ron_balance}")
        if any(
            (index+1 == item if isinstance(item, int) else index+1 in range(item[0], item[1] + 1))
            for item in skipped_accounts
        ):
            continue
        if(ron_balance >= 0.01):
           continue

        try:
            await send_RON(account_name, account_address, 0.1)
            # print("")
        except Exception as e:
           print(f"An error occurred {e}")

##### end of RON


def get_axs_balance(address):
    # Convert address to checksum format
    address = Web3.to_checksum_address(address)
    # Call the balanceOf method
    balance_wei = axs_contract.functions.balanceOf(address).call()
    # Get decimals for the token
    decimals = axs_contract.functions.decimals().call()
    # Convert balance to human-readable format
    balance = balance_wei
    return balance

async def send_AXS(name, account_address, receipient_address, private_key, amount):
    # Get the current nonce
    nonce = web3.eth.get_transaction_count(Web3.to_checksum_address(account_address), 'pending')
    gas_price = web3.eth.gas_price
    # Estimate gas for the transaction
    try:
        gas_estimate = axs_contract.functions.transfer(receipient_address, amount).estimate_gas({
            'from': account_address,
        })
    except Exception as e:
        print(f"Error estimating gas: {e}")
        exit()
    # Build the transaction
    print(f"Gas fee estimate: {gas_estimate}")
    transaction = axs_contract.functions.transfer(receipient_address, amount).build_transaction({
        'chainId': 2020,  # Ronin chain ID
        'gas': gas_estimate,  # Use the estimated gas
        'gasPrice': gas_price,
        'nonce': nonce,
    })
    # Sign the transaction
    signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
    # Send the transaction
    transaction_hash = web3.eth.send_raw_transaction(signed_transaction.raw_transaction)
    print(f"Transaction sent successfully to {name}! Tx hash: {web3.to_hex(transaction_hash)}")
   
async def process_AXS(accounts, skipped_accounts):
   for index, account in enumerate(accounts):
        account_name = account["Name"]
        account_address = Web3.to_checksum_address(account["AccountAddress"])
        scholar_payout = Web3.to_checksum_address(account["ScholarPayoutAddress"])
        private_key = account["PrivateKey"]
        balance = get_axs_balance(account_address)
        print(f"Account: {account_name}, Sender's balance: {balance / (10 ** 18)}, gwei: {balance} AXS")
        if balance > 0:
            try:
                await send_AXS(account_name, account_address, receipient_address=scholar_payout,private_key=private_key, amount=balance )
            except Exception as e:
                print(f"An error occurred {e}")

async def process_accounts(accounts, skipped_accounts, token="RON"):
   if len(accounts) == 0:
      print("No accounts")
      return 0
   
   match token: 
    case "RON":
        return await process_RON(accounts, skipped_accounts)
    case "AXS":
         return await process_AXS(accounts, skipped_accounts)
    case _:
        return "Invalid token"
   
        


async def main():
   token = "RON"
   if (len(sys.argv) < 2):
    print("Please specify the path to the json config file as parameter.")
    exit()

   if len(sys.argv) > 2 and sys.argv[2]:
        token = sys.argv[2]

   with open(sys.argv[1]) as f:
    accounts = json.load(f)
   
   await process_accounts(accounts["Scholars"], SKIP_ACCOUNTS, token)


if __name__ == "__main__":
    asyncio.run(main())

