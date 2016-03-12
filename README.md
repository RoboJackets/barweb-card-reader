# Barweb card reader

Script for piping NFC card ID to Barweb through a web socket.

Using Python 2.7.


## Package requirements

* libusb
* libpcsclite
* libnfc
* python-pyscard
* python-twisted
* python-autobahn
* pcscd

On Ubuntu, the packages can be installed using the following command;

```
sudo apt-get install libusb-dev libpcsclite-dev libnfc-dev python-pyscard python-twisted python-autobahn pcscd
```


## Running the script

To run the script, issue the following command;

```
python src/card_reader_server.py
```
