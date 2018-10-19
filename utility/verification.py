"""provides verification helpers."""
 
from utility.hash_util import hash_block, hash_string_256
from wallet import Wallet

class Verification:

    @staticmethod #itsnot assceing anything from the class 
    def valid_proof(transcations, last_hash, proof):
        
        #creating a string with all the hash inputs 
        guess = (str([tx.to_ordered_dict() for tx in transcations ]) +str(last_hash) + str(proof)).encode()
        guess_hash = hash_string_256(guess)
        print(guess_hash)
        return guess_hash[0:2] == '00'

    @classmethod #these are decorators, it needs something from the class 
    def verify_chain(cls, blockchain):
        for (index, block)in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.transcations[:-1], block.previous_hash, block.proof):
                print('proof of work invalid')
                return False
        return True
    
    @staticmethod
    def verify_transcation( transcation, get_balance, check_funds = True):
        if check_funds:
            sender_balance = get_balance(transcation.sender)
            return sender_balance >= transcation.amount and Wallet.verify_transcation(transcation)
        else:
            return Wallet.verify_transcation(transcation)

    @classmethod
    def verify_transcations(cls, open_transcations, get_balance):
        return all([cls.verify_transcation(tx, get_balance) for tx in open_transcations])
    
    