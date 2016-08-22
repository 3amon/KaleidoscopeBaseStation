#include <IRremote.h>

IRsend irsend;
unsigned long CrappyProjIrCode = 0x40BFB847;
unsigned long EpsonMuteIrCode = 0xC1AAC936;

void setup() {
  Serial.begin(9600);
}

void loop()
{ 
  byte letter[1];  
  if (Serial.available()) {
    letter[0] = Serial.read();
    // If received on signal, power on projector
    if (letter[0] == 'O') {
      irsend.sendNEC(EpsonMuteIrCode, 32);
    }
    // If received off signal, power off projector and send packet
    // to checkin station to exit Play_Video state
    else if (letter[0] == 'F') {
      irsend.sendNEC(EpsonMuteIrCode, 32);  
      }
    }
    delay(100);
}    
