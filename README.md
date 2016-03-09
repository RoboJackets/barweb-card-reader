# Barweb card reader

Script for piping NFC card ID to Barweb through a web socket.

Using Python 2.7.


## Python package requirements

* pyscard, a Python smart card library
* twisted, an asynchronous networking framework

On Ubuntu, the packages can be installed using the following command;

```
pip install -r requirements.txt
```

This command requires Pip to be installed on your system.


## Running the script

To run the script, issue the following command;

```
python src/card_reader_server.py
```
