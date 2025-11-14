#Notes to self:
#This is the Python version used to build this code in Visual Studio Code:
#3.13.3 (tags/v3.13.3:6280bb5, Apr  8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]; 
#Relay logic: set to be 0/LOW to turn on, and 1/HIGH to turn off

#Import
import sys
import threading
from pyfirmata2 import ArduinoMega 
import tkinter as tk
from tkinter import * 
import time
from time import sleep
from datetime import datetime

#============================== Global Variables =============================#
# test variables
PinList     = []
Relay_Names = []
run_test    = False
delay       = 0.0
relay_open  = "Off"
start_time  = 0.0
elapsed     = 0.0

# tkinter variables
win                     = tk.Tk()
my_canvas               = Canvas()
button_start            = Button()
button_manual           = Button()
manual_options          = list()
selected_manual_option  = StringVar()
relay_time              = Entry()
selected_relay_text     = Canvas()
completion_text         = Canvas()

#================================= Constants =================================#
BOARD         = ArduinoMega('/dev/ttyACM0') 
TITLE_FONT    = ('Arial', 40, 'bold')
INPUT_FONT    = ('Arial', 50)
REGULAR_FONT  = ('Arial', 30)
STOP_FONT     = ('Arial', 40, 'bold')

#================================ Functions ==================================#
def set_relay_names():
  """ Define the pins as well as the name of the relays so that their indexing 
  will match up. Pin 26 is the first Relay (which I define to behave 
  differently from the rest), Pin 41 is the final Relay. """
  global PinList
  global Relay_Names

  # set pin list
  PinList = list(reversed(range(26,42)))

  # set relay names "Relay 1, etc."
  Relay_Names = list(range(1,len(PinList)+1))
  for i in range(0,(len(Relay_Names))):
      Relay_Names[i] = ("Relay " + str(Relay_Names[i]))

def default_state():
  """ Sets the default state. Turn everyone off but the first relay, and set 
  the initial logic for some global variables. """  
  global my_canvas 
  global run_test
  global relay_open
  global completion_text
  global selected_relay_text
  global elapsed

  # turn all relays off
  for i in range(26,42):
      BOARD.digital[i].write(1)
  
  # keep the first relay on
  BOARD.digital[PinList[0]].write(1)

  run_test = False
  relay_open = "Off"
  elapsed = 0.0

  # update completion and LED selected text
  completion_text = my_canvas.create_text(50, 495, 
                            text="Run Percent Complete: " + f"{elapsed:.0f}" + "%", 
                            font=REGULAR_FONT, anchor = 'nw')
  selected_relay_text = my_canvas.create_text(50, 550, text="LED select is " + str(relay_open), 
                                            font=REGULAR_FONT, anchor = 'nw')

#=========================== Automated Run Code: =============================#
def button_stop_command():
  """ If the STOP button is pressed then terminate the loop for the automated 
  code, and put all relays in their default state. For ease of use, this stop 
  button will work for both automated and manual states. """
  global run_test
  global button_start
  global button_manual
  global relay_open

  # reset GUI settings
  run_test = False
  relay_open = "Off"
  button_start['state'] = tk.NORMAL
  button_manual['state'] = tk.NORMAL

  # set relays to default state
  my_canvas.delete(completion_text)
  my_canvas.delete(selected_relay_text)
  default_state()

def button_start_command():
  """ Runs the automated test when the AUTOMATED START button is pressed. """
  global run_test
  global delay
  global relay_time
  global relay_open
  global start_time
  global button_start
  global button_manual

  # get the delay and start time
  delay = float(relay_time.get())
  start_time = time.time()

  # if transitioning from manual to automated code, intial to default state
  my_canvas.delete(completion_text)
  my_canvas.delete(selected_relay_text)
  default_state()
  run_test = True
  current_relay = 1
  
  while current_relay <= (len(PinList)-1) and run_test:
    # Disable start buttons once this loop starts so nothing gets pressed twice
    # and open multiple samplers
    button_start['state'] = tk.DISABLED 
    button_manual['state'] = tk.DISABLED

    # open one relay, wait for delay amount of time, then close relay
    relay_open = Relay_Names[current_relay]
    BOARD.digital[PinList[current_relay]].write(0)
    BOARD.digital[PinList[0]].write(0)
    time.sleep(delay)
    current_relay += 1
    BOARD.digital[PinList[current_relay-1]].write(1)

    # if all relays have been tested, turn all relays expect the first
    # one off
    if current_relay == (len(PinList)):
      my_canvas.delete(completion_text)
      my_canvas.delete(selected_relay_text)
      default_state()

  # Re-enable buttons once test is done
  button_start['state'] = tk.NORMAL
  button_manual['state'] = tk.NORMAL

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
  global my_canvas
  global completion_text
  global selected_relay_text

  # set default state at the beginning of this function
  my_canvas.delete(completion_text)
  my_canvas.delete(selected_relay_text)
  default_state()

  # get which relay was selected
  selected_relay = str(selected_manual_option.get()) 

  # If off is selected, return to default state
  if selected_relay == "Off": 
    my_canvas.delete(selected_relay_text)
    default_state()

  # If relay selected isn't off, open that relay.
  else: 
    position = []
    for i in range(len(manual_options)):
      if manual_options[i] == selected_relay:
        position.append(i)
        int_result = int(''.join(map(str, position)))
        BOARD.digital[PinList[int_result]].write(0)
        BOARD.digital[PinList[0]].write(0)
    relay_open = selected_relay

#================================= Widgets: ==================================#
def window_inti():
  """ Initializes the GUI window and sets the GUI background."""
  global my_canvas
  global win

  #Initialize the GUI window "win"
  win.title("Relay Control GUI")
  win.minsize(1280,660)
  time.sleep(0.5)

  # set up background image
  background = tk.PhotoImage(file="./birchbg.png")
  my_canvas = Canvas(win, width = 1280, height= 660)
  my_canvas.pack(fill = "both", expand=TRUE)
  my_canvas.create_image(0,0, image = background, anchor = 'nw')

def setup_window():
  """ Sets up all the buttons and text within the GUI """
  global relay_time
  global manual_options
  global selected_manual_option
  global button_start
  global button_manual

  #================= Left Side =================#
  #Manual Drop Down Menu:
  manual_options  = list(Relay_Names)
  manual_options[0] = "Off"
  selected_manual_option = tk.StringVar(win)
  selected_manual_option.set(manual_options[0]) # default value

  # Label Manual Select
  my_canvas.create_text(50, 80, text="Manual Select", font=TITLE_FONT, 
                        anchor = 'nw')

  # Menu Manual Select
  manual_selection = OptionMenu(win, selected_manual_option, *manual_options)
  button_manual_selection = my_canvas.create_window(120,160, anchor = 'nw', 
                                                    window=manual_selection)
  manual_selection.config(font=REGULAR_FONT, bg = 'white')
  menu = win.nametowidget(manual_selection.menuname) 
  menu.config(font=REGULAR_FONT, bg = 'white')

  # Label Automated Run
  my_canvas.create_text(50, 300, text="Automated Run:", font=TITLE_FONT, 
                        anchor = 'nw')

  # Entry Relay Time
  my_canvas.create_text(50,380, text="Sequence Time (sec):", font=REGULAR_FONT, 
                        anchor = 'nw')
  relay_time = Entry(win, bd=6, width=3, font=INPUT_FONT)
  relay_time_window = my_canvas.create_window(450,360, anchor = 'nw', 
                                              window=relay_time)

  #================= Right Side ================#
  # Button Manual Start
  button_manual = Button(win, text="Manual Start", font=TITLE_FONT, 
                         command=manual_start)
  button_manual_window = my_canvas.create_window(638,165, anchor = 'nw', 
                                                 window=button_manual)
  
  # Button Automated Start
  button_start = Button(win, text="Automated Start", font=TITLE_FONT, 
                        command=button_starter)
  button_start_window = my_canvas.create_window(638,330, anchor = 'nw', 
                                                window=button_start) 
  
  # Button Stop
  # bg = "#fff494"
  button_stop = Button(win, text="STOP", font=TITLE_FONT, fg = "red", 
                       relief = "solid", command = button_stop_command) 
  button_stop_window = my_canvas.create_window(638,495, anchor = 'nw', 
                                               window=button_stop)
  
  # Button End
  button_end = Button(win, text="EXIT", font=TITLE_FONT, 
                      command = close_gui)
  button_end_window = my_canvas.create_window(900, 495, anchor = 'nw',
                                              window=button_end)

#============================ Updating Widgets: ==============================#
def update():
  """ Updates GUI text that states which relay is currently open/being tested """
  global win
  global selected_relay_text
  global relay_open

  # update text in GUI
  my_canvas.delete(selected_relay_text)
  selected_relay_text = my_canvas.create_text(50, 550, text="Relay selected is " + str(relay_open), 
                                              font=REGULAR_FONT, anchor = 'nw')
  win.after(100, update)

def timeupdate():
  """ Updates the 'Run Percent Completed: ' text in the GUI based on how much 
  time has passed """
  global delay 
  global start_time
  global my_canvas
  global completion_text
  global elapsed
  global button_start

  # calculate run progress
  if button_start['state']==tk.NORMAL:
    start_time = 0.0
  elif button_start['state']==tk.DISABLED:
    elapsed = (time.time() - start_time)*100/(16*delay)

  # update text in GUI
  my_canvas.delete(completion_text)
  completion_text = my_canvas.create_text(50, 495, 
                            text="Run Percent Complete: " + f"{elapsed:.0f}" + "%", 
                            font=REGULAR_FONT, anchor = 'nw') 

  win.after(100,timeupdate)

#================================= Close GUI =================================#
def close_gui():
  """Turns LED0 off and closes GUI"""
  global button_start
  global button_manual
  
  # checks if a test is running before closing the GUI
  if button_start['state']==tk.NORMAL:
    default_state()
    BOARD.digital[PinList[0]].write(1)
    print("Closing GUI")
    sys.exit(0)
  else:
    print("Must stop test before closing GUI")

#=================================== Main ====================================#
def main():
  """ The main function that is called when the Python script is ran """
  # configure LEDs
  set_relay_names()
  default_state()

  # initialize/setup window
  window_inti()
  setup_window()

  # update relay and run status
  update()
  timeupdate()
  
  win.state('normal')
  win.mainloop()

if __name__ == '__main__':
  main()
