# for use in Mu Editor under Pygame Zero mode in parallel with sensor code (CircuitPython)
# USAGE: The sensor should be mapped from 0-180. While running, type a number between 
# 40 and 140 and hit enter to create a red line of the inputted angle, then type 0 to 
# remove the red line. These actions should produce the angle_data.csv and 
# red_line_events.csv files
import pgzrun
import pygame
import pygame.gfxdraw
import math
import serial
from datetime import datetime
import csv
import sys

# screen dims
WIDTH = 1080
HEIGHT = 720

# max and min angles matching actual steering range
ANGLE_MIN = 40
ANGLE_MAX = 140
current_angle = ANGLE_MIN

# initialize red line
red_line_angle = None

# serial to communicate with raspberry pico (device with sensors)
pico_serial = serial.Serial('/dev/tty.usbmodem2101', 9600)

# initialize buffer for getting red line angles
input_buffer = ""

# makes CSV file for angle data, logging angle at timestamps
angle_file = open('angle_data.csv', 'w', newline='')
angle_writer = csv.writer(angle_file)
angle_writer.writerow(['Timestamp', 'Current_Angle'])

# makes CSV file for red line data, logging the angle and event type 
# (creation/removal) at timestamps
red_line_file = open('red_line_events.csv', 'w', newline='')
red_line_writer = csv.writer(red_line_file)
red_line_writer.writerow(['Timestamp', 'Red_Line_Angle', 'Event_Type'])

# moving average data point size, 1 for touch sensors, 4 for rest
# *this is because touch sensors don't need noise handling, others do*
# FILTER_WINDOW_SIZE = 1 #TOUCH SENSOR
FILTER_WINDOW_SIZE = 4 #EVERYTHING ELSE
# holds moving averages
angle_history = []

# function to map sensor output to min-max range (40-140)
def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# visual for the game
def draw():
    global red_line_angle
    
    # whole screen is white
    screen.fill((255, 255, 255))
    center = WIDTH // 2, HEIGHT // 2

    # draw arc for steering range (40-140)
    radius = 250
    start_angle = math.radians(180 - ANGLE_MAX)
    end_angle = math.radians(180 - ANGLE_MIN)
    rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    pygame.draw.arc(screen.surface, (0,0,0), rect, start_angle, end_angle, 10)

    # draws black current angle line
    arrow_length = 200
    arrow_angle = math.radians(180 - current_angle)
    arrow_end = center[0] + arrow_length * math.cos(arrow_angle), center[1] - arrow_length * math.sin(arrow_angle)
    pygame.draw.line(screen.surface, (0,0,0), center, arrow_end, 5)

    # draws red line if exists
    if red_line_angle is not None:
        red_line_end = center[0] + radius * math.cos(math.radians(180 - red_line_angle)), center[1] - radius * math.sin(math.radians(180 - red_line_angle))
        pygame.draw.line(screen.surface, (255,0,0), center, red_line_end, 5)

    # displays current angle as text below the steering range
    screen.draw.text("{:.0f}".format(current_angle), (WIDTH // 2, HEIGHT - 50), color=(0,0,0), fontsize=60, center=(WIDTH // 2, HEIGHT - 50))

# updates game based on sensor data
def update():
    global current_angle, red_line_angle, angle_history
    sensor_data = pico_serial.readline().decode().strip()
    try:
        # gets sensors value, values over 179 set to 179, under 0 set to 0
        sensor_value = float(sensor_data)
        sensor_value = max(min(sensor_value, 179), 0)

        # apply moving average filter
        angle_history.append(sensor_value)
        if len(angle_history) > FILTER_WINDOW_SIZE:
            angle_history = angle_history[1:]
        smoothed_angle = sum(angle_history) / len(angle_history)

        # computes angle that should be displayed on visual
        current_angle = map_value(smoothed_angle, 0, 179, ANGLE_MIN, ANGLE_MAX)

        # logs timestamps and angles in CSV for analysis 
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        angle_writer.writerow([timestamp, current_angle])
        print('Wrote angle data:', [timestamp, current_angle])

    # error handling
    except ValueError:
        pass


def on_key_down(key):
    global red_line_angle, input_buffer

    # quit when press 'q'
    if key == keys.Q:  
        angle_file.close()
        red_line_file.close()
        print('Closed angle file')
        print('Closed red line file')
        pygame.quit()
        sys.exit(0)

    # handles keyboard input for creating or removing red line angle
    else:
        if key == keys.RETURN:
            try:
                angle = float(input_buffer)
                timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
                if ANGLE_MIN <= angle <= ANGLE_MAX:  # angle is valid angle
                    red_line_angle = angle
                    red_line_writer.writerow([timestamp, red_line_angle, 'Created'])
                    print('Wrote red line creation event:', [timestamp, red_line_angle, 'Created'])
                elif angle == 0:  # remove red line / angle is invalid
                    red_line_angle = None
                    red_line_writer.writerow([timestamp, '', 'Removed'])
                    print('Wrote red line removal event:', [timestamp, '', 'Removed'])
                input_buffer = ""  # clear buffer
            except ValueError:
                input_buffer = ""  # clear buffer on invalid input
        else:
            if key in range(48, 58):  # check if key is a number
                input_buffer += str(key - 48)  # add char to buffer

# runs game
pgzrun.go()
