### Required Hardware
KlipperScreen should run on any HDMI touchscreen that you can connect to a computer. The required video driver may
be slightly different depending on what model you get. I am developing on a 1024x600 resolution screen. Due to this,
other resolutions may not be scaled properly at this moment. UI scaling is a future development item.

Will also work with a PiTFT 3.5 (http://www.lcdwiki.com/3.5inch_RPi_Display). This is a smaller, much cheaper display that can be installed directly on the RPi using the GPIO pins. No additional cables required. 

#### Configure Hardware

Add the following to _/boot/config.txt_. You can alter the hdmi_cvt to your screen specifications. This example is setup
for a resolution of 1024x600 and a refresh rate of 60hz.
```
hdmi_cvt=1024 600 60 6 0 0 0
hdmi_group=2
hdmi_mode=87
hdmi_drive=2
```
* Development has been using 1024x600 for a screen resolution. Other resolutions may have issues currently

After changing _/boot/config.txt_ you must reboot your raspberry pi. Please also ensure you followed setting up your screen via the screen instructions. This will likely have a xorg.conf.d file for input from the touchscreen that you need to create.

For the 3.5inch RPi Display, you will need to install the driver instead (from http://www.lcdwiki.com/3.5inch_RPi_Display#Driver_Installation)

```
sudo rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
sudo ./LCD35-show
```
Once the pi reboots, the screen should be working. 

### Installation

This install process is meant for Raspbian non-desktop version. If you have installed it on the GUI version, use
`sudo raspi-config` to set boot to console by choosing the following options in order:
* 1 System Options
* S5 Boot / Auto Login
* B1 Console

Follow the instructions to install klipper and moonraker.
klipper: https://github.com/KevinOConnor/klipper/
moonraker: https://github.com/Arksine/moonraker

Ensure that 127.0.0.1 is a trusted client for moonraker, such as in this example:
```
[authorization]
trusted_clients:
  127.0.0.1
```

For moonraker, ensure that 127.0.0.1 is a trusted client:

clone the KlipperScreen git:

```
git clone https://github.com/jordanruthe/KlipperScreen.git
```

Run _scripts/KlipperScreen-install.sh_
This script will install packages that are listed under manual install, create a
python virtual environment at ${HOME}/.KlipperScreen-env and install a systemd
service file.

As an option to do development or interact with KlipperScreen from your computer, you may install tigervnc-scraping-server and VNC to your pi instance. Follow tigervnc server setup procedures for details on how to do that.

If you need a custom location for the configuration file, you can add -c or --configfile to the systemd file and specify
the location of your configuration file.

#### Touchscreen Calibration
Most people don't need to calibrate, but if you do need to calibrate your touchscreen, follow this process:

```
DISPLAY=:0 xinput_calibrator --list
Device "wch.cn USB2IIC_CTP_CONTROL" id=6
DISPLAY=:0 xinput_calibrator -v --device <id from last command>
```
