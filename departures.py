#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pytrafik.client
import json
from socket import AF_INET, SOCK_DGRAM
import sys
import socket
import struct, time
from datetime import datetime
from collections import defaultdict

apiKey = None
apiSecret = None
pathToConfig = "api-config"

LINDHOLMEN_ID = "9021014004490000"
TEKNIKGATAN_ID = "9021014006675000"
stations = {"Lindholmen": LINDHOLMEN_ID, "Teknikgatan": TEKNIKGATAN_ID}


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
    d = time.strptime(time.ctime(t),"%a %b %d %H:%M:%S %Y")
    return (time.strftime("%Y-%m-%d", d), time.strftime("%H:%M", d))


# Fethes the consumer and secret key from configuration file (not version controlled).
# The first line is the key and the second is the secret.
def initAPIkeys():
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
    try:
        vasttrafik = pytrafik.client.Client("json", apiKey, apiSecret)
    except Exception as e:
        print ("Authentication failure, exiting!")
    trips = defaultdict(list)  # A dictionary of lists, holding a list of departures for each bus
    for stationName, stationID in stations.items():
        # Get the departures for each station we are interested in
        try:
            departures = vasttrafik.get_departures(stationID, date=currentDate, time=currentTime)
        except Exception as e:
            print ("Connection failure for station %s" % stationName)
            departures = []  # If something went wrong, empty the departures list so we don't try to iterate through them
        for departure in departures:
            if departure['track'] < 'C':  # We only care for buses going towards the center for now
                try:
                    trips[departure['sname']].append(departure['rtTime'])
                    #print ("Bus %s leaves towards %s at %s" % (departure['sname'], departure['direction'], departure['rtTime']))
                except Exception as e:
                    print ("Error while parsing server response")
    #print (sorted(trips.items()))
    for busLine, departureTimes in trips.items():
            remainingDepartures = 2  # The number of departures that we care to show
            for departureTime in departureTimes:
                remainingDepartures -= 1
                if remainingDepartures < 0:
                    break
                minutesToLeave = ((datetime.strptime(departureTime, "%H:%M") - datetime.strptime(currentTime, "%H:%M")).total_seconds() / 60)
                print ("Bus %s, leaves in %d" % (busLine, minutesToLeave))



if __name__ == "__main__":
    main()
