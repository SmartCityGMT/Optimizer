#!/usr/bin/env python

import sys, os
import csv
 
import requests
import googlemaps
from datetime import datetime
import time

###################################################################
d_address = '107 South High Street'
d_city = 'Columbus'
d_state = 'Ohio'
###################################################################


###################################################################
o_address = '1112 East Main Street'
o_city = 'Columbus'
o_state = 'Ohio'
###################################################################

###################################################################
final_dest_eta = '2017-05-08 18:00:00'
final_destination_etd = '2017-05-08 20:15:00'


#Lat and long of final destination
d_full_address = d_address + ',' + d_city + ',' + d_state
         
response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+d_full_address)
 
resp_json_payload = response.json()

 
orig_lat = str(resp_json_payload['results'][0]['geometry']['location']['lat'])
orig_lng = str(resp_json_payload['results'][0]['geometry']['location']['lng'])

####Starting point lat and long
o_full_address = o_address + ',' + o_city + ',' + o_state
         
response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+o_full_address)
 
resp_json_payload = response.json()
 
start_lat = str(resp_json_payload['results'][0]['geometry']['location']['lat'])
start_long = str(resp_json_payload['results'][0]['geometry']['location']['lng'])

spot_reservations = {}
with open('reservations.csv', 'r') as f:
	reader = csv.reader(f)
	next(reader, None)
	for row in reader:
		spot_reservations[row[0]] = [row[1], row[2]]

		
all_spots = {}		
with open('parking_spot_info.csv', 'r') as f:
	reader = csv.reader(f)
	next(reader, None)
	for row in reader:
		all_spots[row[0]] = [row[1], row[2], row[3]]
		
availability = {}	
with open('availability.csv', 'r') as f:
	reader = csv.reader(f)
	next(reader, None)
	for row in reader:
		availability[row[0]] = [row[1], row[2], row[3]]		
	
qual_spots = []
	
		
		

#Calculate walking times
walking_calcs = {}
for spot in all_spots.keys():
    #insert personal api key below
	gmaps = googlemaps.Client(key = '')
	dest_lat = all_spots[spot][0]
	dest_lng = all_spots[spot][1]
	orig_coord = orig_lat, orig_lng
	dest_coord = dest_lat, dest_lng
	result = gmaps.distance_matrix(orig_coord, dest_coord, mode = "walking")
	#spits out walking time in seconds
	walking_time = result['rows'][0]['elements'][0]['duration']['value']
	#add calc to dictionary
	walking_calcs[spot] = walking_time

		
		
final_eta = datetime.strptime(final_dest_eta, '%Y-%m-%d %H:%M:%S').timestamp()

destination_etd = datetime.strptime(final_destination_etd, '%Y-%m-%d %H:%M:%S').timestamp()


park_info = {}
for temp in walking_calcs.keys():
	parking_eta = final_eta - walking_calcs[temp] - (5*60)

	parking_etd = (destination_etd + walking_calcs[temp] + (5*60))

	park_duration = (destination_etd + walking_calcs[temp] + (5*60)) - parking_eta
	
	park_info[temp] = [parking_eta,parking_etd,park_duration]


#Check if reserved
for spot in park_info:
	for reserv in spot_reservations.keys():
		if spot == reserv:
			if park_info[spot][1] < datetime.strptime(spot_reservations[reserv][0], '%Y-%m-%d %H:%M:%S').timestamp():
				qual_spots.append(reserv)
			elif park_info[spot][0] > datetime.strptime(spot_reservations[reserv][1], '%Y-%m-%d %H:%M:%S').timestamp():
				qual_spots.append(reserv)
			elif reserv in qual_spots:
				qual_spots.remove(reserv)
		elif spot not in spot_reservations.keys():
			qual_spots.append(reserv)

#Check if in operation
for spot in park_info:
	for avail in availability.keys():
		if spot == avail:
			if park_info[spot][0] >= datetime.strptime(availability[avail][1], '%Y-%m-%d %H:%M:%S').timestamp() and park_info[spot][1] <= datetime.strptime(availability[avail][2], '%Y-%m-%d %H:%M:%S').timestamp():
				qual_spots.append(avail)
			elif avail in qual_spots:
				qual_spots.remove(avail)

			
		
min_dur = 1000000000000000000
for spots in qual_spots:
    if park_info[spots][2] < min_dur:
        min_dur = park_info[spots][2]
        best_spot = spots

print("Parking Latitude:")
print(all_spots[best_spot][0])
print("Parking Longitude:")
print(all_spots[best_spot][1])
print("Total Walking Time:")
print(walking_calcs[best_spot]/60)
print("Total Cost:")
print(float(all_spots[best_spot][2])*(park_info[best_spot][2]/3600))		

orig_coord = start_lat, start_long
dest_coord = dest_lat, dest_lng
result = gmaps.distance_matrix(orig_coord, dest_coord, mode = "driving")

#spits out drive time in seconds
drive_time = result['rows'][0]['elements'][0]['duration']['value']

print("Leave at:")
time_to_leave = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(datetime.strptime(final_dest_eta, '%Y-%m-%d %H:%M:%S').timestamp() - (walking_calcs[best_spot] + (5*60) + drive_time)))

print(time_to_leave)





