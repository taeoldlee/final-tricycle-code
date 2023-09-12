"""
for use in Visual Studio Code

USAGE: This code will open a graph for each "red line event" duration
user will click on points of interest on the graph such as 
beginning and end of rise time, end of settling time, peak over/undershoot,
and steady state error line endpoints. 

NOTE: Rise time is the time for the signal to go from 10%-90% of the path to the final angle. 
Settling time is the time it takes for the signal to go from 10% of the path to the final angle 
to the time it takes for the sensor to settle within a 5% tolerance band of the final angle.
Overshoot/undershoot is measured as the amount the signal exceeded the final value measured in percentage. 
Steady state error compares the value of the signal after it has had time to settle down to the final angle.

the terminal will then output the key metrics used for further comparison in Excel.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Cursor

def on_key(event):
    """
    Handles key press events to skip certain points of interest on the graph.
    
    Parameters:
    - event: matplotlib event object
        The key press event triggered by user
        
    Global Variables Modified:
    - action_counter: int
        Tracks number of clicks or key presses
        
    Notes:
    - 'x' key is used to skip a point, which is then represented by 'None' in the data.
    - Mostly used for settling time and overshoot/undershoot; using it for other metrics may break the code.
    """
    global action_counter
    if event.key == 'x':
        if action_counter == 0:
            rise_time_start.append(None)
            plt.title("Skipped! Click on rise time end")
        elif action_counter == 1:
            rise_time_end.append(None)
            plt.title("Skipped! Click on settling time end")
        elif action_counter == 2:
            settling_time_end.append(None)
            plt.title("Skipped! Click on overshoot/undershoot peak")
        elif action_counter == 3:
            overshoot.append(None)
            plt.title("Skipped! Click on steady state start")
        elif action_counter == 4:
            steady_state_error_start.append(None)
            plt.title("Skipped! Click on steady state end")
        elif action_counter == 5:
            steady_state_error_end.append(None)
            plt.title("Skipped! You are done clicking")
        action_counter += 1
        plt.draw()

def onclick(event):
    """
    Handles mouse click events to capture points of interest on the graph.
    
    Parameters:
    - event: matplotlib event object
        The click event triggered by user
        
    Global Variables Modified:
    - action_counter: int
        Tracks number of clicks or key presses
        
    Notes:
    - Appends the x or y coordinate of the clicked point to respective data array
    """
    global action_counter

    if action_counter == 0:
        plt.title("Click on end rise time")
        rise_time_start.append(event.xdata)
    elif action_counter == 1:
        plt.title("Click on end settling time")
        rise_time_end.append(event.xdata)
    elif action_counter == 2:
        plt.title("Click on peak overshoot/undershoot")
        settling_time_end.append(event.xdata)
    elif action_counter == 3:
        plt.title("Click on steady state error start")
        overshoot.append(event.ydata)
    elif action_counter == 4:
        plt.title("Click on steady state error end")
        steady_state_error_start.append(event.ydata)
    elif action_counter == 5:
        plt.title("Clicking is done!")
        steady_state_error_end.append(event.ydata)
    action_counter += 1
    plt.draw()

# get angle and red line event data from csv files
angle_data = pd.read_csv('angle_data.csv') # name of angle data CSV made by AngleGraphic.py
red_line_data = pd.read_csv('red_line_events.csv') # name of red line events CSV made by AngleGraphic.py

# converts timestamps to datetime
angle_data['Timestamp'] = pd.to_datetime(angle_data['Timestamp'])
red_line_timestamps = pd.to_datetime(red_line_data['Timestamp'])
# extracts red line angles and event type
red_line_angles = red_line_data['Red_Line_Angle']
red_line_events = red_line_data['Event_Type']

# counts red line events from the CSV file
event_counter = 0

# loops through each red line event
for i, event in enumerate(red_line_events):
    # initialize variables for metrics of current event, inside loop since each event is different
    if event == 'Created':
        action_counter = 0
        rise_time_start, rise_time_end, settling_time_end, overshoot, steady_state_error_start, steady_state_error_end = [], [], [], [], [], []
        event_counter += 1
        target_angle = red_line_angles[i]
        start_time = red_line_timestamps[i]
        end_time = red_line_timestamps[i + 1] if i < len(red_line_events) - 1 else None
        filtered_angle_data = angle_data[(angle_data['Timestamp'] >= start_time) & (angle_data['Timestamp'] < end_time)]

        # error handling if data is empty, skips event
        if filtered_angle_data.empty:
            print(f'Red Line Event {event_counter} - Data is empty. Skipping this event.')
            continue

        # relative timestamps so that start is 0
        relative_timestamps = (filtered_angle_data['Timestamp'] - start_time).dt.total_seconds()
        angles = filtered_angle_data['Current_Angle']
        angles = angles.reset_index(drop=True)
        color = 'black'

        # initializes different milestone variables based on starting and target angles 
        starting_angle = angles[0]
        angle_diff = abs(starting_angle - target_angle)
        tenper = angle_diff * 0.1
        ninper = angle_diff * 0.9
        tenperline = starting_angle + (tenper if target_angle > starting_angle else -tenper)
        ninperline = starting_angle + (ninper if target_angle > starting_angle else -ninper)
        five_percent_difference = angle_diff * 0.05
        five_percent_above = target_angle + (five_percent_difference if target_angle > starting_angle else -five_percent_difference)
        five_percent_below = target_angle - (five_percent_difference if target_angle > starting_angle else -five_percent_difference)

        # plots the graph used for visual analysis
        plt.figure(figsize=(20, 8))
        plt.plot(relative_timestamps, angles, label=f'Red Line Event {event_counter}', color='black')
        plt.axhline(target_angle, alpha=0.5, color='black')
        plt.axhline(tenperline, linestyle='dashed', color='black')
        plt.axhline(ninperline, linestyle='dashed', color='black')
        plt.axhline(five_percent_above, linestyle='dashed', color='red', alpha=0.5) # 5% above
        plt.axhline(five_percent_below, linestyle='dashed', color='red', alpha=0.5) # 5% below
        plt.xlabel('Time (seconds)')
        plt.ylabel('Angle')
        plt.legend()
        plt.title("Click on start rise time, click 'x' to skip")
        cursor = Cursor(plt.gca(), useblit=True, color='red', linewidth=1)
        plt.connect('button_press_event', onclick)
        plt.connect('key_press_event', on_key)
        

        plt.show()


        # printing final results in terminal
        print("Red line event", event_counter)

        # calculate the applicable metrics
        rise_time_value = None if rise_time_start[0] is None or rise_time_end[0] is None else rise_time_end[0] - rise_time_start[0]
        settling_time_value = None if settling_time_end[0] is None or rise_time_start[0] is None else settling_time_end[0] - rise_time_start[0]
        overshoot_percent = None if overshoot[0] is None else (abs(target_angle -  overshoot[0]) / abs(starting_angle - target_angle)) * 100
        steady_state_error_value = None if steady_state_error_start[0] is None or steady_state_error_end[0] is None else abs(((steady_state_error_start[0] + steady_state_error_end[0]) / 2) - target_angle)

        # prints the applicable metrics, prints 'None' if does not exist
        print("Rise Time: {:.2f} seconds".format(rise_time_value) if rise_time_value is not None else "Rise Time: None")
        print("Settling Time: {:.2f} seconds".format(settling_time_value) if settling_time_value is not None else "Settling Time: None")
        print("Overshoot/Undershoot: {:.2f}%".format(overshoot_percent) if overshoot_percent is not None else "Overshoot/Undershoot: None")
        print("Steady-state error: {:.2f}%".format(steady_state_error_value) if steady_state_error_value is not None else "Steady-state error: (%) None")
        print("{:.2f}".format(rise_time_value) if rise_time_value is not None else "None")
        print("{:.2f}".format(settling_time_value) if settling_time_value is not None else "None")
        print("{:.2f}".format(overshoot_percent) if overshoot_percent is not None else "None")
        print("{:.2f}".format(steady_state_error_value) if steady_state_error_value is not None else "None")
        print("\n")

        