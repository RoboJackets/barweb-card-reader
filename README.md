# Apiary NFC Reader

Script for piping GTID from BuzzCards to Apiary through a web socket or keyboard emulation.

## Package requirements

* libusb
* libpcsclite
* libnfc
* pcscd

On Ubuntu, the packages can be installed using the following command;

```
sudo apt-get install libusb-dev libpcsclite-dev libnfc-dev pcscd swig
```

```
pip install -r requirements.txt
```

### Kernel Module Conflicts

If you're running this on Ubuntu, you'll likely get a "No readers connected" error when running the script. That's because one of the default kernel modules conflicts with the Python smart card libraries. You can disable the conflicting module by making this change:

`sudo echo "blacklist pn533_usb" >> /etc/modprobe.d/blacklist-libnfc.conf`

## Running the script

The script supports running either as a WebSocket server or a keyboard emulator.
The mode is determined with a parameter (`-s` for WebSocket, `-k` for keyboard).

### Running from secondary terminal on Linux

If you're launching the script from a secondary terminal (anything that isn't inside the active X session), you'll likely get an error running the script (`Xlib.error.DisplayNameError: Bad display name ""`). This is because there's no display associated with your terminal. You can force the script to run against the primary display by manually specifying the display like so: `DISPLAY=":0" python card_reader_server.py -k`. 

### Keyboard Mode:
```
python card_reader_server.py -k
```

On **macOS**, one of the following must be true:

- The process must run as root.
- The application must be white listed in _System Preferences_ -> _Security_ -> _Privacy_ -> _Accessibility_. 
Depending on the version of macOS, your terminal emulator and/or IDE may also need to be whitelisted.

### WebSocket Mode:
```
python card_reader_server.py -s
```

## Supervisor configuration

To run the script using Supervisor, use the following configuration:

```
[program:apiary-nfc-reader]
directory=<path to where you cloned it>
command=DISPLAY=":0" python card_reader_server.py <-k or -s>
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=<pick a location>
user=<pick a user>
```
