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
BOARD         = ArduinoMega('COM5') 
WIN           = tk.Tk()
MY_CANVAS     = tk.Canvas(WIN, width = 1280, height= 660)
TITLE_FONT    = ('Arial', 40, 'bold')
INPUT_FONT    = ('Arial', 50)
REGULAR_FONT  = ('Arial', 30)
STOP_FONT     = ('Arial', 40, 'bold')
PINLIST       = [41, 40, 39, 38, 37, 36, 35, 34, 
                 33, 32, 31, 30, 29, 28, 27, 26]
RELAY_NAMES   = ["Relay 1", "Relay 2", "Relay 3", "Relay 4", "Relay 5",
                 "Relay 6", "Relay 7", "Relay 8", "Relay 9", "Relay 10",
                 "Relay 11", "Relay 12", "Relay 13", "Relay 14", "Relay 15",
                 "Relay 16"]
FIELDNAMES    = ['RUN', 'DELAY', 'RELAY', 'START TIME', 'END TIME']
DATE          = datetime.date(datetime.today())

#============================== Global Variables =============================#
# test variables
run_test          = False   # Indicates if a testing is running or not
delay             = 0.0     # Delay time between each relay for automated run
relay_open        = "Off"   # Relay that is currently open ("Off" means default 
                            # state)
start_time        = 0.0     # Time that automated/manual run was started
local_start_time  = 0.0     # Time that automated/manual run was started (used 
                            # for logging)
end_time          = 0.0     # Time that automated/manual run was completed/stopped
elapsed           = 0.0     # Percentage of run time completed
selected_run      = ""      # Which run (automated or manual) is currently being 
                            # ran (used for logging)

# tkinter variables
background              = tk.PhotoImage(file="./birchbg.png")
button_start            = Button()
button_manual           = Button()
manual_options          = list()
selected_manual_option  = StringVar()
relay_time              = Entry()
selected_relay_text     = Canvas()
completion_text         = Canvas()

#================================ Functions ==================================#
def default_state():
  """ Sets the default state. Turn everyone off but the first relay, and set 
  the initial logic for some global variables. """  
  global run_test
  global relay_open
  global start_time
  global local_start_time
  global end_time
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
  run_test = False
  relay_open = "Off"
  elapsed = 0.0
  completion_text = MY_CANVAS.create_text(50, 495, 
                            text="Run Percent Complete: 0%", font=REGULAR_FONT, 
                            anchor = 'nw')
  selected_relay_text = MY_CANVAS.create_text(50, 550, text="LED select is Off", 
                                            font=REGULAR_FONT, anchor = 'nw')
  
  # reset start and end time and selecte run
  start_time = 0.0
  end_time = 0.0
  selected_run = ""
  
def logging(run: str, delay, relay: str, start, end):
  """ Logs data to a .csv file with the name of the file being the date it was
  created (ex. 11-14-2025.csv). Log files are created with the "Logs" folder. 
  The log data include the type of run (automated or manual), the delay time, 
  which relay is open, when the run started, and when the run was 
  completed/ended """

  # convert timestamps into local time
  if run == " ":
    start = " "
    end = " "
  else:
    start = time.strftime("%H:%M:%S", start)
    end = time.strftime("%H:%M:%S", end)

  # format data
  data = {'RUN': f'{run}', 
          'DELAY': f'{delay}',
          'RELAY': f'{relay}', 
          'START TIME': f'{start}', 
          'END TIME': f'{end}'}

  if run != "":
    with open(f'./Logs/{DATE}.csv', 'a', newline='') as csvfile:
      writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
      writer.writerow(data)

#=========================== Automated Run Code: =============================#
def button_stop_command():
  """ If the STOP button is pressed then terminate the loop for the automated 
  code, and put all relays in their default state. For ease of use, this stop 
  button will work for both automated and manual states. """
  global run_test
  global button_start
  global button_manual
  global delay
  global relay_open
  global local_start_time
  global end_time
  global selected_run
  global selected_relay
  global relay_open

  # get end time
  end_time = time.localtime()

  # set data based on run
  if selected_run == "AUTOMATED":
    selected_relay = relay_open
  elif selected_run == "MANUAL":
    delay = None

  # log data
  logging(selected_run, delay, selected_relay, local_start_time, end_time)
  logging(" ", " ", " ", local_start_time, end_time)

  # reset GUI settings
  run_test = False
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
  global run_test
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
  run_test = True
  current_relay = 1

  # automated run loop
  while current_relay <= (len(PINLIST)-1) and run_test:
    # Disable start buttons once this loop starts so nothing gets pressed twice
    # and open multiple samplers
    button_start['state'] = tk.DISABLED 
    button_manual['state'] = tk.DISABLED
    button_exit['state'] = tk.DISABLED

    # open one relay, wait for delay amount of time, then close relay
    relay_open = RELAY_NAMES[current_relay]
    BOARD.digital[PINLIST[current_relay]].write(0)
    BOARD.digital[PINLIST[0]].write(0)
    relay_start_time = time.localtime()
    time.sleep(delay)
    current_relay += 1
    BOARD.digital[PINLIST[current_relay-1]].write(1)
    relay_end_time = time.localtime()

    # log start/end time for relay
    logging(selected_run, delay, relay_open, relay_start_time, relay_end_time)

  # get end time and log data
  end_time = time.localtime()
  logging(selected_run, delay, 'Complete automated run', local_start_time, end_time)
  logging(" ", " ", " ", local_start_time, end_time)

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

#============================ Manual Run Code: ===============================#
def manual_start():
  """ Runs the manual test with the selected relay when the MANUAL START button
  is pressed """
  global relay_open
  global manual_options
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
    for i in range(len(manual_options)):
      if manual_options[i] == selected_relay:
        position.append(i)
        int_result = int(''.join(map(str, position)))
        BOARD.digital[PINLIST[int_result]].write(0)
        BOARD.digital[PINLIST[0]].write(0)
    relay_open = selected_relay

#================================= Widgets: ==================================#
def window_inti():
  """ Initializes the GUI window and sets the GUI background."""
  global background

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
  global manual_options
  global selected_manual_option
  global button_start
  global button_manual
  global button_exit

  #================= Left Side =================#
  #Manual Drop Down Menu:
  manual_options  = list(RELAY_NAMES)
  manual_options[0] = "Off"
  selected_manual_option = tk.StringVar(WIN)
  selected_manual_option.set(manual_options[0]) # default value

  # Label Manual Select
  MY_CANVAS.create_text(50, 80, text="Manual Select", font=TITLE_FONT, 
                        anchor = 'nw')

  # Menu Manual Select
  manual_selection = OptionMenu(WIN, selected_manual_option, *manual_options)
  button_manual_selection = MY_CANVAS.create_window(120,160, anchor = 'nw', 
                                                    window=manual_selection)
  manual_selection.config(font=REGULAR_FONT, bg = 'white')
  menu = WIN.nametowidget(manual_selection.menuname) 
  menu.config(font=REGULAR_FONT, bg = 'white')

  # Label Automated Run
  MY_CANVAS.create_text(50, 300, text="Automated Run:", font=TITLE_FONT, 
                        anchor = 'nw')

  # Entry Relay Time
  MY_CANVAS.create_text(50,380, text="Sequence Time (sec):", font=REGULAR_FONT, 
                        anchor = 'nw')
  relay_time = Entry(WIN, bd=6, width=3, font=INPUT_FONT)
  relay_time_window = MY_CANVAS.create_window(450,360, anchor = 'nw', 
                                              window=relay_time)

  #================= Right Side ================#
  # Button Manual Start
  button_manual = Button(WIN, text="Manual Start", font=TITLE_FONT, 
                         command=manual_start)
  button_manual_window = MY_CANVAS.create_window(638,165, anchor = 'nw', 
                                                 window=button_manual)
  
  # Button Automated Start
  button_start = Button(WIN, text="Automated Start", font=TITLE_FONT, 
                        command=button_starter)
  button_start_window = MY_CANVAS.create_window(638,330, anchor = 'nw', 
                                                window=button_start) 
  
  # Button Stop
  # bg = "#fff494"
  button_stop = Button(WIN, text="STOP", font=TITLE_FONT, fg = "red", 
                       relief = "solid", command = button_stop_command) 
  button_stop_window = MY_CANVAS.create_window(638,495, anchor = 'nw', 
                                               window=button_stop)
  
  # Button End
  button_exit = Button(WIN, text="EXIT", font=TITLE_FONT, 
                      command = close_gui)
  button_exit_window = MY_CANVAS.create_window(900, 495, anchor = 'nw',
                                              window=button_exit)

#============================ Updating Widgets: ==============================#
def update():
  """ Updates GUI text that states which relay is currently open/being tested """
  global selected_relay_text
  global relay_open

  # update text in GUI
  MY_CANVAS.delete(selected_relay_text)
  selected_relay_text = MY_CANVAS.create_text(50, 550, text="Relay selected is " + str(relay_open), 
                                              font=REGULAR_FONT, anchor = 'nw')
  WIN.after(100, update)

def timeupdate():
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

  WIN.after(100,timeupdate)

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
  window_inti()
  setup_window()

  # create log file
  with open(f'./Logs/{DATE}.csv', 'a', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
    writer.writeheader()

  # update relay and run status
  update()
  timeupdate()
  
  WIN.state('normal')
  WIN.mainloop()

if __name__ == '__main__':
  main()
