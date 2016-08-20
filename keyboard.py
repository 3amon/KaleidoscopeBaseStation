import evdev
import gevent
from config import config
from gevent.queue import Queue
import string

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
    'RSHIFT',
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

key_event_queue = Queue()

def get_cap_state(keyboard):
    result = False
    if 'KEY_LEFTSHIFT' in mapFirstElement(keyboard.active_keys(verbose = True)) or \
       'KEY_RIGHTSHIFT' in mapFirstElement(keyboard.active_keys(verbose=True)):
        result = not result

    if 'LED_CAPSL' in mapFirstElement(keyboard.leds(verbose=True)):
        result = not result

    return result


def watch_keyboard():
    keyboard = get_keyboard()
    if not config["debug"]:
        try:
            keyboard.grab()
        except IOError:
            keyboard.ungrab()
            keyboard.grab()
    while True:
        event = keyboard.read_one()
        if event and event.type == evdev.ecodes.EV_KEY:
            key = evdev.KeyEvent(event)
            if key.keystate == evdev.KeyEvent.key_down:

                key_lookup = scancodes.get(key.scancode) or 'INVALID'

                if key_lookup in string.ascii_uppercase and not get_cap_state(keyboard):
                    key_lookup = key_lookup.lower()

                key_event_queue.put_nowait(key_lookup)
        gevent.sleep(0.1)

# start watching the keyboard
gevent.spawn(watch_keyboard)