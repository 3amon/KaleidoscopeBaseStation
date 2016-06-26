import json
from sqlalchemy import Column, Integer, Text, String
from base import Base
from config import config

class PlayerDbObj(Base):
    __tablename__ = 'players'

    uid = Column(Integer, primary_key=True)
    name = Column(String)
    puzzles = Column(Text)

class Player:
    def __init__(self, name = None, uid = None, db_obj = None):
        if db_obj:
            self.name = db_obj.name
            self.uid = db_obj.uid
            self.puzzles = json.loads(db_obj.puzzles)
        else:
            self.name = name
            self.uid = uid
            self.puzzles = {}
            for player in config['puzzles']:
                complete = 0
                tries = 0
                if config["debug"]:
                    import random
                    # if we are debugging we want to set these values to something else
                    complete = 1 if random.random() > 0.5 else 0
                    tries = random.randint(0, 20) + complete
                self.puzzles[player] = [complete, tries]

    def get_db_obj(self, db_obj = None):
        result = db_obj
        if not result:
            result = PlayerDbObj()
        result.name = self.name
        result.uid = self.uid
        result.puzzles = json.dumps(self.puzzles)
        return result

    def get_puzzle_count(self):
        count = 0
        for name, [complete, tries] in self.puzzles.iteritems():
            if tries > 0:
                count += 1
        return count

    # Note: We do not update name
    def update_user(self, rfid_data):
        data_block = config['rfid']['data_block']
        data_tries_byte = config['rfid']['puzzle_data_tries_byte']
        data_complete_byte = config['rfid']['puzzle_data_complete_byte']
        puzzle_data_puzzle_size = config['rfid']['puzzle_data_size']

        puzzle_byte_array = rfid_data[data_block]

        self.puzzles = {}
        for name in config['puzzles']:
            puzzle_id = config['puzzles'][name]["id"]
            complete = puzzle_byte_array[puzzle_id * puzzle_data_puzzle_size + data_complete_byte]
            tries = puzzle_byte_array[puzzle_id * puzzle_data_puzzle_size + data_tries_byte]
            self.puzzles[name] = [complete, tries]

    def get_rfid_data(self):

        name_block = config['rfid']['name_block']
        data_block = config['rfid']['data_block']
        data_tries_byte = config['rfid']['puzzle_data_tries_byte']
        data_complete_byte = config['rfid']['puzzle_data_complete_byte']
        puzzle_data_puzzle_size = config['rfid']['puzzle_data_size']
        total_puzzle_size = puzzle_data_puzzle_size * len(config['puzzles'])

        name_byte_array = [0] * 16
        for i in range(min(16, len(self.name))):
            name_byte_array[i] = self.name[i]

        puzzle_byte_array = [0] * 16
        for name, [complete, tries] in self.puzzles.iteritems():
            puzzle_id = config['puzzles'][name]["id"]
            # Note: The offset math is going to be a bit more complicated if we ever build enough puzzles that we
            # need to read from additional blocks.
            # Way says that every 4 blocks are reserved (3,7,11,etc). Plus, we would need to read
            # from block N+1 every 16 bytes too. So we would need an outer loop that skips all
            # i % 4 = 3 blocks starting block 7.
            puzzle_byte_array[puzzle_id * puzzle_data_puzzle_size + data_complete_byte] = complete
            puzzle_byte_array[puzzle_id * puzzle_data_puzzle_size + data_tries_byte] = tries

        rfid_data = {}
        rfid_data['uid'] = self.uid
        rfid_data[name_block] = name_byte_array
        rfid_data[data_block] = puzzle_byte_array
        return rfid_data


