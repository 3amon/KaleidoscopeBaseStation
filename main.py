import gevent
from player import Player, PlayerDbObj
from base import Base
import video
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import lcd_i2c
import puzzle_rfid
from config import config
import keyboard
import os

# Constants
DEBUG_MODE = 1
BASE_STATION_TASK_TIMEOUT = config['timeout']
BASE_STATION_VIDEO_TIMEOUT = config['timeout_video']

# Initialze the postgresql database driver
engine = create_engine(os.environ['KAL_DB_PATH'])
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def wait_for_rfid():
    rfid_data = None
    print("Waiting for RFID")
    while not rfid_data:
        rfid_data = puzzle_rfid.read_player_data()
        gevent.sleep(0.5)

    return rfid_data

def create_user(uid):
    lcd_i2c.display_on()
    lcd_i2c.lcd_string("Enter name:", lcd_i2c.LCD_LINE_1)
    key = None
    name = ''
    while(not keyboard.key_event_queue.empty()):
        keyboard.key_event_queue.get()
    while key != 'CRLF':
        key = keyboard.key_event_queue.get()
        if key == 'BKSP':
            name = name[:-1]
        elif key in keyboard.nonprintable:
            pass
        else:
            if len(name) < 16:
                name += key
        lcd_i2c.lcd_string(name, lcd_i2c.LCD_LINE_2)
    lcd_i2c.display_off()
    return Player(name = name, uid = uid)

def add_or_update_player(player, db_obj = None):
    if not db_obj:
        print("Adding " + player.name + " to the database!")
    else:
        print("Updating: " + player.name + " in the database!")
    session.add(player.get_db_obj(db_obj))
    session.commit()

def update_rfid_card(player):
    print("Writing to player RFID")
    print player.get_rfid_data()
    while not puzzle_rfid.write_player_data(player.get_rfid_data()):
        gevent.sleep(0)

def lookup_or_add_user(rfid_data):
    print rfid_data
    print("Looking up " + rfid_data["uid"])
    player_db = session.query(PlayerDbObj).filter_by(uid = rfid_data["uid"]).one_or_none()
    if not player_db:
        print("Creating user " + str(rfid_data["uid"]))
        player = create_user(rfid_data["uid"])
        update_rfid_card(player)
        add_or_update_player(player)
        return player
    else:
        player = Player(db_obj=player_db)
        player.update_user(rfid_data)
        add_or_update_player(player, player_db)
        return player

def play_video_for_user(player):
    if config["debug"]:
        print "Playing video : " + video.choose_video(player)["name"]
    else:
        video.play_video(video.choose_video(player)["path"])


def play():
    rfid_data = gevent.spawn(wait_for_rfid).get()
    user = gevent.with_timeout(BASE_STATION_TASK_TIMEOUT, lookup_or_add_user, rfid_data)
    gevent.with_timeout(BASE_STATION_VIDEO_TIMEOUT, play_video_for_user, user)


if __name__ == "__main__":
    lcd_i2c.lcd_init()
    lcd_i2c.display_off()
    while True:
        try:
            play()
        except gevent.Timeout:
            print('Could not complete in timeout!')
            exit(1)
