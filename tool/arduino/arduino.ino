#define ACC_PIN 2
#define IGN_PIN 3
#define PWR_ON 4
#define WD_OFF_PIN 8
#define OPT2_PIN 9
#define NOT_BIND_1 10
#define NOT_BIND_2 11

void processCommand(int command, uint8_t pin)
{
    if (command % 2 == 0)
    {
        digitalWrite(pin, HIGH);
        if (digitalRead(pin) == HIGH)
        {
            Serial.println(String(command) + " executed");
        }
        else
        {
            Serial.println(String(command) + " unexecuted");
        }
    }
    else
    {
        digitalWrite(pin, LOW);
        if (digitalRead(pin) == LOW)
        {
            Serial.println(String(command) + " executed");
        }
        else
        {
            Serial.println(String(command) + " unexecuted");
        }
    }
}

void setup()
{
    Serial.begin(9600);
    pinMode(ACC_PIN, OUTPUT);
    pinMode(IGN_PIN, OUTPUT);
    pinMode(WD_OFF_PIN, OUTPUT);
    pinMode(OPT2_PIN, OUTPUT);
    for (size_t i = 2; i < 12; i++)
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
        case 1:
            processCommand(receivedValue, ACC_PIN);
            break;
        case 2:
            processCommand(receivedValue, ACC_PIN);
            break;
        case 3:
            processCommand(receivedValue, IGN_PIN);
            break;
        case 4:
            processCommand(receivedValue, IGN_PIN);
            break;
        case 5:
            processCommand(receivedValue, OPT2_PIN);
            break;
        case 6:
            processCommand(receivedValue, OPT2_PIN);
            break;
        case 7:
            processCommand(receivedValue, WD_OFF_PIN);
            break;
        case 8:
            processCommand(receivedValue, WD_OFF_PIN);
            break;
        default:
            Serial.println("Invalid command received");
            break;
        }
    }
}
