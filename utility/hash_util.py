import hashlib as hl
import json


 
def hash_string_256(string):
    return hl.sha256(string).hexdigest()

def hash_block(block):

   # return '-'.join([str(bloc k[key]) for key in block]) # join function is to add a variable to your argument 
    hashable_block  = block.__dict__.copy()
    hashable_block['transcations'] = [tx.to_ordered_dict() for tx in hashable_block['transcations']]
    return hash_string_256(json.dumps(hashable_block, sort_keys=True).encode())  # json to convert a dictionary 