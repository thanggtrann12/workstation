#define ACC_PIN 2
#define IGN_PIN 3
#define WD_OFF_PIN 8
#define OPT2_PIN 9

#define E_OK 0
#define E_NOT_OK 1

void printPinState()
{
  int accState = digitalRead(ACC_PIN);
  int ignState = digitalRead(IGN_PIN);
  int wdOffState = digitalRead(WD_OFF_PIN);
  int opt2State = digitalRead(OPT2_PIN);
  Serial.print("[" + String(accState) + "]");
  Serial.print("[" + String(ignState) + "]");
  Serial.print("[" + String(wdOffState) + "]");
  Serial.println("[" + String(opt2State) + "]");
}
void processCmd(uint8_t pin, uint8_t state)
{
  if (pin == 0 && state == 0)
  {
    printPinState();
  }
  else
  {
    digitalWrite(pin, state);
    if (digitalRead(pin) == state)
    {
      Serial.println(E_OK);
    }
    else
    {
      Serial.println(E_NOT_OK);
    }
    Serial.flush();
  }
}
void setup()
{
  Serial.begin(9600);
  pinMode(ACC_PIN, OUTPUT);
  pinMode(IGN_PIN, OUTPUT);
  pinMode(WD_OFF_PIN, OUTPUT);
  pinMode(OPT2_PIN, OUTPUT);
}

void loop()
{
  if (Serial.available() > 0)
  {
    String receivedData = Serial.readStringUntil('\n');

    if (receivedData.length() > 0)
    {
      int receivedValue = receivedData.toInt();
      int _pin = receivedValue / 10;
      int _state = receivedValue % 10;
      processCmd(_pin, _state);
    }
  }
}
