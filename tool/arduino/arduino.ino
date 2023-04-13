#define ACC_PIN 2
#define IGN_PIN 3
#define PWR_ON 4
#define WD_OFF_PIN 8
#define OPT2_PIN 9
#define NOT_BIND_1 10
#define NOT_BIND_2 11
#define E_OK 1
#define E_NOT_OK 2

void processCommand(uint8_t pin, uint8_t state)
{
  digitalWrite(pin, state);
  if (state == LOW)
    Serial.println(E_OK);
  else
   Serial.println(E_NOT_OK);
   Serial.flush();
}

void setup()
{
    Serial.begin(9600);
    pinMode(ACC_PIN, OUTPUT);
    pinMode(IGN_PIN, OUTPUT);
    pinMode(WD_OFF_PIN, OUTPUT);
    pinMode(OPT2_PIN, OUTPUT);
    digitalWrite(ACC_PIN, LOW);
    digitalWrite(IGN_PIN, LOW);
    for (size_t i = 4; i < 12; i++)
    {
        digitalWrite(i, HIGH);
    }
}

void loop()
{
    if (Serial.available() > 0)
    {
        String receivedData = Serial.readStringUntil('\n');
        int receivedValue = receivedData.toInt();
        switch (receivedValue)
        {
        case 10:
            processCommand(ACC_PIN, LOW);
            break;
        case 11:
            processCommand(ACC_PIN, HIGH);
            break;
        case 20:
            processCommand(IGN_PIN, LOW);
            break;
        case 21:  
            processCommand(IGN_PIN, HIGH);
            break;
        case 30:
            processCommand(OPT2_PIN, LOW);
            break;
        case 31:
            processCommand(OPT2_PIN, HIGH);
            break;
        case 40:
            processCommand(WD_OFF_PIN, LOW);
            break;
        case 41:
            processCommand(WD_OFF_PIN, HIGH);
            break;
        default:
            break;
        }
    }
}
