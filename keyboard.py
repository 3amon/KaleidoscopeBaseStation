import evdev
from config import config
import string
from subprocess import call

# we are going to just list every key we care about
scancodes = {
    # Scancode: ASCIICode
    0: None,      2: '1',     3:  '2',     4: '3', 5:  '4', 6:  '5', 7:  '6', 8: '7', 9: '8',
    10: '9',     11: '0',     14: 'BKSP', 16: 'Q', 17: 'W', 18: 'E', 19: 'R',
    20: 'T',     21: 'Y',     22: 'U',    23: 'I', 24: 'O', 25: 'P',
    30: 'A',     31: 'S',     32: 'D',    33: 'F', 34: 'G', 35: 'H', 36: 'J', 37: 'K', 38: 'L',
    42: 'LSHFT', 44: 'Z',     45: 'X',    46: 'C', 47: 'V', 48: 'B', 49: 'N',
    50: 'M',     54: 'RSHFT', 28: 'CRLF'}

nonprintable = [
    'LSHFT',
    'RSHFT',
    'CRLF',
    'BKSP',
    'INVALID'
]

def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])

def mapFirstElement(list_of_tuples):
    return map(lambda tuple: tuple[0], list_of_tuples)

# This is going to get the first InputDevice that has keys we care about
def get_keyboard():
    devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
    for device in devices:
        cap_list_unflat = device.capabilities()
        cap_list = flatten(cap_list_unflat.values())
        mylist = flatten(cap_list)
        if set(scancodes).issubset(set(mylist)):
            return device

    return None

def get_cap_state(keyboard):
    result = False
    if 'KEY_LEFTSHIFT' in mapFirstElement(keyboard.active_keys(verbose = True)) or \
       'KEY_RIGHTSHIFT' in mapFirstElement(keyboard.active_keys(verbose=True)):
        result = not result

    if 'LED_CAPSL' in mapFirstElement(keyboard.leds(verbose=True)):
        result = not result

    return result

def keyboard_check_updates(keyboard_obj):
    event = keyboard_obj.read_one()
    if event and event.type == evdev.ecodes.EV_KEY:
        key = evdev.KeyEvent(event)
        if key.keystate == evdev.KeyEvent.key_down:

            key_lookup = scancodes.get(key.scancode) or 'INVALID'
            if key_lookup in string.ascii_uppercase and not get_cap_state(keyboard_obj):
                key_lookup = key_lookup.lower()

            return key_lookup
    return None

def grab_keyboard():

    keyboard_obj = get_keyboard()
    call(["sudo", "killall", "dbus-daemon"])
    if not config["debug"]:
        keyboard_obj.grab()

    return keyboard_obj
