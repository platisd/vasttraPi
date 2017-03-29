#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pytrafik.client
import json
from socket import AF_INET, SOCK_DGRAM
import sys
import socket
import struct, time
import threading
from datetime import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk

apiKey = None
apiSecret = None
pathToConfig = "api-config"

mainThread = threading.current_thread()

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


# Get the next trips as a list of busline numbers and minutes to leave for the next two trips
def getNextTrips():
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
                    # Sometimes rtTime is not returned, so fall back to normal time instead
                    departureTime = departure['rtTime'] if 'rtTime' in departure else departure['time']
                    trips[departure['sname']].append(departureTime)
                    #print ("Bus %s leaves towards %s at %s" % (departure['sname'], departure['direction'], departure['rtTime']))
                except Exception as e:
                    print ("Error while parsing server response")
    #print (sorted(trips.items()))
    nextTrips=[]
    for busLine, departureTimes in trips.items():
            remainingDepartures = 2  # The number of departures that we care to show
            for departureTime in departureTimes:
                remainingDepartures -= 1
                if remainingDepartures < 0:
                    break
                minutesToLeave = ((datetime.strptime(departureTime, "%H:%M") - datetime.strptime(currentTime, "%H:%M")).total_seconds() / 60)
                # If a bus leaves the next day, the above result will be a negative number, therefore we need to completement it
                # with the amount of minutes in a day (1440)
                if minutesToLeave < 0:  # meaning that the next departure time is on the next day
                    MINUTES_IN_DAY = 1440
                    minutesToLeave += MINUTES_IN_DAY
                #print ("Bus %s, leaves in %d" % (busLine, minutesToLeave))
                nextTrips.append((busLine, minutesToLeave))
    return nextTrips



class GUI:
    def __init__(self, master, **kwargs):
        self.master = master
        master.grid()
        master.title("Departures")

        # f = Frame(root, bg = "orange", width = 500, height = 500)
        # f.pack(side=LEFT, expand = 1)
        #
        # f3 = Frame(f, bg = "red", width = 500)
        # f3.pack(side=LEFT, expand = 1, pady = 50, padx = 50)
        #
        # f2 = Frame(root, bg = "black", height=100, width = 100)
        # f2.pack(side=LEFT, fill = Y)

        # A new frame inside master with boarder
        headerFrame = tk.Frame(master, bd="0")
        # Set the header frame's background to black
        headerFrame.configure(background='black')
        # Use the grid layout and expand the frame
        headerFrame.grid(row=0, sticky=tk.E+tk.W)

        # Label inside heade frame
        headerLbl = tk.Label(headerFrame, text="Departures", font=("Helvetica bold", 25), bg="black", fg="white")
        # Place label on grid layout, row 0 and do not expand
        headerLbl.grid(row=0)
        # Center column 0 inside header frame
        headerFrame.grid_columnconfigure(0, weight=1)

        subHeadersFrame = tk.Frame(master)
        subHeadersFrame.configure(background='black')
        subHeadersFrame.grid(row=1, sticky=tk.E+tk.W)

        busNoLbl = tk.Label(subHeadersFrame, text="Bus Number", font=("Helvetica", 20), bg="black", fg="white")
        busNoLbl.grid(row=0, column=0)
        busDestLbl = tk.Label(subHeadersFrame, text="Destination", font=("Helvetica", 20), bg="black", fg="white")
        busDestLbl.grid(row=0, column=1)
        minsLeftLbl = tk.Label(subHeadersFrame, text="Minutes Left", font=("Helvetica", 20), bg="black", fg="white")
        minsLeftLbl.grid(row=0, column=2)
        # Center column 0 inside header frame
        subHeadersFrame.grid_columnconfigure(0, weight=1)
        subHeadersFrame.grid_columnconfigure(1, weight=1)
        subHeadersFrame.grid_columnconfigure(2, weight=1)


        # Keep everything in column 0 of master centered/expanded
        master.grid_columnconfigure(0, weight=1)

        w, h = master.winfo_screenwidth(), master.winfo_screenheight()
        master.overrideredirect(0)
        master.geometry("%dx%d+0+0" % (w, h))

    # Receives a list of tuples (busline, minutesToLeave) as the argument and displays them
    def populateTable(self, departures):
        # l2 = Label(self.master, text="Second")
        # l2.grid(row=1, sticky=W)
        currentRow = 1  # start from row 1
        for departure in departures:
            (bus, minutes) = departure
            bgColor = "white" if currentRow % 2 else "gray"
            busLbl = Label(self.master, text=bus, font=("Helvetica", 16), bg=bgColor)
            busLbl.grid(row=currentRow, column=0, sticky=W )
            minutesLbl = Label(self.master, text=int(minutes) if int(minutes) != 0 else "Now", font=("Helvetica", 16), bg=bgColor)
            minutesLbl.grid(row=currentRow, column=1, sticky=W)
            currentRow += 1


    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom

def updateGui(gui):
    nextTrips = getNextTrips()
    #gui.populateTable(nextTrips)
    if mainThread.is_alive():
        threading.Timer(30, updateGui, [gui]).start()



def main():
    # Initialize the API keys using the config file
    initAPIkeys()
    root = tk.Tk()
    gui = GUI(root)
    updateGui(gui)
    print ("Main loop")
    root.mainloop()


if __name__ == "__main__":
    main()
