from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 
from Crypto.Hash import SHA256
import Crypto.Random
import binascii

class Wallet:
    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.node_id = node_id

    def create_keys(self):
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key
      

    def load_keys(self):
        try:
            with open('wallet-{}.txt'.format(self.node_id), mode = 'r') as f:
                keys = f.readlines()
                public_key = keys[0][:-1]
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except (IOError,IndexError):
            print('Loading wallet failed ...')
            return False

    def save_keys(self):
        if self.public_key != None and self.private_key != None:
            try:
                with open('wallet-{}.txt'.format(self.node_id), mode = 'w') as f:
                    f.write(self.public_key)
                    f.write('\n')
                    f.write(self.private_key)
                return True
            except (IOError,IndexError):
                print('saving wallet failed ...')
                return False

    def generate_keys(self):
        private_key  = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'), binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii'))

    def sign_transaction(self, sender, recipient,amount):
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        hash_digest = SHA256.new(( str(sender)+ str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(hash_digest)
        return binascii.hexlify(signature).decode('ascii')

    @staticmethod
    def verify_transcation(transcation):
        public_key = RSA.importKey(binascii.unhexlify(transcation.sender))
        verifer = PKCS1_v1_5.new(public_key)
        hash_digest = SHA256.new(( str(transcation.sender)+ str(transcation.recipient) + str(transcation.amount)).encode('utf8'))
        return verifer.verify(hash_digest, binascii.unhexlify(transcation.signature))