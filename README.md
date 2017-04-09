# VasttraPi
Your personal departures screen for Västtrafik buses. Currently it is hardcoded to look for
buses going from Lindholmen to the center, but can be easily modified or extended.

## How to install
First, prepare your Raspberry Pi for connecting with your local wireless network and enable SSH. The following guide has been tested on **2017-03-02-raspbian-jessie**.

* Set the correct timezone to your Pi
  * `sudo raspi-config`
  * Localisation Options
  * Change timezone
  * Europe
  * Stockholm
* Clone the vasttraPi repository
  * `git clone https://github.com/platisd/vasttraPi.git`
* Clone the PyTrafik repository
  * `git clone https://github.com/axelniklasson/PyTrafik.git`
* Install the PyTrafik Python3 module
  * `sudo pip3 install PyTrafik/`
* Create an api-config file with your API tokens
  * `nano vasttraPi/api-config`
  * Add your API tokens. The first line should be the (public) key and the second is the secret.
![api config screenshot](http://i.imgur.com/ghl3XRM.png)
* Make the Python3 GUI start right after boot
  * `nano /home/pi/.xsession`
  * Add: `python3 /home/pi/vasttraPi/departures.py`
* Sync, reboot and the departures screen should pop up
  * `sync`
  * `sudo reboot`
