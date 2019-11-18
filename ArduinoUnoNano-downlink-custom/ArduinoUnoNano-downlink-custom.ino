/*
 * Author: Dennis Ruigrok and JP Meijers
 * Date: 2017-01-16
 *
 * This program is meant to be used with an Arduino UNO or NANO, conencted to an RNxx3 radio module.
 * It will most likely also work on other compatible Arduino or Arduino compatible boards,
 * like The Things Uno, but might need some slight modifications.
 *
 * Transmit a one byte packet via TTN, using confirmed messages,
 * waiting for an acknowledgement or a downlink message.
 *
 * CHECK THE RULES BEFORE USING THIS PROGRAM!
 *
 * CHANGE ADDRESS!
 * Change the device address, network (session) key, and app (session) key to the values
 * that are registered via the TTN dashboard.
 * The appropriate line is "myLora.initABP(XXX);" or "myLora.initOTAA(XXX);"
 * When using ABP, it is advised to enable "relax frame count".
 *
 * Connect the RN2xx3 as follows:
 * RN2xx3 -- Arduino
 * Uart TX -- 10
 * Uart RX -- 11
 * Reset -- 12
 * Vcc -- 3.3V
 * Gnd -- Gnd
 *
 * If you use an Arduino with a free hardware serial port, you can replace
 * the line "rn2xx3 myLora(mySerial);"
 * with     "rn2xx3 myLora(SerialX);"
 * where the parameter is the serial port the RN2xx3 is connected to.
 * Remember that the serial port should be initialised before calling initTTN().
 * For best performance the serial port should be set to 57600 baud, which is impossible with a software serial port.
 * If you use 57600 baud, you can remove the line "myLora.autobaud();".
 *
 */
#include <rn2xx3.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11); // TX, RX

//create an instance of the rn2xx3 library,
//giving the software serial as port to use
rn2xx3 myLora(mySerial);

bool triggered = false;

ISR(ANALOG_COMP_vect)
  {
  triggered = true;
  }

// the setup routine runs once when you press reset:
void setup()
{
  //output LED pin
  pinMode(13, OUTPUT);
  led_on();

  // Open serial communications and wait for port to open:
  Serial.begin(57600); //serial port to computer
  mySerial.begin(9600); //serial port to radio
  Serial.println("Startup");

  initialize_radio();

  //transmit a startup message
  myLora.tx("TTN Mapper on TTN Enschede node");

  led_off();

  setupAcomp();
  
  delay(2000);

  
}

void initialize_radio()
{
  //reset rn2483
  pinMode(12, OUTPUT);
  digitalWrite(12, LOW);
  delay(500);
  digitalWrite(12, HIGH);

  delay(100); //wait for the RN2xx3's startup message
  mySerial.flush();

  //Autobaud the rn2483 module to 9600. The default would otherwise be 57600.
  myLora.autobaud();

  //check communication with radio
  String hweui = myLora.hweui();
  while(hweui.length() != 16)
  {
    Serial.println("Communication with RN2xx3 unsuccesful. Power cycle the board.");
    Serial.println(hweui);
    delay(10000);
    hweui = myLora.hweui();
  }

  //print out the HWEUI so that we can register it via ttnctl
  Serial.println("When using OTAA, register this DevEUI: ");
  Serial.println(myLora.hweui());
  Serial.println("RN2xx3 firmware version:");
  Serial.println(myLora.sysver());



  //configure your keys and join the network
  Serial.println("Trying to join TTN");
  bool join_result = false;

  //ABP: initABP(String addr, String AppSKey, String NwkSKey);
  //join_result = myLora.initABP("02017201", "8D7FFEF938589D95AAD928C2E2E7E48F", "AE17E567AECC8787F749A62F5541D522");

  //OTAA: initOTAA(String AppEUI, String AppKey);
   const char *appEui = "70B3D57ED0025AF4";
  const char *appKey = "97D1E4ECE8E172261187351B747CBE4A";

//  join_result = myLora.initOTAA(appEui, appKey);
//
//  while(!join_result)
//  {
//    Serial.println("Unable to join. Are your keys correct, and do you have TTN coverage?");
//    delay(60000); //delay a minute before retry
//    join_result = myLora.init();
//  }
  Serial.println("Successfully joined TTN");

    Serial.println(myLora.sendRawCommand("radio set sf sf7"));

}

String sensor_value;
// the loop routine runs over and over again forever:
void loop()
{
  
  if(triggered)
  {
    triggered = false;
    Serial.println("Interrupt worked !");
  }
  Serial.println("loop");
//    led_on();
//
//    
//    Serial.print("TXing");
//    //myLora.txCnf/("!"); //one byte, blocking function
//
//    sensor_value = getGasSensorVoltage();
//    Serial.println(sensor_value);
//    switch(myLora.txCnf(sensor_value)) //one byte, blocking function
//    {
//      case TX_FAIL:
//      {
//        Serial.println("TX unsuccessful or not acknowledged");
//        break;
//      }
//      case TX_SUCCESS:
//      {
//        Serial.println("TX successful and acknowledged");
//        Serial.print(myLora.getSNR());
//        Serial.print("\n");
//        break;
//      }
//      case TX_WITH_RX:
//      {
//        String received = myLora.getRx();
//        received = myLora.base16decode(received);
//        Serial.print("Received downlink: " + received);
//        Serial.print(myLora.getSNR());
//        break;
//      }
//      default:
//      {
//        Serial.println("Unknown response from TX function");
//      }
//    }
//
//    led_off();
    delay(1000);
}
//
//void loop() {
//    float sensor_volt;
//    float sensorValue;
//
//    sensorValue = analogRead(A0);
//    sensor_volt = sensorValue/1024*5.0;
//
//    Serial.print("sensor_volt = ");
//    Serial.print(sensor_volt);
//    Serial.println("V");
//    delay(1000);
//}


void led_on()
{
  digitalWrite(13, 1);
}

void led_off()
{
  digitalWrite(13, 0);
}

String getGasSensorVoltage()
{
  float sensor_volt;
  float sensorValue;

  sensorValue = analogRead(A0);
  sensor_volt = sensorValue/1024*5.0;
  return String(sensor_volt);
}

void setupAcomp()
{
  ACSR =
 (0<<ACD) |   // Analog Comparator: Enabled
 (0<<ACBG) |   // Analog Comparator Bandgap Select: AIN0 is applied to the positive input
 (0<<ACO) |   // Analog Comparator Output: Off
 (1<<ACI) |   // Analog Comparator Interrupt Flag: Clear Pending Interrupt
 (1<<ACIE) |   // Analog Comparator Interrupt: Enabled
 (0<<ACIC) |   // Analog Comparator Input Capture: Disabled
 (1<<ACIS1) | (1<ACIS0);   // Analog Comparator Interrupt Mode: Comparator Interrupt on Rising Output Edge
//   ADCSRB = 0;           // (Disable) ACME: Analog Comparator Multiplexer Enable
//  ACSR =  bit (ACI)     // (Clear) Analog Comparator Interrupt Flag
//        | bit (ACIE)    // Analog Comparator Interrupt Enable
//        | bit (ACIS1)  // ACIS1, ACIS0: Analog Comparator Interrupt Mode Select (trigger on falling edge)
//        | bit (ACIS0);  // ACIS1, ACIS0: Analog Comparator Interrupt Mode Select (trigger on falling edge)
}
