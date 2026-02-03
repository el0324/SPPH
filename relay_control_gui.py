#Notes to self:
#This is the Python version used to build this code in Visual Studio Code:
#3.13.3 (tags/v3.13.3:6280bb5, Apr  8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]; 
#Relay logic: set to be 0/LOW to turn on, and 1/HIGH to turn off

#Import
import sys
import threading
import csv
from pyfirmata2 import ArduinoMega
import tkinter as tk
from tkinter import * 
import time
from time import sleep
from datetime import datetime
from dataclasses import dataclass

#================================= Constants =================================#
BOARD               = ArduinoMega('COM5') 
WIN                 = tk.Tk()
MY_CANVAS           = tk.Canvas(WIN, width = 1280, height= 660)
BACKGROUND_IMG      = tk.PhotoImage(file="./birchbg.png")
TITLE_FONT          = ('Arial', 40, 'bold')
INPUT_FONT          = ('Arial', 50)
REGULAR_FONT        = ('Arial', 30)
STOP_FONT           = ('Arial', 40, 'bold')
PINLIST             = [41, 40, 39, 38, 37, 36, 35, 34, 
                        33, 32, 31, 30, 29, 28, 27, 26]
RELAY_NAMES         = ["Relay 1", "Relay 2", "Relay 3", "Relay 4", "Relay 5",
                        "Relay 6", "Relay 7", "Relay 8", "Relay 9", "Relay 10",
                        "Relay 11", "Relay 12", "Relay 13", "Relay 14", "Relay 15",
                        "Relay 16"]
MANUAL_OPTIONS      = ["Off"] + RELAY_NAMES[1:]
SENSOR_PIN          = 0
SAMPLING_RATE       = 1000  # in milliseconds
RELAY_FIELDNAMES    = ['RUN', 'DELAY (s)', 'RELAY', 'START TIME', 'END TIME', 
                        'SENSOR']
SENSOR_FIELDNAMES   = ['RUN', 'RELAY', 'TIME', 'SENSOR VALUE', 'STATUS']
DATE                = datetime.date(datetime.today())
LOWER_OPEN_THRES    = 0.1545
UPPER_OPEN_THRES    = 0.1848
LOWER_AMB_THRES     = -0.009
UPPER_AMB_THRES     = 0.002
RAW_AMB             = 0.4976

#================================== Classes ==================================#
@dataclass
class GUIState:
    delay:              float = 0.0 # Delay time between each relay for automated run
    start_time:         float = 0.0 # Time that automated/manual run was started
    local_start_time:   float = 0.0 # Time that automated/manual run was started  
                                    # (used for logging)
    elapsed:            float = 0.0 # Percentage of run time completed (used
                                    # for logging)
    selected_run:       str = "" # Which run (automated or manual) is currently being
    selected_relay:     str = "" # Relay selected for manual run
    relay_open:         str = "Off" # Relay that is currently open ("Off" means
                                    # default state)
    sensor_val:         str = "" # Sensor measurement data (in absolute form -
                                    # ambient value set as zero)
    sensor_status_text: str = "IDLE" # Status of the sensor (IDLE, OPEN, LEAK,
                                        # or AMBIENT)
    sensor_text_bd:     str = "#6B6B6E" # Background colour for sensor_status_text

class GUIWidgets:
    def __init__(self):
        self.button_start           = None  # Automated Start button
        self.button_manual          = None  # Maunal Start button
        self.button_exit            = None  # Exit button
        self.selected_manual_option = None  # Relay selected from manual drop-down menu
        self.relay_time             = None  # Relay delay time input
        self.selected_relay_text    = None  # Text to show which relay is open
        self.completion_text        = None  # Text to show completion percentage
        self.sensor_value_text      = None  # Text displayed when Check Sensor
                                            # button is pressed
        self.sensor_status_window   = None  # Display for sensor status 

#================================ Functions ==================================#
def default_state(state: GUIState, widget: GUIWidgets) -> None:
    """ Sets the default state. Turn everyone off but the first relay, and set 
    the initial logic for some global variables. 
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """  
    # turn all relays off
    for i in range(26,42):
        BOARD.digital[i].write(1)
    
    # keep the first relay on
    BOARD.digital[PINLIST[0]].write(1)

    # reset completion and selected relay
    state.relay_open = "Off"
    state.elapsed = 0.0
    widget.completion_text = MY_CANVAS.create_text(50, 495, 
                                text="Run Percent Complete: 0%", font=REGULAR_FONT, 
                                anchor = 'nw')
    widget.selected_relay_text = MY_CANVAS.create_text(50, 550, text="LED select is Off", 
                                                font=REGULAR_FONT, anchor = 'nw')

    # reset start and end time and selecte run
    state.start_time = 0.0
    state.selected_run = ""

def log_relay(run: str, delay: float|None, relay: str, start, end, state: GUIState) -> None:
    """ Logs data to a .csv file with the name of the file being the date it was
    created (ex. 11-14-2025.csv). Log files are created with the "Logs" folder. 
    The log data include the type of run (automated or manual), the delay time, 
    which relay is open, when the run started, when the run was 
    completed/ended, and the absolute value from the sensor 

    parameters: 
        run: either "AUTOMATED" or "MANUAL"
        delay: relay delay in seconds
        relay: the relay that data is being collected from
        start: time at which the relay opened
        end: time at which the realy closed
        state: GUIState class
    """
    # convert timestamps into local time/date
    if run == " ":
        start = " "
        end = " "
        sensor = " "
    elif relay == 'Complete automated run':
        start = time.strftime("%m/%d/%Y %H:%M:%S", start)
        end = time.strftime("%m/%d/%Y %H:%M:%S", end)
        sensor = " "
    else:
        start = time.strftime("%m/%d/%Y %H:%M:%S", start)
        end = time.strftime("%m/%d/%Y %H:%M:%S", end)
        sensor = f'{state.sensor_val} {state.sensor_status_text}'

    # format data
    data = {'RUN': f'{run}', 
            'DELAY (s)': f'{delay}',
            'RELAY': f'{relay}', 
            'START TIME': f'{start}', 
            'END TIME': f'{end}',
            'SENSOR': sensor}

    # write to log file
    if run != "":
        with open(f'./Relay_Logs/relay-{DATE}.csv', 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=RELAY_FIELDNAMES)
            writer.writerow(data)

#================================ Run Code: ==================================#
def button_stop_command(state: GUIState, widget: GUIWidgets) -> None:
    """ If the STOP button is pressed then terminate the loop for the automated 
    code, and put all relays in their default state. For ease of use, this stop 
    button will work for both automated and manual states. 

    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """
    # get end time
    end_time = time.localtime()

    # set data based on run
    if state.selected_run == "AUTOMATED":
        state.selected_relay = state.relay_open
    elif state.selected_run == "MANUAL":
        state.delay = None

    # log data
    log_relay(state.selected_run, state.delay, state.selected_relay, 
            state.local_start_time, end_time, state)
    log_relay(" ", " ", " ", state.local_start_time, end_time, state)

    # reset GUI settings
    state.relay_open = "Off"
    widget.button_start['state'] = tk.NORMAL
    widget.button_manual['state'] = tk.NORMAL
    widget.button_exit['state'] = tk.NORMAL

    # set relays to default state
    MY_CANVAS.delete(widget.completion_text)
    MY_CANVAS.delete(widget.selected_relay_text)
    default_state(state, widget)

def button_start_command(state: GUIState, widget: GUIWidgets) -> None:
    """ Runs the automated test when the AUTOMATED START button is pressed. 
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """  
    # if transitioning from manual to automated code, intial to default state
    if state.selected_run == "MANUAL":
        MY_CANVAS.delete(widget.completion_text)
        MY_CANVAS.delete(widget.selected_relay_text)
        default_state(state, widget)
    
    # get the delay and start time
    state.delay = float(widget.relay_time.get())
    state.start_time = time.time()
    state.local_start_time = time.localtime()
    state.selected_run = "AUTOMATED"
    
    # prepare to start test
    current_relay = 1

    # automated run loop
    while current_relay <= (len(PINLIST)-1):
        # Disable start buttons once this loop starts so nothing gets pressed twice
        # and open multiple samplers
        widget.button_start['state'] = tk.DISABLED 
        widget.button_manual['state'] = tk.DISABLED
        widget.button_exit['state'] = tk.DISABLED

        # open one relay and measure differential pressure 
        state.relay_open = RELAY_NAMES[current_relay]
        BOARD.digital[PINLIST[current_relay]].write(0)
        BOARD.digital[PINLIST[0]].write(0)
        relay_start_time = time.localtime()

        # wait for delay amount of time, then close relay
        time.sleep(state.delay)
        current_relay += 1
        BOARD.digital[PINLIST[current_relay-1]].write(1)
        relay_end_time = time.localtime()

        # log start/end time for relay
        log_relay(state.selected_run, state.delay, state.relay_open, 
                  relay_start_time, relay_end_time, state)

    # get end time, turn off sensor sampling, and log data
    end_time = time.localtime()
    log_relay(state.selected_run, state.delay, 'Complete automated run', state.local_start_time, 
                end_time, state)
    log_relay(" ", " ", " ", state.local_start_time, end_time, state)

    # return to default state once run is complete
    MY_CANVAS.delete(widget.completion_text)
    MY_CANVAS.delete(widget.selected_relay_text)
    default_state(state, widget)

    # Re-enable buttons once test is done
    widget.button_start['state'] = tk.NORMAL
    widget.button_manual['state'] = tk.NORMAL
    widget.button_exit['state'] = tk.NORMAL

def button_starter(state: GUIState, widget:GUIWidgets) -> None:
    """ Starts thread for automated run

    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """
    t = threading.Thread(target=button_start_command, args=(state, widget))
    t.start()

def manual_start(state: GUIState, widget: GUIWidgets) -> None:
    """ Runs the manual test with the selected relay when the MANUAL START button
    is pressed 
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """
    # set default state at the beginning of this function
    MY_CANVAS.delete(widget.completion_text)
    MY_CANVAS.delete(widget.selected_relay_text)
    default_state(state, widget)

    # get which relay was selected
    state.selected_relay = str(widget.selected_manual_option.get()) 

    # set start time and selected run
    state.local_start_time = time.localtime()
    state.selected_run = "MANUAL"

    # If off is selected, return to default state
    if state.selected_relay == "Off": 
        MY_CANVAS.delete(widget.selected_relay_text)
        default_state(state, widget)

    # If relay selected isn't off, open that relay.
    else: 
        widget.button_start['state'] = tk.DISABLED 
        widget.button_manual['state'] = tk.DISABLED
        widget.button_exit['state'] = tk.DISABLED
        position = []
        for i in range(len(MANUAL_OPTIONS)):
            if MANUAL_OPTIONS[i] == state.selected_relay:
                position.append(i)
                int_result = int(''.join(map(str, position)))
                BOARD.digital[PINLIST[int_result]].write(0)
                BOARD.digital[PINLIST[0]].write(0)
        state.relay_open = state.selected_relay

#=============================== Sensor Code: ================================#
def format_sensor_data(data, state: GUIState) -> None:
    """ Takes incoming data from the differential pressure sensor and formats it
    for logging and status updates.
    
    parameters:
        data: incoming sensor data
        state: GUIState class
    """ 
    # change data into absolute value relative to 0.4976 (the ambient value)
    state.sensor_val = round(data - RAW_AMB, 4)
    
    # update sensor status based on measurement
    if state.sensor_val > LOWER_OPEN_THRES and state.sensor_val < UPPER_OPEN_THRES: # normal operations
        state.sensor_status_text = "OPEN"
        state.sensor_text_bd = "#00cc1f"
    elif state.sensor_val > LOWER_AMB_THRES and state.sensor_val < UPPER_AMB_THRES:  # ambient
        state.sensor_status_text = "AMBIENT"
        state.sensor_text_bd = "#6B6B6E"
    elif state.sensor_val < LOWER_AMB_THRES:  # leak
        state.sensor_status_text = "LEAK"
        state.sensor_text_bd = "#cc0000"
    else: # pressure is not within desired range (either greater or less than expected)
        state.sensor_status_text = "WARNING"
        state.sensor_text_bd = "#ffea00"

    # set time of measurement
    measurement_time = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime())

    # format data
    log_data = {
                'RUN': f'{state.selected_run}', 
                'RELAY': f'{state.relay_open}', 
                'TIME': f'{measurement_time}',
                'SENSOR VALUE': f'{state.sensor_val}',
                'STATUS': F'{state.sensor_status_text}'
            }

    # write to sensor log file
    with open(f'./Sensor_Logs/sensor-{DATE}.csv', 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=SENSOR_FIELDNAMES)
        writer.writerow(log_data)

def button_sensor_command(state: GUIState, widget: GUIWidgets) -> None:
    """ Displays sensor value 
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """
    raw_value = round(state.sensor_val+RAW_AMB, 4)
    MY_CANVAS.delete(widget.sensor_value_text)
    widget.sensor_value_text = MY_CANVAS.create_text(370, 350, text=raw_value, 
                                                    font=TITLE_FONT, anchor = 'nw')

#================================= Widgets: ==================================#
def window_inti(background: PhotoImage) -> None:
    """ Initializes the GUI window and sets the GUI background.
    
    parameters:
        background: window background image
    """

    #Initialize the GUI window "win"
    WIN.title("Relay Control GUI")
    WIN.minsize(1280,660)

    # create canvas widget
    MY_CANVAS.pack(fill = "both", expand=TRUE)

    # set up background image
    MY_CANVAS.create_image(0, 0, image=background, anchor = 'nw')

def setup_window(state: GUIState, widget: GUIWidgets) -> None:
    """ Sets up all the buttons and text within the GUI 
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """
    #================= Left Side =================#
    #Manual Drop Down Menu:
    widget.selected_manual_option = tk.StringVar(WIN)
    widget.selected_manual_option.set(MANUAL_OPTIONS[0]) # default value

    # Label Manual Select
    MY_CANVAS.create_text(50, 55, text="Manual Select:", font=TITLE_FONT, 
                            anchor = 'nw')

    # Menu Manual Select
    manual_selection = OptionMenu(WIN, widget.selected_manual_option, *MANUAL_OPTIONS)
    button_manual_selection = MY_CANVAS.create_window(450,55, anchor = 'nw', 
                                                        window=manual_selection)
    manual_selection.config(font=REGULAR_FONT, bg = 'white')
    menu = WIN.nametowidget(manual_selection.menuname) 
    menu.config(font=REGULAR_FONT, bg = 'white')

    # Label Automated Run
    MY_CANVAS.create_text(50, 165, text="Automated Run:", font=TITLE_FONT, 
                            anchor = 'nw')

    # Entry Relay Time
    MY_CANVAS.create_text(50,245, text="Sequence Time (sec):", font=REGULAR_FONT, 
                            anchor = 'nw')
    widget.relay_time = Entry(WIN, bd=6, width=3, font=REGULAR_FONT)
    relay_time_window = MY_CANVAS.create_window(450,240, anchor = 'nw', 
                                                window=widget.relay_time)

    # Button Check Sensor
    button_sensor = Button(WIN, text="Check Sensor", font=REGULAR_FONT, 
                            command=lambda: button_sensor_command(state, widget))
    button_sensor_window = MY_CANVAS.create_window(50,340, anchor='nw', 
                                                    window=button_sensor)
    widget.sensor_value_text = MY_CANVAS.create_text(450, 340, text=state.sensor_val, 
                                                    font=TITLE_FONT, anchor = 'nw')

    #================= Right Side ================#
    # Sensor status
    sensor_status = Label(WIN, text=state.sensor_status_text, font=REGULAR_FONT, 
                            bg=state.sensor_text_bd, anchor='nw')
    widget.sensor_status_window = MY_CANVAS.create_window(700,55, anchor = 'nw', window=sensor_status)

    # Button Manual Start
    widget.button_manual = Button(WIN, text="Manual Start", font=TITLE_FONT, 
                            command=lambda: manual_start(state, widget))
    button_manual_window = MY_CANVAS.create_window(700,165, anchor = 'nw', 
                                                    window=widget.button_manual)

    # Button Automated Start
    widget.button_start = Button(WIN, text="Automated Start", font=TITLE_FONT, 
                            command=lambda: button_starter(state, widget))
    button_start_window = MY_CANVAS.create_window(700,330, anchor = 'nw', 
                                                    window=widget.button_start) 

    # Button Stop
    # bg = "#fff494"
    button_stop = Button(WIN, text="STOP", font=TITLE_FONT, fg = "red", 
                        relief = "solid", command=lambda: button_stop_command(state, widget)) 
    button_stop_window = MY_CANVAS.create_window(700,495, anchor = 'nw', 
                                                window=button_stop)

    # Button End
    widget.button_exit = Button(WIN, text="EXIT", font=TITLE_FONT, 
                        command=lambda: close_gui(state, widget))
    button_exit_window = MY_CANVAS.create_window(962, 495, anchor = 'nw',
                                                window=widget.button_exit)

#============================ Updating Widgets: ==============================#
def relay_update(state: GUIState, widget: GUIWidgets) -> None:
    """ Updates GUI text that states which relay is currently open/being tested 
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """
    # update text in GUI
    MY_CANVAS.delete(widget.selected_relay_text)
    if widget.button_start['state']==tk.NORMAL:
        widget.selected_relay_text = MY_CANVAS.create_text(50, 550, text=f"Relay selected is off", 
                                                font=REGULAR_FONT, anchor = 'nw')
    else:
        widget.selected_relay_text = MY_CANVAS.create_text(50, 550, text=f"Relay selected is {state.relay_open}", 
                                                font=REGULAR_FONT, anchor = 'nw')
    
    WIN.after(100, lambda: relay_update(state, widget))

def time_update(state: GUIState, widget: GUIWidgets) -> None:
    """ Updates the 'Run Percent Completed: ' text in the GUI based on how much 
    time has passed 
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """
    # calculate run progress
    if widget.button_start['state']==tk.NORMAL:
        state.start_time = 0.0
    elif widget.button_start['state']==tk.DISABLED and state.selected_run=="AUTOMATED":
        state.elapsed = (time.time() - state.start_time)*100/(16*state.delay)

    # update text in GUI
    MY_CANVAS.delete(widget.completion_text)
    widget.completion_text = MY_CANVAS.create_text(50, 495, 
                                text="Run Percent Complete: " + f"{state.elapsed:.0f}"+"%", 
                                font=REGULAR_FONT, anchor = 'nw') 

    WIN.after(100, lambda: time_update(state, widget))

def sensor_status_update(state: GUIState, widget: GUIWidgets) -> None:
    """ Updates GUI sensor status label based on incoming sensor data
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """ 
    # Sensor status
    MY_CANVAS.delete(widget.sensor_status_window)
    sensor_status = Label(WIN, text=state.sensor_status_text, font=REGULAR_FONT, 
                            bg=state.sensor_text_bd, anchor='nw')
    widget.sensor_status_window = MY_CANVAS.create_window(700, 55, anchor = 'nw', 
                                                    window=sensor_status)

    WIN.after(100, lambda: sensor_status_update(state, widget))

#================================= Close GUI =================================#
def close_gui(state: GUIWidgets, widget: GUIWidgets) -> None:
    """ Turns LED0 off and closes GUI
    
    parameters:
        state: GUIState class
        widget: GUIWidgets class
    """
    # checks if a test is running before closing the GUI
    if widget.button_start['state']==tk.NORMAL:
        default_state(state, widget)
        BOARD.digital[PINLIST[0]].write(1)
        print("Closing GUI")
        sys.exit(0)
    else:
        print("Must stop test before closing GUI")

#=================================== Main ====================================#
def main() -> None:
    """ The main function that is called when the Python script is ran """
    state = GUIState()
    widgets = GUIWidgets()

    # configure relays
    default_state(state, widgets)

    # initialize/setup window
    window_inti(BACKGROUND_IMG)
    setup_window(state, widgets)

    # create log files
    with open(f'./Relay_Logs/relay-{DATE}.csv', 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=RELAY_FIELDNAMES)
        writer.writeheader()
    
    with open(f'./Sensor_Logs/sensor-{DATE}.csv', 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=SENSOR_FIELDNAMES)
        writer.writeheader()

    # set up analog read for differential pressure sensor
    BOARD.analog[SENSOR_PIN].enable_reporting()
    BOARD.analog[SENSOR_PIN].register_callback(lambda data: format_sensor_data(data, state))
    BOARD.samplingOn(sample_interval=SAMPLING_RATE)
    
    # update relay, run status, and sensor status
    relay_update(state, widgets)
    time_update(state, widgets)
    sensor_status_update(state, widgets)
    
    # run main window loop
    WIN.state('normal')
    WIN.after(100, relay_update(state, widgets))
    WIN.after(100,time_update(state, widgets))
    WIN.after(100, sensor_status_update(state, widgets))
    WIN.mainloop()

if __name__ == '__main__':
  main()
  
