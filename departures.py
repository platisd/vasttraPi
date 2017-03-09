#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pytrafik.client
import json

apiKey = None
apiSecret = None

LINDHOLMEN_ID = "9021014004490000"

# Fethes the consumer and secret key from configuration file (not version controlled).
# The first line is the key and the second is the secret.
def initAPIkeys():
    pathToConfig = "api-config"
    f = open(pathToConfig)
    global apiKey, apiSecret
    apiKey = f.readline().replace('\n', "")
    apiSecret = f.readline().replace('\n', "")
    f.close()


def main():
    initAPIkeys()
    vasttrafik = pytrafik.client.Client("json", apiKey, apiSecret)
    departures = vasttrafik.get_departures(LINDHOLMEN_ID)
    for departure in departures:
        print (departure)



if __name__ == "__main__":
    main()
