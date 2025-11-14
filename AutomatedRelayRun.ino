//Relay 1 we want to have on whenever something else is on. This is because the air sampler solenoid it will be connected to will be
//unlike the other solenoids, in a normally closed configuration so that when power is supplied (when we turn its relay on here) the valve will be
//shut and when power is not supplied the air sampler valve will be open. This is done so that the pump always is able to draw air from somewhere.

//Setting the relay and button pins:
int RELAY0 = 41;
int RELAY1 = 40;
int RELAY2 = 39;
int RELAY3 = 38;
int RELAY4 = 37;
int RELAY5 = 36;
int RELAY6 = 35;
int RELAY7 = 34;
int RELAY8 = 33;
int RELAY9 = 32;
int RELAY10 = 31;
int RELAY11 = 30;
int RELAY12 = 29;
int RELAY13 = 28;
int RELAY14 = 27;
int RELAY15 = 26;
int RELAYS[] = { RELAY0, RELAY1, RELAY2, RELAY3, RELAY4, RELAY5, RELAY6, RELAY7, RELAY8, RELAY9, RELAY10, RELAY11, RELAY12, RELAY13, RELAY14, RELAY15 };  //shove them into an array to call on later.

unsigned long start_delay_min = 60;  //Write how long you want the start time delay to be minutes
unsigned long relay_delay_min = 42;  //Write how long you want the delay between relays (after the start time delay) to be minutes 1 or 15

unsigned long dt = (60000 * relay_delay_min);
unsigned long start = (60000 * start_delay_min);

//unsigned long dt = (1000);
//unsigned long start = (1000);

void setup() {
  Serial.begin(9600);  // open the serial port at 9600 bps: NEW
  Serial.println(dt);
  Serial.println(start);
  pinMode(RELAYS[0], OUTPUT);
  digitalWrite(RELAYS[0], HIGH);
  for (int i = 1; i <= 16; i++) {  //set the relays to 'high' so that they will be 'off' initially
    pinMode(RELAYS[i], OUTPUT);
    digitalWrite(RELAYS[i], HIGH);
  }
  delay(start);
  for (byte i = 1; i <= 15; i = i + 1) {  //sequentially turns each relay 'on' for the specified delay time, while keeping the first relay 'on' always.
    digitalWrite(RELAYS[i], LOW);
    digitalWrite(RELAYS[0], LOW);
    Serial.println("Valve open:");
    Serial.println(i);
    delay(dt);
    digitalWrite(RELAYS[i], HIGH);  //shuts off whatever relay is open per the loop
                                    //shuts 'off' the first relay so that is off when the loop ends. Serial.println("Valves closed.");
  }
  digitalWrite(RELAYS[0], HIGH);
}

void loop() {  //took the previous for loop and delay out of the void loop so that it would only run once per power cycle
}