#define ACC_PIN 2
#define IGN_PIN 3
#define WD_PIN 8
#define OPT2_PIN 9

void set_pin_state(String hexData);
void get_all_state();
void set_wake_up();

void setup()
{
  Serial.begin(9600);
  pinMode(ACC_PIN, OUTPUT);
  pinMode(IGN_PIN, OUTPUT);
  pinMode(WD_PIN, OUTPUT);
  pinMode(OPT2_PIN, OUTPUT);
}

void loop()
{
  if (Serial.available() > 0)
  {
    String hexData = Serial.readStringUntil('\n');
    hexData.trim();
    if (strcmp(hexData.c_str(), "ALL") == 0)
      get_all_state();
    else if (strcmp(hexData.c_str(), "WAKEUP") == 0)
      set_wake_up();
    else if (strcmp(hexData.c_str(), "STANDBY") == 0)
      set_standby();
    else
      set_pin_state(hexData);
    hexData = "";
  }
}
void set_pin_state(String hexData)
{
  int accState = hexData[0] - '0';
  int ignState = hexData[1] - '0';
  int wdOffState = hexData[2] - '0';
  int opt2State = hexData[3] - '0';
  digitalWrite(ACC_PIN, accState);
  digitalWrite(IGN_PIN, ignState);
  digitalWrite(WD_PIN, wdOffState);
  digitalWrite(OPT2_PIN, opt2State);
  get_all_state();
}
void get_all_state()
{
  int accState = digitalRead(ACC_PIN);
  int ignState = digitalRead(IGN_PIN);
  int wdOffState = digitalRead(WD_PIN);
  int opt2State = digitalRead(OPT2_PIN);
  String response = String(accState) + String(ignState) + String(wdOffState) + String(opt2State);
  Serial.println(response);
}

void set_wake_up()
{
  digitalWrite(ACC_PIN, 0);
  digitalWrite(IGN_PIN, 0);
  get_all_state();
}
void set_standby()
{
  digitalWrite(ACC_PIN, 1);
  digitalWrite(IGN_PIN, 1);
  get_all_state();
}