from time import time
from utility.printable import Printable


class Block(Printable):
    def __init__(self, index, previous_hash,transcations, proof, time = time()):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = time
        self.transcations = transcations
        self.proof = proof

   
