//Relay 1 we want to have on whenever something else is on. This is because the air sampler solenoid it will be connected to will be
//unlike the other solenoids, in a normally closed configuration so that when power is supplied (when we turn its relay on here) the valve will be
//shut and when power is not supplied the air sampler valve will be open. This is done so that the pump always is able to draw air from somewhere.

//Setting the relay and button pins:
int LED0 = 53;

unsigned long start_delay_min = 60;  //Write how long you want the start time delay to be minutes
unsigned long relay_delay_min = 42;  //Write how long you want the delay between relays (after the start time delay) to be minutes 1 or 15

//unsigned long dt = (60000 * relay_delay_min);
//unsigned long start = (60000 * start_delay_min);

unsigned long dt = (1000);
unsigned long start = (1000);

void setup() {
  Serial.begin(9600);  // open the serial port at 9600 bps: NEW
  Serial.println(dt);
  Serial.println(start);
  pinMode(LED0, OUTPUT);

  delay(start);
  digitalWrite(LED0, HIGH);

  delay(dt);
  digitalWrite(LED0, LOW);
}

void loop() {  //took the previous for loop and delay out of the void loop so that it would only run once per power cycle
}
