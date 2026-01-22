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

#================================= Constants =================================#
BOARD             = ArduinoMega('COM5') 
WIN               = tk.Tk()
MY_CANVAS         = tk.Canvas(WIN, width = 1280, height= 660)
BACKGROUND_IMG    = tk.PhotoImage(file="./birchbg.png")
TITLE_FONT        = ('Arial', 40, 'bold')
INPUT_FONT        = ('Arial', 50)
REGULAR_FONT      = ('Arial', 30)
STOP_FONT         = ('Arial', 40, 'bold')
PINLIST           = [41, 40, 39, 38, 37, 36, 35, 34, 
                    33, 32, 31, 30, 29, 28, 27, 26]
RELAY_NAMES       = ["Relay 1", "Relay 2", "Relay 3", "Relay 4", "Relay 5",
                    "Relay 6", "Relay 7", "Relay 8", "Relay 9", "Relay 10",
                    "Relay 11", "Relay 12", "Relay 13", "Relay 14", "Relay 15",
                    "Relay 16"]
MANUAL_OPTIONS    = ["Off"] + RELAY_NAMES[1:]
SENSOR_PIN        = 0
SAMPLING_RATE     = 1000  # in milliseconds
RELAY_FIELDNAMES  = ['RUN', 'DELAY (s)', 'RELAY', 'START TIME', 'END TIME', 
                     'SENSOR']
SENSOR_FIELDNAMES = ['RUN', 'RELAY', 'TIME', 'SENSOR VALUE', 'STATUS']
DATE              = datetime.date(datetime.today())

#============================== Global Variables =============================#
# test variables
delay             = 0.0     # Delay time between each relay for automated run
relay_open        = "Off"   # Relay that is currently open ("Off" means default 
                            # state)
start_time        = 0.0     # Time that automated/manual run was started
local_start_time  = 0.0     # Time that automated/manual run was started (used 
                            # for logging)
elapsed           = 0.0     # Percentage of run time completed
selected_run      = ""      # Which run (automated or manual) is currently being 
                            # ran (used for logging)
sensor_val        = ""
sensor_value_text = ""
sensor_status_text= "IDLE"
sensor_text_bd    = "#6B6B6E"


# tkinter variables
button_start            = Button()
button_manual           = Button()
selected_manual_option  = StringVar()
relay_time              = Entry()
selected_relay_text     = Canvas()
completion_text         = Canvas()
sensor_status_window    = Canvas()

#================================ Functions ==================================#
def default_state() -> None:
  """ Sets the default state. Turn everyone off but the first relay, and set 
  the initial logic for some global variables. """  
  global relay_open
  global start_time
  global elapsed
  global selected_run
  global selected_relay_text
  global completion_text

  # turn all relays off
  for i in range(26,42):
      BOARD.digital[i].write(1)
  
  # keep the first relay on
  BOARD.digital[PINLIST[0]].write(1)

  # reset completion and selected relay
  relay_open = "Off"
  elapsed = 0.0
  completion_text = MY_CANVAS.create_text(50, 495, 
                            text="Run Percent Complete: 0%", font=REGULAR_FONT, 
                            anchor = 'nw')
  selected_relay_text = MY_CANVAS.create_text(50, 550, text="LED select is Off", 
                                            font=REGULAR_FONT, anchor = 'nw')

  # reset start and end time and selecte run
  start_time = 0.0
  selected_run = ""

def log_relay(run: str, delay, relay: str, start, end) -> None:
  """ Logs data to a .csv file with the name of the file being the date it was
  created (ex. 11-14-2025.csv). Log files are created with the "Logs" folder. 
  The log data include the type of run (automated or manual), the delay time, 
  which relay is open, when the run started, when the run was 
  completed/ended, and the absolute value from the sensor """
  global sensor_val
  global sensor_status_text

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
    sensor = f'{sensor_val} {sensor_status_text}'

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
def button_stop_command() -> None:
  """ If the STOP button is pressed then terminate the loop for the automated 
  code, and put all relays in their default state. For ease of use, this stop 
  button will work for both automated and manual states. """
  global button_start
  global button_manual
  global delay
  global relay_open
  global local_start_time
  global selected_run
  global selected_relay

  # get end time
  end_time = time.localtime()

  # set data based on run
  if selected_run == "AUTOMATED":
    selected_relay = relay_open
  elif selected_run == "MANUAL":
    delay = None

  # log data
  log_relay(selected_run, delay, selected_relay, local_start_time, end_time)
  log_relay(" ", " ", " ", local_start_time, end_time)

  # reset GUI settings
  relay_open = "Off"
  button_start['state'] = tk.NORMAL
  button_manual['state'] = tk.NORMAL
  button_exit['state'] = tk.NORMAL

  # set relays to default state
  MY_CANVAS.delete(completion_text)
  MY_CANVAS.delete(selected_relay_text)
  default_state()

def button_start_command():
  """ Runs the automated test when the AUTOMATED START button is pressed. """
  global delay
  global relay_time
  global relay_open
  global start_time
  global local_start_time
  global button_start
  global button_manual
  global button_exit
  global selected_run
  
  # if transitioning from manual to automated code, intial to default state
  if selected_run == "MANUAL":
    MY_CANVAS.delete(completion_text)
    MY_CANVAS.delete(selected_relay_text)
    default_state()
  
  # get the delay and start time
  delay = float(relay_time.get())
  start_time = time.time()
  local_start_time = time.localtime()
  selected_run = "AUTOMATED"

  # prepare to start test
  current_relay = 1

  # automated run loop
  while current_relay <= (len(PINLIST)-1):
    # Disable start buttons once this loop starts so nothing gets pressed twice
    # and open multiple samplers
    button_start['state'] = tk.DISABLED 
    button_manual['state'] = tk.DISABLED
    button_exit['state'] = tk.DISABLED

    # open one relay and measure differential pressure 
    relay_open = RELAY_NAMES[current_relay]
    BOARD.digital[PINLIST[current_relay]].write(0)
    BOARD.digital[PINLIST[0]].write(0)
    relay_start_time = time.localtime()

    # wait for delay amount of time, then close relay
    time.sleep(delay)
    current_relay += 1
    BOARD.digital[PINLIST[current_relay-1]].write(1)
    relay_end_time = time.localtime()

    # log start/end time for relay
    log_relay(selected_run, delay, relay_open, relay_start_time, relay_end_time)

  # get end time, turn off sensor sampling, and log data
  end_time = time.localtime()
  log_relay(selected_run, delay, 'Complete automated run', local_start_time, 
            end_time)
  log_relay(" ", " ", " ", local_start_time, end_time)

  # return to default state once run is complete
  MY_CANVAS.delete(completion_text)
  MY_CANVAS.delete(selected_relay_text)
  default_state()

  # Re-enable buttons once test is done
  button_start['state'] = tk.NORMAL
  button_manual['state'] = tk.NORMAL
  button_exit['state'] = tk.NORMAL

def button_starter():
  t = threading.Thread(target=button_start_command)
  t.start()

def manual_start():
  """ Runs the manual test with the selected relay when the MANUAL START button
  is pressed """
  global relay_open
  global selected_manual_option
  global button_start
  global button_manual
  global button_exit
  global completion_text
  global selected_relay_text
  global selected_relay
  global local_start_time
  global selected_run

  # set default state at the beginning of this function
  MY_CANVAS.delete(completion_text)
  MY_CANVAS.delete(selected_relay_text)
  default_state()

  # get which relay was selected
  selected_relay = str(selected_manual_option.get()) 

  # set start time and selected run
  local_start_time = time.localtime()
  selected_run = "MANUAL"

  # If off is selected, return to default state
  if selected_relay == "Off": 
    MY_CANVAS.delete(selected_relay_text)
    default_state()

  # If relay selected isn't off, open that relay.
  else: 
    button_start['state'] = tk.DISABLED 
    button_manual['state'] = tk.DISABLED
    button_exit['state'] = tk.DISABLED
    position = []
    for i in range(len(MANUAL_OPTIONS)):
      if MANUAL_OPTIONS[i] == selected_relay:
        position.append(i)
        int_result = int(''.join(map(str, position)))
        BOARD.digital[PINLIST[int_result]].write(0)
        BOARD.digital[PINLIST[0]].write(0)
    relay_open = selected_relay

#=============================== Sensor Code: ================================#
def format_sensor_data(data):
  global selected_run
  global relay_open
  global sensor_val
  global sensor_status_text
  global sensor_text_bd

  # change data into absolute value relative to 0.4976 (the ambient value)
  sensor_val = round(data - 0.4976, 4)
  
  # update sensor status based on measurement
  # # TO DO: test range for 9.8 - 10.3L/min
  if sensor_val > 0.152 and sensor_val < 0.187: # normal operations
    sensor_status_text = "OPEN"
    sensor_text_bd = "#00cc1f"
  elif sensor_val > -0.009 and sensor_val < 0.002:  # ambient
    sensor_status_text = "AMBIENT"
    sensor_text_bd = "#6B6B6E"
  elif sensor_val < 0.152:  # leak
    sensor_status_text = "LEAK"
    sensor_text_bd = "#cc0000"
  else:   # pressure is not within desired range (either greater or less than expected)
    sensor_status_text = "WARNING"
    sensor_text_bd = "#ffea00"

  # set time of measurement
  measurement_time = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime())

  # format data
  data = {'RUN': f'{selected_run}', 
          'RELAY': f'{relay_open}', 
          'TIME': f'{measurement_time}',
          'SENSOR VALUE': f'{sensor_val}',
          'STATUS': F'{sensor_status_text}'}

  # write to sensor log file
  with open(f'./Sensor_Logs/sensor-{DATE}.csv', 'a', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=SENSOR_FIELDNAMES)
    writer.writerow(data)

  return sensor_val

def button_sensor_command():
  """ Displays sensor value """
  global sensor_value_text
  global sensor_val

  raw_value = round(sensor_val+0.4976, 4)
  MY_CANVAS.delete(sensor_value_text)
  sensor_value_text = MY_CANVAS.create_text(370, 350, text=raw_value, font=TITLE_FONT, 
                        anchor = 'nw')

#================================= Widgets: ==================================#
def window_inti(background: PhotoImage) -> None:
  """ Initializes the GUI window and sets the GUI background."""

  #Initialize the GUI window "win"
  WIN.title("Relay Control GUI")
  WIN.minsize(1280,660)

  # create canvas widget
  MY_CANVAS.pack(fill = "both", expand=TRUE)

  # set up background image
  MY_CANVAS.create_image(0, 0, image = background, anchor = 'nw')

def setup_window():
  """ Sets up all the buttons and text within the GUI """
  global relay_time
  global selected_manual_option
  global sensor_value_text
  global sensor_val
  global button_start
  global button_manual
  global button_exit
  global sensor_status_window

  #================= Left Side =================#
  #Manual Drop Down Menu:
  selected_manual_option = tk.StringVar(WIN)
  selected_manual_option.set(MANUAL_OPTIONS[0]) # default value

  # Label Manual Select
  MY_CANVAS.create_text(50, 55, text="Manual Select:", font=TITLE_FONT, 
                        anchor = 'nw')

  # Menu Manual Select
  manual_selection = OptionMenu(WIN, selected_manual_option, *MANUAL_OPTIONS)
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
  relay_time = Entry(WIN, bd=6, width=3, font=REGULAR_FONT)
  relay_time_window = MY_CANVAS.create_window(450,240, anchor = 'nw', 
                                              window=relay_time)
  
  # Button Check Sensor
  button_sensor = Button(WIN, text="Check Sensor", font=REGULAR_FONT, 
                         command=button_sensor_command)
  button_sensor_window = MY_CANVAS.create_window(50,340, anchor='nw', 
                                                 window=button_sensor)
  sensor_value_text = MY_CANVAS.create_text(450, 340, text=sensor_val, font=TITLE_FONT, 
                        anchor = 'nw')
  
  #================= Right Side ================#
  # Sensor status
  sensor_status = Label(WIN, text=sensor_status_text, font=REGULAR_FONT, 
                        bg=sensor_text_bd, anchor='nw')
  sensor_status_window = MY_CANVAS.create_window(700,55, anchor = 'nw', window=sensor_status)

  # Button Manual Start
  button_manual = Button(WIN, text="Manual Start", font=TITLE_FONT, 
                         command=manual_start)
  button_manual_window = MY_CANVAS.create_window(700,165, anchor = 'nw', 
                                                 window=button_manual)
  
  # Button Automated Start
  button_start = Button(WIN, text="Automated Start", font=TITLE_FONT, 
                        command=button_starter)
  button_start_window = MY_CANVAS.create_window(700,330, anchor = 'nw', 
                                                window=button_start) 
  
  # Button Stop
  # bg = "#fff494"
  button_stop = Button(WIN, text="STOP", font=TITLE_FONT, fg = "red", 
                       relief = "solid", command = button_stop_command) 
  button_stop_window = MY_CANVAS.create_window(700,495, anchor = 'nw', 
                                               window=button_stop)
  
  # Button End
  button_exit = Button(WIN, text="EXIT", font=TITLE_FONT, 
                      command = close_gui)
  button_exit_window = MY_CANVAS.create_window(962, 495, anchor = 'nw',
                                              window=button_exit)

#============================ Updating Widgets: ==============================#
def relay_update():
  """ Updates GUI text that states which relay is currently open/being tested """
  global selected_relay_text
  global relay_open

  # update text in GUI
  MY_CANVAS.delete(selected_relay_text)
  selected_relay_text = MY_CANVAS.create_text(50, 550, text="Relay selected is " + str(relay_open), 
                                              font=REGULAR_FONT, anchor = 'nw')
  WIN.after(100, relay_update)

def time_update():
  """ Updates the 'Run Percent Completed: ' text in the GUI based on how much 
  time has passed """
  global delay 
  global start_time
  global completion_text
  global elapsed
  global button_start
  global selected_run

  # calculate run progress
  if button_start['state']==tk.NORMAL:
    start_time = 0.0
  elif button_start['state']==tk.DISABLED and selected_run=="AUTOMATED":
    elapsed = (time.time() - start_time)*100/(16*delay)

  # update text in GUI
  MY_CANVAS.delete(completion_text)
  completion_text = MY_CANVAS.create_text(50, 495, 
                            text="Run Percent Complete: " + f"{elapsed:.0f}" + "%", 
                            font=REGULAR_FONT, anchor = 'nw') 

  WIN.after(100,time_update)

def sensor_status_update():
  global sensor_status_text
  global sensor_text_bd
  global sensor_status_window

  # Sensor status
  MY_CANVAS.delete(sensor_status_window)
  sensor_status = Label(WIN, text=sensor_status_text, font=REGULAR_FONT, bg=sensor_text_bd, anchor='nw')
  sensor_status_window = MY_CANVAS.create_window(700, 55, anchor = 'nw', window=sensor_status)

  WIN.after(100, sensor_status_update)

#================================= Close GUI =================================#
def close_gui():
  """Turns LED0 off and closes GUI"""
  global button_start
  global button_manual
  
  # checks if a test is running before closing the GUI
  if button_start['state']==tk.NORMAL:
    default_state()
    BOARD.digital[PINLIST[0]].write(1)
    print("Closing GUI")
    sys.exit(0)
  else:
    print("Must stop test before closing GUI")

#=================================== Main ====================================#
def main():
  """ The main function that is called when the Python script is ran """
  # configure relays
  default_state()

  # initialize/setup window
  window_inti(BACKGROUND_IMG)
  setup_window()

  # create log files
  with open(f'./Relay_Logs/relay-{DATE}.csv', 'a', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=RELAY_FIELDNAMES)
    writer.writeheader()
  
  with open(f'./Sensor_Logs/sensor-{DATE}.csv', 'a', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=SENSOR_FIELDNAMES)
    writer.writeheader()

  # set up analog read for differential pressure sensor
  BOARD.analog[SENSOR_PIN].enable_reporting()
  BOARD.analog[SENSOR_PIN].register_callback(format_sensor_data)
  BOARD.samplingOn(sample_interval=SAMPLING_RATE)
  
  # update relay and run status
  relay_update()
  time_update()
  sensor_status_update()
  
  WIN.state('normal')
  WIN.mainloop()

if __name__ == '__main__':
  main()
