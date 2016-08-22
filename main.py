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
from arduinoSerial import ser

# Constants
DEBUG_MODE = 1
BASE_STATION_TASK_TIMEOUT = config['timeout']
BASE_STATION_VIDEO_TIMEOUT = config['timeout_video']

# Initialze the postgresql database driver
engine = create_engine("postgresql://pi:raspberry@127.0.0.1:5432")
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

def get_keyboard_entry(keyboard_obj, prompt, max_len):
    lcd_i2c.lcd_string(prompt, lcd_i2c.LCD_LINE_1)
    key = None
    name = ''
    lcd_i2c.lcd_string(name, lcd_i2c.LCD_LINE_2)
    while key != 'CRLF':
        key = keyboard.keyboard_check_updates(keyboard_obj)
        if(key):
            if key == 'BKSP':
                name = name[:-1]
            elif key in keyboard.nonprintable:
                pass
            else:
                if len(name) < max_len:
                    name += key
            lcd_i2c.lcd_string(name, lcd_i2c.LCD_LINE_2)
        gevent.sleep(0.01)
    return name

def add_or_update_player(player):
    session.add(player.get_db_obj())
    session.commit()

def update_rfid_card(player):
    print("Writing to player RFID")
    print player.get_rfid_data()
    while not puzzle_rfid.write_player_data(player.get_rfid_data()):
        lcd_i2c.lcd_string("Please verify", lcd_i2c.LCD_LINE_1)
        lcd_i2c.lcd_string("your amulet", lcd_i2c.LCD_LINE_2)
        gevent.sleep(0.1)

def lookup_player(rfid_data):
    print("Looking up " + rfid_data["uid"])
    player_db = session.query(PlayerDbObj).filter_by(uid = rfid_data["uid"]).one_or_none()
    if not player_db:
        return None
    else:
        player = Player(db_obj=player_db)
        player.update_user(rfid_data)
        add_or_update_player(player)
        return player

def play_video_for_user(player):
    if config["debug"]:
        print "Playing video : " + video.choose_video(player)["name"]
    else:
        ser.write(b"O")
        video.play_video(video.choose_video(player)["path"])
        ser.write(b"F")

def check_win_condition(player):
    if(player.get_puzzle_count() >= config["puzzle_win_treshold"]):
        print "Removing player from database!"
        player.clear_uid()
        add_or_update_player(player)
        if(player.past_choice_count >= player.present_choice_count):
            lines = [
                ################
                ["Go to ",
                 "Kaleidoscope"],
                ["Coffeeshop ",
                 "when open"],
                ["and ask",
                 "barista:"],
                ["\"Do you feel the",
                 "mirrors today?\""]
            ]
            for line in lines:
                lcd_i2c.lcd_string(line[0], lcd_i2c.LCD_LINE_1)
                lcd_i2c.lcd_string(line[1], lcd_i2c.LCD_LINE_2)
                gevent.sleep(4)
        else:
            lines = [
                ################
                ["Go to 4:30 & B",
                 "and climb tower"]
            ]
            for line in lines:
                lcd_i2c.lcd_string(line[0], lcd_i2c.LCD_LINE_1)
                lcd_i2c.lcd_string(line[1], lcd_i2c.LCD_LINE_2)
                gevent.sleep(8)
            pass;
    else:
        if(player.get_puzzle_count() >= 0):
            lines = [
                ################
                ["Come back when",
                 "you have"],
                ["completed",
                 "more quests."]
            ]
            for line in lines:
                lcd_i2c.lcd_string(line[0], lcd_i2c.LCD_LINE_1)
                lcd_i2c.lcd_string(line[1], lcd_i2c.LCD_LINE_2)
                gevent.sleep(4)
            pass;

def play_video_for_new_user():
    if config["debug"]:
        print "Playing video : " + video.choose_video(None)["name"]
    else:
        ser.write(b"O")
        video.play_video(video.choose_video(None)["path"])
        ser.write(b"F")

def get_initial_choice(keyboard_obj):
    lines = [
        ################
        ["Read passage",
         "and answer"],
        ["wisely, as your",
         "choices may"],
        ["change your",
         "destiny."]
    ]
    for line in lines:
        lcd_i2c.lcd_string(line[0], lcd_i2c.LCD_LINE_1)
        lcd_i2c.lcd_string(line[1], lcd_i2c.LCD_LINE_2)
        gevent.sleep(4)
    pass;
    
    while(True):
        lines = [
            ################
            ["Do you burn",
             "the receipt?"],
            ["1. Burn receipt",
             "2. Keep receipt"]
        ]

        for line in lines:
            lcd_i2c.lcd_string(line[0], lcd_i2c.LCD_LINE_1)
            lcd_i2c.lcd_string(line[1], lcd_i2c.LCD_LINE_2)
            gevent.sleep(4)
        pass;
        gevent.sleep(3)
        choice = get_keyboard_entry(keyboard_obj, "Enter choice:", 1)

        if(choice == '1'):
            return False #present choice
        elif(choice == '2'):
            return True #past choice

def play(keyboard_obj):

    rfid_data = gevent.spawn(wait_for_rfid).get()
    player = gevent.with_timeout(BASE_STATION_TASK_TIMEOUT, lookup_player, rfid_data)

    if(player):
        gevent.with_timeout(BASE_STATION_VIDEO_TIMEOUT, play_video_for_user, player)
        lcd_i2c.display_on()
        gevent.with_timeout(BASE_STATION_TASK_TIMEOUT, check_win_condition, player)
    else:
        gevent.with_timeout(BASE_STATION_VIDEO_TIMEOUT, play_video_for_new_user)
        lcd_i2c.display_on()
        name = gevent.with_timeout(BASE_STATION_TASK_TIMEOUT, get_keyboard_entry, keyboard_obj, "Enter your name:", 15)
        initial_choice_past = gevent.with_timeout(BASE_STATION_VIDEO_TIMEOUT, get_initial_choice, keyboard_obj)
        player = Player(name=name, uid=rfid_data["uid"], initial_choice_past=initial_choice_past)
        gevent.with_timeout(BASE_STATION_TASK_TIMEOUT, update_rfid_card, player)
        gevent.with_timeout(BASE_STATION_TASK_TIMEOUT, add_or_update_player, player)
        lcd_i2c.lcd_string("Refer to map to", lcd_i2c.LCD_LINE_1)
        lcd_i2c.lcd_string("continue journey", lcd_i2c.LCD_LINE_2)
        gevent.sleep(5)


    lcd_i2c.display_off()

if __name__ == "__main__":
    lcd_i2c.lcd_init()
    lcd_i2c.display_off()
    keyboard_obj = keyboard.grab_keyboard()
    while True:
        try:
            play(keyboard_obj)
        except gevent.Timeout:
            print('Could not complete in timeout!')
            exit(1)
