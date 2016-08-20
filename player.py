import json
from sqlalchemy import Column, Integer, Text, String
from base import Base
from config import config
import uuid

class PlayerDbObj(Base):
    __tablename__ = 'players'
    uid = Column(String, primary_key=True)
    name = Column(String)
    puzzles = Column(Text)
    id = Column(String)
    present_choice_count = Column(Integer)
    past_choice_count = Column(Integer)

class Player:
    def __init__(self, name = None, uid = None, initial_choice_past = None, db_obj = None):
        if db_obj:
            self.db_obj = db_obj
            self.name = db_obj.name
            self.uid = db_obj.uid
            self.puzzles = json.loads(db_obj.puzzles)
            self.id = db_obj.id
            self.present_choice_count = db_obj.present_choice_count
            self.past_choice_count = db_obj.past_choice_count
        else:
            self.db_obj = PlayerDbObj()
            self.name = name
            self.uid = uid
            self.id = uuid.uuid4()
            self.puzzles = {}
            self.present_choice_count = 0
            self.past_choice_count = 0
            if(initial_choice_past):
                self.past_choice_count = 1
            else:
                self.present_choice_count = 1
            for player in config['puzzles']:
                complete = 0
                tries = 0
                if config["debug"]:
                    import random
                    # if we are debugging we want to set these values to something else
                    complete = 1 if random.random() > 0.5 else 0
                    tries = random.randint(0, 20) + complete
                self.puzzles[player] = [complete, tries]

    def clear_uid(self):
        self.uid = uuid.uuid4()

    def get_db_obj(self):
        result = self.db_obj
        result.name = self.name
        result.uid = self.uid
        result.puzzles = json.dumps(self.puzzles)
        result.id = self.id
        result.present_choice_count = self.present_choice_count
        result.past_choice_count = self.past_choice_count
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
        past_choice_count_byte = config['rfid']['past_choice_count_byte']
        present_choice_count_byte = config['rfid']['present_choice_count_byte']

        self.past_choice_count = rfid_data[data_block][past_choice_count_byte]
        self.present_choice_count = rfid_data[data_block][present_choice_count_byte]
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
        past_choice_count_byte = config['rfid']['past_choice_count_byte']
        present_choice_count_byte = config['rfid']['present_choice_count_byte']

        name_byte_array = [0] * 16
        for i in range(min(16, len(self.name))):
            name_byte_array[i] = ord(self.name[i])

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
        rfid_data[data_block][past_choice_count_byte] = self.past_choice_count
        rfid_data[data_block][present_choice_count_byte] = self.present_choice_count
        return rfid_data


