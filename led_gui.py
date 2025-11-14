""" This python scipt is modified from "relay Control GUI May 6final.py" and is
used to test is the Raspberry Pi can launch the GUI to control 16 LEDs.
"""

#Import
from pyfirmata2 import ArduinoMega 
import tkinter as tk
from tkinter import * 
import time
from time import sleep
from datetime import datetime
import sys
import threading

#============================== Global Variables =============================#
# test variables
PinList     = []                         
led_names   = []              
run_test    = False
delay       = 0.0
led_on      = "Off"
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
selected_led_text       = Canvas()
completion_text         = Canvas()

#================================= Constants =================================#
BOARD         = ArduinoMega('/dev/ttyACM0') 
TITLE_FONT    = ('Arial', 40, 'bold')
INPUT_FONT    = ('Arial', 50)
REGULAR_FONT  = ('Arial', 30)
STOP_FONT     = ('Arial', 40, 'bold')

#================================ Functions ==================================#
def set_led_names():
  """ Define the pins as well as the name of the relays so that their indexing 
  will match up. Pin 26 is the first Relay (which I define to behave differently 
  from the rest), Pin 41 is the final Relay.

  parameters: None
  returns: None
  """
  global PinList
  global led_names

  # set pin list
  PinList = [23, 24, 27, 28, 31, 32, 35, 36, 39, 40, 43, 44, 47, 48, 51, 52]

  # set led names "LED 1, etc."
  led_names = list(range(1,len(PinList)+1))
  for i in range(0,(len(led_names))):
      led_names[i] = ("LED " + str(led_names[i]))

def default_state():
  """ Sets the default state. Turn everyone off but the first relay, and set 
  the initial logic for some global variables.

  parameters: None
  returns: None
  """ 
  global my_canvas 
  global run_test
  global led_on
  global completion_text
  global selected_led_text
  global elapsed

  # turn all relays off
  for i in range(16):
      BOARD.digital[PinList[i]].write(0)
  
  # keep the first relay on
  BOARD.digital[PinList[0]].write(1)

  run_test = False
  led_on = "Off"
  elapsed = 0.0

  # update completion and LED selected text
  completion_text = my_canvas.create_text(50, 495, 
                            text="Run Percent Complete: " + f"{elapsed:.0f}" + "%", 
                            font=REGULAR_FONT, anchor = 'nw')
  selected_led_text = my_canvas.create_text(50, 550, text="LED select is " + str(led_on), 
                                            font=REGULAR_FONT, anchor = 'nw')

#=========================== Automated Run Code: =============================#
def button_stop_command():
  """ If the STOP button is pressed then terminate the loop for the automated 
  code, and put all relays in their default state. For ease of use, this stop 
  button will work for both automated and manual states.

  parameters: None
  returns: None
  """
  global run_test
  global button_start
  global button_manual
  global led_on

  # terminate loop?
  run_test = False
  led_on = "Off"
  button_start['state'] = tk.NORMAL
  button_manual['state'] = tk.NORMAL

  # set relays to default state
  my_canvas.delete(completion_text)
  my_canvas.delete(selected_led_text)
  default_state()

def button_start_command():
  """ Runs the automated test when the start button is pressed.

  parameters: None
  returns: None
  """
  global run_test
  global delay
  global relay_time
  global led_on
  global start_time
  global button_start
  global button_manual

  delay = float(relay_time.get())
  start_time = time.time()

  # if transitioning from manual to automated code, intial to default state
  my_canvas.delete(completion_text)
  my_canvas.delete(selected_led_text)
  default_state()
  run_test = True
  current_led = 1
  
  while current_led <= (len(PinList)-1) and run_test:
    # Disable start buttons once this loop starts so nothing gets 
    # pressed twice and open multiple samplers
    button_start['state'] = tk.DISABLED 
    button_manual['state'] = tk.DISABLED

    # turn on one LED, wait for delay amount of time, then turn off LED
    led_on = led_names[current_led]
    BOARD.digital[PinList[current_led]].write(1)
    BOARD.digital[PinList[0]].write(1)
    time.sleep(delay)
    current_led += 1
    BOARD.digital[PinList[current_led-1]].write(0)

    # if all LEDs have been tested, return to default state
    if current_led == (len(PinList)):
      my_canvas.delete(completion_text)
      my_canvas.delete(selected_led_text)
      default_state()

  # Re-enable buttons once test is done
  button_start['state'] = tk.NORMAL
  button_manual['state'] = tk.NORMAL

def button_starter():
  t = threading.Thread(target=button_start_command)
  t.start()


#============================ Manual Run Code: ===============================#
def manual_start():
  global led_on
  global manual_options
  global selected_manual_option
  global my_canvas
  global completion_text
  global selected_led_text
  
  #set default state at the beginning of this function
  my_canvas.delete(completion_text)
  my_canvas.delete(selected_led_text)
  default_state()

  #select an LED, call variable float
  selected_relay = str(selected_manual_option.get()) 

  # If off is selected, return to default state 
  if selected_relay == "Off": 
    my_canvas.delete(selected_led_text)
    default_state()

  # If LED is selected and it's not the 'off' option, turn it on.
  else: 
    position = []
    for i in range(len(manual_options)):
      if manual_options[i] == selected_relay:
        position.append(i)
        int_result = int(''.join(map(str, position)))
        BOARD.digital[PinList[int_result]].write(1)
        BOARD.digital[PinList[0]].write(1)
    led_on = selected_relay

#================================= Widgets: ==================================#
def window_inti():
  """ Initializes the GUI window and sets the GUI background."""
  global my_canvas
  global win

  #Initialize the GUI window "win"
  win.title("LED Control GUI")
  win.minsize(1280,660)
  #win.attributes('-fullscreen', True) #delete this if I want.
  time.sleep(0.5)

  background = tk.PhotoImage(file="./birchbg.png")
  my_canvas = Canvas(win, width = 1280, height= 660)
  my_canvas.pack(fill = "both", expand=TRUE)
  my_canvas.create_image(0,0, image = background, anchor = 'nw')

def setup_window():
  global relay_time
  global manual_options
  global selected_manual_option
  global button_start
  global button_manual

  #================================ Left Side ================================#
  #Manual Drop Down Menu:
  manual_options  = list(led_names)
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

  #=============================== Right Side ================================#
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
  global win
  global selected_led_text

  my_canvas.delete(selected_led_text)
  selected_led_text = my_canvas.create_text(50, 550, text="LED select is " + str(led_on), 
                            font=REGULAR_FONT, anchor = 'nw')
  win.after(100, update)

def timeupdate():
  global delay 
  global start_time
  global my_canvas
  global completion_text
  global elapsed
  global button_start

  if button_start['state']==tk.NORMAL:
    start_time = 0.0
  elif button_start['state']==tk.DISABLED:
    elapsed = (time.time() - start_time)*100/(16*delay)

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
  
  if button_start['state']==tk.NORMAL:
    default_state()
    BOARD.digital[PinList[0]].write(0)
    print("Closing GUI")
    sys.exit(0)
  else:
    print("Must stop test before closing GUI")

#=================================== Main ====================================#
def main():
  # configure LEDs
  set_led_names()
  default_state()

  # initialize/setup window
  window_inti()
  setup_window()

  # update time
  update()
  timeupdate()
  
  win.state('normal')
  win.mainloop()

if __name__ == '__main__':
  main()
