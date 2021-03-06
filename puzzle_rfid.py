import struct
import MFRC522
from config import config

MIFAREReader = MFRC522.MFRC522()

def write_player_data(rfid_data):
    # Scan for cards
    (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status != MIFAREReader.MI_OK:
        return None

    # Get the UID of the card
    (status, uid) = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status != MIFAREReader.MI_OK:
        return None

    # This is the default key for authentication
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

    # Select the scanned tag
    MIFAREReader.MFRC522_SelectTag(uid)

    name_block = int(config['rfid']['name_block'])
    data_block = int(config['rfid']['data_block'])

    # Authenticate
    status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 4, key, uid)

    # Check if authenticated
    if status != MIFAREReader.MI_OK:
        return None

    if(not MIFAREReader.MFRC522_Write(name_block, rfid_data[name_block])):
        return None

    # Authenticate
    status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, name_block, key, uid)

    # Check if authenticated
    if status != MIFAREReader.MI_OK:
        return None

    if(not MIFAREReader.MFRC522_Write(data_block, rfid_data[data_block])):
        return None

    MIFAREReader.MFRC522_StopCrypto1()

    return True

def read_player_data():
    # Scan for cards
    (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status != MIFAREReader.MI_OK:
        return None

    # Get the UID of the card
    (status, uid) = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status != MIFAREReader.MI_OK:
        return None

    # This is the default key for authentication
    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

    # Select the scanned tag
    MIFAREReader.MFRC522_SelectTag(uid)

    data_block = config['rfid']['data_block']

    # Authenticate
    status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, data_block, key, uid)

    # Check if authenticated
    if status != MIFAREReader.MI_OK:
        return None

    block_size = 16

    puzzle_byte_array = [0] * block_size

    # Reading a single block for puzzle data
    # If we need to do more here, we will
    data = MIFAREReader.MFRC522_Read(data_block)
    if not data:
        return None

    MIFAREReader.MFRC522_StopCrypto1()

    for i in range(min(len(puzzle_byte_array), len(data))):
        puzzle_byte_array[i] = data[i]

    rfid_data = {}
    # Note: We are not going to read the name back from the RFID card here
    rfid_data[data_block] = puzzle_byte_array
    uid_byte_str = "".join(map(chr, uid))
    rfid_data["uid"] = str(struct.unpack('<I', uid_byte_str[:4])[0])
    return rfid_data
