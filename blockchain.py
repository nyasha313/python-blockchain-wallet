from functools import reduce # to avoid importing the whole libaray
import hashlib as hl

import json
import pickle 
import requests

from utility.hash_util import hash_block
from utility.verification import Verification
from block import Block
from transcation import Transcation
from wallet import Wallet


MINING_REWARD = 10

print(__name__)

class BlockChain:
    def __init__(self, public_key, node_id):
        genesis_block = Block(0, '', [], 100, 0 )
        #initialising empty blockchain list  
        self.chain = [genesis_block]
        #unhandled transcations 
        self.__open_transcations = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.load_data()

    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_transcations(self):
        return self.__open_transcations[:]

    def load_data(self):
        try:
            with open('BlockChain-{}.txt'.format(self.node_id), mode = 'r') as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transcation(tx['sender'], tx['recipient'],tx['signature'],tx['amount']) for tx in block['transcations']]
                    updated_block = Block(block['index'],block['previous_hash'],converted_tx, block['proof'],block['timestamp'] )
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                open_transcations = json.loads(file_content[1][:-1])
                updated_transcations = []
                for tx in open_transcations:
                    updated_transcation = Transcation(tx['sender'], tx['recipient'],tx['signature'], tx['amount'])
                    updated_transcations.append(updated_transcation)
                self.__open_transcations = updated_transcations
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError): 
            pass
        finally:
            print('clean up!')


    def save_data(self):
        try:
            with open('BlockChain-{}.txt'.format(self.node_id), mode = 'w') as f:
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [tx.__dict__ for tx in block_el.transcations] ,block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transcations]
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))

        except IOError:
            print('Saving Failed!!')


    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        #try diffrent POw numbers and return the first valid number 
        while not Verification.valid_proof(self.__open_transcations, last_hash, proof):
            proof += 1
        return proof


    def get_balance(self, sender = None):

        if sender == None:
            if self.public_key == None:
                return None
            participant = self.public_key
        else:
            participant = sender

        tx_sender = [[tx.amount for tx in  block.transcations if tx.sender == participant] for block in self.__chain]
        open_tx_sender = [tx.amount for tx in  self.__open_transcations if tx.sender == participant] 
        tx_sender.append(open_tx_sender) 
        print(tx_sender)
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)
        tx_recipient = [[tx.amount for tx in  block.transcations if tx.recipient == participant] for block in self.__chain]
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)
        return amount_received - amount_sent
    
    def get_last_value(self):
        if len(self.__chain) < 1:
            return None  #returns nothing 
        return self.__chain[-1]

    def add_value(self,  recipient, sender, signature , amount=1.0, is_reciving = False): #adding transaction
       

    #    """  transcation = {'sender': sender, 
    #     'recipient': recipient, 
    #     'amount': amount} """
        if self.public_key == None:
            return False
        transcation = Transcation(sender, recipient,signature, amount)
        if Verification.verify_transcation(transcation, self.get_balance): 
            self.__open_transcations.append(transcation)
            self.save_data()
            if not is_reciving:  
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transcation'.format(node)
                    try:
                        response = requests.post(url, json={'sender': sender, 'recipient': recipient, 'amount': amount, 'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transcation declined, needs resolving')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def mine_block(self):
        if self.public_key == None:
            return None 
        last_block = self.__chain[-1]
        hashed_block = hash_block(last_block) 
        proof = self.proof_of_work()
        """ reward_trascation = {'sender': 'MINING',
                            'recipient': owner,
                            'amount': MINING_REWARD} """

        reward_trascation = Transcation('MINING', self.public_key ,'', MINING_REWARD) # every time i mine i get a new unique id for evry user
        copied_transcations = self.__open_transcations[:]
        for tx in copied_transcations:
            if not Wallet.verify_transcation(tx):
                return None
        copied_transcations.append(reward_trascation)
        block = Block(len(self.__chain),hashed_block,copied_transcations, proof)
        self.__chain.append(block)
        self.__open_transcations = []
        self.save_data()
        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = block.__dict__.copy()
            converted_block['transcations'] = [
                tx.__dict__ for tx in converted_block['transcations']]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block
    

    def add_block(self, block):
        """Add a block which was received via broadcasting to the localb
        lockchain."""
        # Create a list of transaction objects
        transcations = [Transcation(
            tx['sender'],
            tx['recipient'],
            tx['signature'],
            tx['amount']) for tx in block['transcations']]
        # Validate the proof of work of the block and store the result (True
        # or False) in a variable
        proof_is_valid = Verification.valid_proof(
            transcations[:-1], block['previous_hash'], block['proof'])
        # Check if previous_hash stored in the block is equal to the local
        # blockchain's last block's hash and store the result in a block
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        # Create a Block object
        converted_block = Block(
            block['index'],
            block['previous_hash'],
            transactions,
            block['proof'],
            block['timestamp'])
        self.__chain.append(converted_block)
        stored_transcations = self.__open_transcations[:]
        # Check which open transactions were included in the received block
        # and remove them
        # This could be improved by giving each transaction an ID that would
        # uniquely identify it
        for itx in block['transcations']:
            for opentx in stored_transcations:
                if (opentx.sender == itx['sender'] and
                        opentx.recipient == itx['recipient'] and
                        opentx.amount == itx['amount'] and
                        opentx.signature == itx['signature']):
                    try:
                        self.__open_transcations.remove(opentx)
                    except ValueError:
                        print('Item was already removed')
        self.save_data()
        return True

    def add_peer_node(self, node):
        #addds a new node to the peer node set , node url which should be added
        self.__peer_nodes.add(node)
        self.save_data

    def remove_peer_node(self, node):
        self.__peer_nodes.discard(node)  #removes a node 
        self.save_data()

    def get_peer_nodes(self):
        return list(self.__peer_nodes)

