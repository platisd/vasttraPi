/**
 * Power Control board for the Raspberry Pi using an ATTinyx5 microcontroller.
 * The Power Control board is using a relay to turn on and off the power to a Raspberry Pi.
 * Additionally, they are connected via (software) UART for communication when the RPi is on.
 * The microcontroller connected to a capacitive touch sensor which allows interaction with
 * the external user that wants to turn the Raspberry Pi on and off.
 * 
 * ==== STATES ====
 * The microcontroller has the following states:
 * - Sleep state where the microcontroller is in deep sleep and the power to the RPi is OFF.
 * - Operation state where the microcontroller is triggering the relay to power on the RPi and
 * can communication to it via UART.
 * 
 * ==== CURRENT FUNCTIONALITY ====
 * Upon starting up, the microcontroller goes in deep sleep which can be interrupted by a HIGH
 * signal coming from the capacitive sensor. This initiates a window of operation for the Raspberry Pi
 * during which it will remain on. Every consecutive touch moves the end of this window further in the
 * future, therefore, prolonging the period that the Raspberry Pi is functioning. In other words, on
 * every touch, the operation gets extended for the specified amount of time.
 */

#include <avr/sleep.h>    // Sleep Modes
#include <avr/power.h>    // Power management

const unsigned short touchSensorPin = PB2;
const unsigned short rpiPwrPin = PB3;
const boolean powerOnState = LOW; // The rpiPwrPin state that turns the power on to the RPi

volatile unsigned long timeToSleep = 0;
const unsigned long awakePeriod = 600000; // Time in milliseconds to remain awake on every new touch

/**
 * The change interrupt callback
 */
ISR (PCINT0_vect)
{
  // We register a touch event only when the signal from the touchSensor is rising
  if (digitalRead(touchSensorPin) == HIGH){
    timeToSleep = millis() + awakePeriod;
  }
}

/**
 * Makes the microcontroller go to deep sleep until a change interrupt occurs
 */
void goToSleep() {
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  ADCSRA = 0;            // turn off ADC
  power_all_disable ();  // power off ADC, Timer 0 and 1, serial interface
  sleep_enable();
  sleep_cpu();          // Sleep here and wait for the interrupt
  sleep_disable();
  power_all_enable();    // power everything back on
}

void turnRPiPowerOn(){
  digitalWrite(rpiPwrPin, powerOnState);
}

void turnRPiPowerOff(){
  digitalWrite(rpiPwrPin, !powerOnState);
}

void setup() {
  Serial.begin(9600); // The Universal ATtinyCore library by Spence Konde uses PB0 as TX and PB1 as RX
  pinMode(rpiPwrPin, OUTPUT);
  pinMode(touchSensorPin, INPUT);
  turnRPiPowerOff(); // When starting up, make sure the power to the RPi is off
  // Setup pin change interrupt for D2
  PCMSK  |= bit (PCINT2); // want pin D2 (PB2)
  GIFR   |= bit (PCIF); // clear any outstanding interrupts
  GIMSK  |= bit (PCIE); // enable pin change interrupts
}

void loop() {
  if (millis() >= timeToSleep) { // Check if it is currently time to be asleep
    turnRPiPowerOff(); // Turn off the power to the RPi
    goToSleep(); // Deep sleep until a change interrupt at the specified pin is triggered
  } else { // If we should not be sleeping, then we should be awake and doing stuff
    turnRPiPowerOn(); // Turn on the power to the RPi (if this is already on, it won't make any difference)
  }
}
