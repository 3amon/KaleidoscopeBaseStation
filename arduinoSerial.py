import serial
import time
import gevent

projectorOffDuration = 5

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=200)
ser.flushInput()

if __name__ == "__main__":
    while True:
        try:
            ser.write(b"F")
            time.sleep(projectorOffDuration)
        except gevent.Timeout:
            print('Could not complete in timeout!')
            exit(1)
