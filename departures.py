#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pytrafik.client
import json
from socket import AF_INET, SOCK_DGRAM
import sys
import socket
import struct, time

apiKey = None
apiSecret = None

LINDHOLMEN_ID = "9021014004490000"
TEKNIKGATAN_ID = "9021014006675000"
stations = [LINDHOLMEN_ID, TEKNIKGATAN_ID]


# Fetches the time from NTP server. Source: http://blog.mattcrampton.com/post/88291892461/query-an-ntp-server-from-python
def getNTPTime(host = "pool.ntp.org"):
    port = 123
    buf = 1024
    address = (host,port)
    msg = '\x1b' + 47 * '\0'

    # reference time (in seconds since 1900-01-01 00:00:00)
    TIME1970 = 2208988800 # 1970-01-01 00:00:00

    # connect to server
    client = socket.socket( AF_INET, SOCK_DGRAM)
    client.sendto(bytes(msg, "UTF-8"), address)
    msg, address = client.recvfrom( buf )

    t = struct.unpack( "!12I", msg )[10]
    t -= TIME1970
    #return time.ctime(t).replace("  "," ")
    #return time.strftime("%H:%M", time.ctime(t))
    d = time.strptime(time.ctime(t),"%a %b %d %H:%M:%S %Y")
    return (time.strftime("%Y-%m-%d", d), time.strftime("%H:%M", d))


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
    # Initialize the API keys using the config file
    initAPIkeys()
    # Get the current time and date from an NTP server as the host might not have an RTC
    (currentDate, currentTime) = getNTPTime()
    # Initialize the connection to the Vasttrafik server
    vasttrafik = pytrafik.client.Client("json", apiKey, apiSecret)
    for station in stations:
        # Get the departures for each station we are interested in
        departures = vasttrafik.get_departures(station, date=currentDate, time=currentTime)
        for departure in departures:
            #print (departure['direction'])
            if departure['track'] < 'C':
                print ("Bus %s leaves towards %s at %s" % (departure['sname'], departure['direction'], departure['time']))


if __name__ == "__main__":
    main()
