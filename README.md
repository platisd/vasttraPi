# VasttraPi
Your personal departures screen for Västtrafik buses. Currently it is hardcoded to look for buses going from Lindholmen to the center, but can be easily modified or extended. It uses a Python wrapper ([PyTrafik](https://github.com/axelniklasson/PyTrafik)), around the Västtrafik API by Axel Niklasson.

## How to install
First, prepare your Raspberry Pi for connecting with your local wireless network and enable SSH. The following guide has been tested on **2017-03-02-raspbian-jessie** running on a **Raspberry Pi Zero W**.

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
* Make sure you have PySerial 3.3 or greater installed
  * sudo pip3 install pyserial --upgrade
* Create an api-config file with your [Västtrafik API tokens](https://developer.vasttrafik.se/portal/#/applications)
  * `nano vasttraPi/api-config`
  * Add your API tokens. The first line should be the (public) key and the second is the secret.
![api config screenshot](http://i.imgur.com/ghl3XRM.png)
* Make the Python3 GUI start right after boot
  * `nano /home/pi/.xsession`
  * Add: `python3 /home/pi/vasttraPi/departures.py`
  * To undo this, do not just empty the .xsession file, remove it completely.
* Sync, reboot and the departures screen should pop up
  * `sync`
  * `sudo reboot`

### Read-only & OverlayFS (Optional)
The Python3 script, which is configured to run on startup, is listening to the serial port for an "off" string in order to shutdown the Raspberry Pi. This is done in order to protect the SD card from being corrupted, even though this has rarely happened to me. That being said, if you do not want to bother with the extra USB-serial connection or feel like trying something new, an effective way of protecting the SD card is by using a read-only filesystem and OverlayFS. After a lot of search I found the great [instructions](http://wiki.psuter.ch/doku.php?id=solve_raspbian_sd_card_corruption_issues_with_read-only_mounted_root_partition) by Pascal Suter who provided a very useful [script](overlayRoot.sh) in order to achieve that.

* Copy the `overlayRoot.sh` script to `/sbin/`
  * `sudo cp /home/pi/vasttraPi/overlayRoot.sh /sbin/`
* Disable swap
  * `sudo dphys-swapfile swapoff`
  * `sudo dphys-swapfile uninstall`
  * `sudo update-rc.d dphys-swapfile remove`
* Once you have your partitions set up the way you want them edit the `/boot/cmdline.txt` to run the `overlayRoot.sh` script.
  * `nano /boot/cmdline.txt`
  * Append `init=/sbin/overlayRoot.sh` to the end of the existing file.
* After rebooting, any changes to the partitions will be non-persistent. If you want to undo this, simply restore the `/boot/cmdline.txt` to its original state.
