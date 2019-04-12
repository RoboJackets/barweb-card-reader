# Apiary NFC Reader

Script for piping GTID / Prox # from BuzzCards to Apiary through a web socket.


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

## Running the script

To run the script, issue the following command;

```
python card_reader_server.py
```
