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
import os

# Change working directory to the one that the file is residing in
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

apiKey = None
apiSecret = None
pathToConfig = "api-config"

mainThread = threading.current_thread()

LINDHOLMEN_ID = "9021014004490000"
TEKNIKGATAN_ID = "9021014006675000"
stations = {"Lindholmen": LINDHOLMEN_ID, "Teknikgatan": TEKNIKGATAN_ID}
destinations= {"16": "Marklandsgatan", "99": "Hj. Bratningsplatsen", "45": "Backebol",
               "55": "Johanneberg", "16X": "Centralstationen", "121": "Partille"}
sideColumnMinSize = 100
departureFontSize = 40
refreshRate = 29


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
        busDestLbl = tk.Label(subHeadersFrame, text="Destination", font=("Helvetica", 20), bg="black", fg="white")
        minsLeftLbl = tk.Label(subHeadersFrame, text="Minutes Left", font=("Helvetica", 20), bg="black", fg="white")

        busNoLbl.grid(row=0, column=0)
        busDestLbl.grid(row=0, column=1)
        minsLeftLbl.grid(row=0, column=2)
        # Expand the middle column so the other two move to the sides
        subHeadersFrame.grid_columnconfigure(1, weight=1)

        # The frame that will contain the departures
        departuresFrame = tk.Frame(master)
        departuresFrame.grid(row=2, sticky=tk.E+tk.W)
        departuresFrame.grid_columnconfigure(1, weight=1)
        self.departuresFrame = departuresFrame

        # Keep everything in column 0 of master centered/expanded
        master.grid_columnconfigure(0, weight=1)

        w, h = master.winfo_screenwidth(), master.winfo_screenheight()
        master.overrideredirect(0)  # Set to 1 to force full window mode
        master.geometry("%dx%d+0+0" % (w, h))

    # Receives a list of tuples (busline, minutesToLeave) as the argument and displays them
    def populateTable(self, departures):
        currentRow = 0
        for departure in departures:
            (bus, minutes) = departure
            # Change background color for each row
            bgColor = "white" if currentRow % 2 else "gray"

            # The frame that will contain each departure
            rowFrame = tk.Frame(self.departuresFrame)
            rowFrame.grid(row=currentRow, columnspan=3, sticky=tk.E+tk.W)
            rowFrame.configure(background=bgColor)
            currentRow += 1

            # After we have created the frame that will hold each departure, create the labels
            busNo = tk.Label(rowFrame, text=bus, font=("Helvetica", departureFontSize), bg=bgColor)
            busDest = tk.Label(rowFrame, text=destinations.get(bus, bus), font=("Helvetica", departureFontSize), bg=bgColor)
            minsLeft = tk.Label(rowFrame, text=int(minutes) if int(minutes) != 0 else "Now", font=("Helvetica", departureFontSize), bg=bgColor)
            busNo.grid(row=0, column=0)
            busDest.grid(row=0, column=1)
            minsLeft.grid(row=0, column=2)

            # Expand the middle column to push the other two to the sides
            rowFrame.grid_columnconfigure(1, weight=1)
            # Set the minimum size of the side columns so the middle column text is always at the same position
            rowFrame.grid_columnconfigure(0, minsize=sideColumnMinSize)
            rowFrame.grid_columnconfigure(2, minsize=sideColumnMinSize)

    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom

def updateGui(gui):
    # Get the next trips from Vasttrafik's public API for the station we are interested in
    nextTrips = getNextTrips() # contains a list of tuples (bus, minutesToDepart)
    # Sort the trips based on departure time (i.e. the second element in the tuples)
    nextTrips.sort(key=lambda trips: trips[1])
    gui.populateTable(nextTrips)
    if mainThread.is_alive():
        threading.Timer(refreshRate, updateGui, [gui]).start()



def main():
    # Initialize the API keys using the config file
    initAPIkeys()
    root = tk.Tk()
    gui = GUI(root)
    updateGui(gui)  # Periodically update the gui with the latest departures
    root.mainloop()  # Blocking loop


if __name__ == "__main__":
    main()
