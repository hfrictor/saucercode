import datetime
import math
import os
import PIL.Image
import PIL.ImageTk
import pyfireconnect
#import RPi.GPIO as GPIO
#import serial
import sys
import threading
import time
from tkinter import *
import tkinter.font as font
import urllib.request


#*************************************START CONNECTION**************************************

# Open UART serial connection
#ser = serial.Serial("/dev/ttyS0", 115200)  # opens port with baud rate
ser = ""

#**************************************FIREBASE SET UP**************************************

#Check for internet connection
hasInternet = False

def checkInternet():
  internet = True
  try:
    urllib.request.urlopen('https://smart-saucer.firebaseio.com/')
  except:
    internet = False
  return internet

time.sleep(1)
hasInternet = checkInternet()

#Set timezone
os.environ['TZ'] = 'US/Eastern'
time.tzset()

#pyfire set up if internet is connected
if(hasInternet):
  config = {
    "apiKey" : "AIzaSyBq-3aOFMlc-9IcSV-X2ZvrIceH5Uvz-U4",
    "authDomain" : "smart-saucer.firebaseapp.com",
    "databaseURL" : "https://smart-saucer.firebaseio.com/",
    "storageBucket" : "smart-saucer.appspot.com"
  }

  firebase = pyfireconnect.initialize(config)
  db = firebase.database()

  # Set up size and weight amounts to 0
  db.child("Pizza Throughput").child("7").set({"COUNT":0, "WEIGHT":0})
  db.child("Pizza Throughput").child("10").set({"COUNT":0, "WEIGHT":0})
  db.child("Pizza Throughput").child("12").set({"COUNT":0, "WEIGHT":0})
  db.child("Pizza Throughput").child("14").set({"COUNT":0, "WEIGHT":0})

#***********************************VARIABLE DECLARATIONS***********************************

# Color variables for consistency
main_bg = "#FFFFFF" #switched from gray20
button_color = "#CCCDD0" #switched from gray20
donatos_path = "donatos.png" #switched from white
main_fg = "#000000" #switched from FFFFFF

imageOne_path = "donatos.png"
imageTwo_path = "donatos.png"
imageThree_path = "donatos.png"
imageFour_path = "donatos.png"
imageFive_path = "donatos.png"
imageSix_path = "donatos.png"
imageSeven_path = "donatos.png"
imageEight_path = "donatos.png"
imageNine_path = "donatos.png"

# Light, normal, extra sauce speeds
lt = 1.25
med = 1
ext = 0.75

# Size calibrations from file
with open('diagnostics.txt', 'r') as reader:
        calibs = reader.read().splitlines()

global calibration
calibration = {7: int(calibs[4]), 10: int(calibs[5]), 12: int(calibs[6]), 14: int(calibs[7])}

# Motor speed
global s1_speed, s2_speed, s3_speed, s4_speed
global motor1speeds, motor2speeds, motor3speeds, motor4speeds

#************************************************************************************************************************************************************************
# This section includes all the varibales that affect the coverage of the pizza

#Variable for the turn table speed
turn_table_speed = 2500

#Varibale for the turn table time
turn_table_time = 7

#Below are the new vaiables for the individual motor speeds
#Modify this one to change the 7 inch speeds
motor_one_7 = 3500
motor_one_10 = 3500
motor_one_12 = 3500
motor_one_14 = 3400

#Modify this one to change the 10 inch speeds
motor_two_7 = 0
motor_two_10 = 2500
motor_two_12 = 2500
motor_two_14 = 2500

#Modify this one to change the 12 inch speeds
motor_three_7 = 0
motor_three_10 = 0
motor_three_12 = 2900
motor_three_14 = 2500

#Modify this one to change the 14 inch speeds
motor_four_7 = 0
motor_four_10 = 0
motor_four_12 = 0
motor_four_14 = 2500

#*************************************************************************************************************************************************************************

motor1speeds = {7:motor_one_7, 10:motor_one_10, 12:motor_one_12, 14:motor_one_14} # Sauce motor 1 speed
motor2speeds = {7:motor_two_7, 10:motor_two_10, 12:motor_two_12, 14:motor_two_14} # Sauce motor 2 speed
motor3speeds = {7:motor_three_7, 10:motor_three_10, 12:motor_three_12, 14:motor_three_14} # Sauce motor 3 speed
motor4speeds = {7:motor_four_7, 10:motor_four_10, 12:motor_four_12, 14:motor_four_14} # Sauce motor 4 speed

clean_prime_speed = 2500 # Sauce motor speed when cleaning and priming

# Weights for recording data

lt_weights = {7:0.06, 10:0.11, 12:0.18, 14:0.25}
med_weights = {7:0.11, 10:0.25, 12:0.36, 14:0.5}
ext_weights = {7:0.17, 10:0.36, 12:0.54, 14:0.75}

# Size / Steps / Sauce Amount
global size
size = -1 # No default size
global sauce_spin_steps
sauce_spin_steps = 1000
global amount
amount = med #normal amount at start

# Variable for total machine time
global totalTime
totalTime = time.time()

# Variables for emergency stop
global shutdown
shutdown = False
global running
running = False

#*************************************BUTTON FUNCTIONS**************************************

# Function used for size double click
def setSize(button, new_size):
    global size
    size = new_size
    runSaucer(button)

# Function for stop button
def emergencyStop():
    global shutdown
    shutdown = True
   
# Function to destroy two screens instead of just 1
def killTwoScreens(screen1, screen2):
    screen2.destroy()
    screen1.destroy()
    
#************************************SAUCER FUNCTIONS***************************************

#Function for running saucer
def runSaucer(button):
    # Set shutdown variable to false since we are running
    global running
    global shutdown
    shutdown = False
    
    if(not running):
        # Set speeds using size and amount
        setSpeeds(size, amount)
        
        print("SIZE: " + str(size))
        print("RUNNING SAUCE")
        
        # Start sauce program thread
        sauce = threading.Thread(target=sauceProgram, args = (button,))
        sauce.start()
    

# Function for sauce thread
def sauceProgram(button):
    # Set running variable to true since we are running
    global running, size
    running = True
    button['bg'] = "gray60"
    
    global shutdown
    pizzaTime = time.time()
    
    # Run corresponding saucer pumps
    global sauce_spin_steps
    pumpProgram(size)
    spinFunc()
    while((not shutdown) and (time.time()-pizzaTime < turn_table_time)):
        pass
    stopPumping()
    stopSpinning()
        
    # Update diagnostics and firebase if emergency stop was not made
    if(not shutdown):
        pizzaTime = time.time() - pizzaTime
        updateDiagnostics(pizzaTime)
        updateFirebase(time.strftime("%H:%M:%S"),size)
    
    # Set amount to normal
    setAmount(med)
    
    # Update running - sauce is done
    running = False
    size = -1

#Functions for starting and stopping spin
def spinFunc():
  spin = "$STEPPER_START,TURNTABLE,FORWARD,"+ str(turn_table_speed) + ",0\r\n"
  ser.write(spin.encode())
  print(spin)

def stopSpinning():
  stop = "$STEPPER_STOP,TURNTABLE\r\n"
  ser.write(stop.encode())
  print(stop)

#Functions for starting and stopping sauce
def pumpProgram(size):
    # Start pumping infinitely based on size
    start1 = "$STEPPER_START,PUMP1,FORWARD," + str(s1_speed) + ",0\r\n"
    print(start1)
    ser.write(start1.encode())
    if size >= 10:
        start2 = "$STEPPER_START,PUMP2,FORWARD," + str(s2_speed) + ",0\r\n"
        print(start2)
        ser.write(start2.encode())
    if size >= 12:
        start3 = "$STEPPER_START,PUMP3,FORWARD," + str(s3_speed) + ",0\r\n"
        print(start3)
        ser.write(start3.encode())
    if size >= 14:
        start4 = "$STEPPER_START,PUMP4,FORWARD," + str(s4_speed) + ",0\r\n"
        print(start4)
        ser.write(start4.encode())

def stopPumping():
  global pumping
  pumping = False
  stop1 = "$STEPPER_STOP,PUMP1\r\n"
  print(stop1)
  ser.write(stop1.encode())
  stop2 = "$STEPPER_STOP,PUMP2\r\n"
  print(stop2)
  ser.write(stop2.encode())
  stop3 = "$STEPPER_STOP,PUMP3\r\n"
  print(stop3)
  ser.write(stop3.encode())
  stop4 = "$STEPPER_STOP,PUMP4\r\n"
  print(stop4)
  ser.write(stop4.encode())

#**************************************CLEAN AND PRIME**************************************

# Function to clean
def clean(button):
    # Set shutdown variable to false since we are running
    global running
    global shutdown
    shutdown = False
    
    if(not running):
        # Start clean program thread
        c = threading.Thread(target=cleanProgram, args=(button,))
        c.start()

# Function used in clean thread
def cleanProgram(button):
    print("Cleaning\n")
    
    # Set running variable to true since we are cleaning
    global running
    running = True
    button['bg'] = "gray60"
    
    global shutdown, clean_prime_speed
    cleanTime = time.time()

    # Pump for 2 minutes
    start1 = "$STEPPER_START,PUMP1,FORWARD," + str(clean_prime_speed) + ",0\r\n"
    ser.write(start1.encode())
    start2 = "$STEPPER_START,PUMP2,FORWARD," + str(clean_prime_speed) + ",0\r\n"
    ser.write(start2.encode())
    start3 = "$STEPPER_START,PUMP3,FORWARD," + str(clean_prime_speed) + ",0\r\n"
    ser.write(start3.encode())
    start4 = "$STEPPER_START,PUMP4,FORWARD," + str(clean_prime_speed) + ",0\r\n"
    ser.write(start4.encode())
    while((not shutdown) and (time.time()-cleanTime < 120)):
        button['text'] = int(120-(time.time()-cleanTime))
    stopPumping()
    
    # Update running - cleaning is done
    running = False
    button['bg'] = button_color
    button['text'] = "CLEAN"

# Function to prime
def prime(button):
    # Set shutdown variable to false since we are running
    global running
    global shutdown
    shutdown = False
    
    if(not running):
        # Start clean program thread
        p = threading.Thread(target=primeProgram, args=(button,))
        p.start()
        
# Function used in prime thread
def primeProgram(button):
    print("Priming\n")
        
    # Set running variable to true since we are priming
    global running
    running = True
    button['bg'] = "gray60"
    
    global shutdown, clean_prime_speed
    primeTime = time.time()

    # Pump for 30 seconds
    start1 = "$STEPPER_START,PUMP1,FORWARD," + str(clean_prime_speed) + ",0\r\n"
    ser.write(start1.encode())
    start2 = "$STEPPER_START,PUMP2,FORWARD," + str(clean_prime_speed) + ",0\r\n"
    ser.write(start2.encode())
    start3 = "$STEPPER_START,PUMP3,FORWARD," + str(clean_prime_speed) + ",0\r\n"
    ser.write(start3.encode())
    start4 = "$STEPPER_START,PUMP4,FORWARD," + str(clean_prime_speed) + ",0\r\n"
    ser.write(start4.encode())
    while((not shutdown) and (time.time()-primeTime < 30)):
        button['text'] = int(30-(time.time()-primeTime))
    stopPumping()
    
    # Update running - priming is done
    running = False
    button['bg'] = button_color
    button['text'] = "PRIME"

#*************************************CHANGE SAUCE AMT**************************************

# Functions for setting pump amount as percentage of speeds and colors of buttons
def setSpeeds(sz, amt):
    # Calculate calibration constant
    cal = math.sqrt((150 - calibration[sz])/100)
        
    # Assign speeds to each motor (corresponding speed x calibration percent x extra/normal/less)
    global s1_speed, s2_speed, s3_speed, s4_speed
    s1_speed = int(motor1speeds[sz]*cal*amt) # Sauce stepper motor 1 speed
    s2_speed = int(motor2speeds[sz]*cal*amt) # Sauce stepper motor 2 speed
    s3_speed = int(motor3speeds[sz]*cal*amt) # Sauce stepper motor 3 speed
    s4_speed = int(motor4speeds[sz]*cal*amt) # Sauce stepper motor 4 speed

def setColor(color):
    fourteenButton["bg"] = color
    twelveButton["bg"] = color
    tenButton["bg"] = color
    sevenButton["bg"] = color

def setAmount(amt):
    global amount, speed
    if amt == amount or amt == med:
        amount = med
        setColor("lime green")
        light["bg"] = button_color
        extra["bg"] = button_color
    elif amt == lt:
        amount = lt
        setColor("orange")
        light["bg"] = "orange"
        extra["bg"] = button_color
    elif amt == ext:
        amount = ext
        setColor("DarkOrange2")
        light["bg"] = button_color
        extra["bg"] = "DarkOrange2"

#********************************CALIBRATION / DIAGNOSTICS**********************************

# Functions for adding and subtracting from saucer pump speed during calibration
def add(size, speedVar):
    if(calibration[size] < 100):
        calibration[size] = calibration[size] + 5
        speedVar.set(calibration[size])
        updateCalibrationFile()

def subtract(size, speedVar):
    if(calibration[size] > 0):
        calibration[size] = calibration[size] - 5
        speedVar.set(calibration[size])
        updateCalibrationFile()

# Function for saving current calibrations
def updateCalibrationFile():
    # Get current data
    with open('/home/pi/SaucerCode/diagnostics.txt', 'r') as reader:
        calibs = reader.read().splitlines()
        
    # Update data
    global calibration
    calibs[4] = str(calibration[7])
    calibs[5] = str(calibration[10])
    calibs[6] = str(calibration[12])
    calibs[7] = str(calibration[14])
    
    # Set data in file
    with open('/home/pi/SaucerCode/diagnostics.txt', 'w') as writer:
        for data in calibs:
            writer.write("%s\n" % data)

# Function for updating diagnostics
def updateDiagnostics(pizzaTime):
    # Get current data
    with open('/home/pi/SaucerCode/diagnostics.txt', 'r') as reader:
        diags = reader.read().splitlines()
        
    # Update total time
    global totalTime
    diags[1] = str(int(diags[1]) + int((time.time() - totalTime)/60))
    
    # Set data in file
    with open('/home/pi/SaucerCode/diagnostics.txt', 'w') as writer:
        for data in diags:
            writer.write("%s\n" % data)
  
# Function for sending sos menu data to Firebase
def updateFirebase(timeString, size):
    # Send pizza made to Firebase
    fbString = str(size) + '" pizza made at ' + timeString
    
    if(hasInternet):
      count = db.child("Pizza Throughput").child(str(size)).get().val()["COUNT"]
      weight = db.child("Pizza Throughput").child(str(size)).get().val()["WEIGHT"]

      count += 1
      if(amount == lt):
        weight += lt_weights[size]
      elif(amount == med):
        weight += med_weights[size]
      else:
        weight += ext_weights[size]

      db.child("Pizza Throughput").child(str(size)).update({"COUNT":count})
      db.child("Pizza Throughput").child(str(size)).update({"WEIGHT":weight})

      db.child("Pizzas").push(fbString)
      
      print(fbString)
      print("Sending data to Firebase")

#*****************************************HELP MENU*****************************************

# Function for changing button text based on answer
def change(button):
    if button['text'] == "NO":
        button['bg'] = "PaleGreen1"
        button['text'] = "YES"
    else:
        button['bg'] = "IndianRed2"
        button['text'] = "NO"

# Function for sending sos menu data to Firebase
def send(answers, menu):
    # Send to Firebase
    str = "Answers:"
    for button in answers:
        str = str + " " + button['text']
    if(hasInternet):
      db.child("Help Requests").push(str)
    print(str)
    print("Sending data to Firebase")
    
    # Pop up then exit
    msg = StringVar()
    msg.set("FORM SUBMITTED\nIn an emergency,\nplease call 614-226-4421.\n")
    smallFont = font.Font(family='Helvetica', size=20, weight='normal')
    text = Label(menu, font=smallFont, textvariable=msg, bg = "light green", bd=4, relief="groove", fg="black", height=7, width=35)
    text.place(x=130, y=120)
    menu.update()
    ok = Button(menu, text = "OK", font = smallFont, fg= main_fg, bg = button_color, command = menu.destroy)
    ok.place(x=365, y=278)


#***************************************DATA SCREEN*****************************************
    
# Function setting up screen with Firebase data
def dataScreen(more):
    # Create window for data screen
    data = Toplevel()
    data.title("Saucer Data Screen")
    data.geometry('800x480')
    data.configure(bg=main_bg)
    data.overrideredirect(1)
    
    # Fonts for screen
    sizeFont = font.Font(family='Helvetica', size=25, weight='normal')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    descriptionFont = font.Font(family='Helvetica', size=20, weight='normal')
    titleFont = font.Font(family='Helvetica', size=20, weight='bold')
    
    # Data screen buttons
    home  = Button(data, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = lambda : killTwoScreens(data, more), height = 2, width = 7) # will this work?? !!!!
    home.place(x=625, y=380)
    back  = Button(data, text = "BACK", font = otherFont, bg = button_color, fg = main_fg, command = data.destroy, height = 2, width = 7)
    back.place(x=445, y=380)
    
    # Read data from Firebase if internet, else show error text
    if(hasInternet):
        # Gather data from database
        count7 = db.child("Pizza Throughput").child(str(7)).get().val()["COUNT"]
        weight7 = db.child("Pizza Throughput").child(str(7)).get().val()["WEIGHT"]
        count10 = db.child("Pizza Throughput").child(str(10)).get().val()["COUNT"]
        weight10 = db.child("Pizza Throughput").child(str(10)).get().val()["WEIGHT"]
        count12 = db.child("Pizza Throughput").child(str(12)).get().val()["COUNT"]
        weight12 = db.child("Pizza Throughput").child(str(12)).get().val()["WEIGHT"]
        count14 = db.child("Pizza Throughput").child(str(14)).get().val()["COUNT"]
        weight14 = db.child("Pizza Throughput").child(str(14)).get().val()["WEIGHT"]
        
        # Output recent pizzas, as many as possible
        title = Text(data, font = titleFont, bd = -2, bg = main_bg, fg = main_fg, height=1, width=40)
        title.insert(INSERT, "DATA: RECENT PIZZAS")
        title.place(x=25,y=25)
        
        yPos = 75
        fbdata = db.child("Pizzas").get()
        fb_list = fbdata.each()
        fb_list.reverse()
        for p in fb_list:
            txt = Text(data, font = descriptionFont, bd = -2, bg = main_bg, fg = main_fg, height=1, width=25)
            txt.insert(INSERT,p.val())
            txt.place(x=25,y=yPos)
            yPos += 50
            if(yPos > 450): break
        
        # Output count / weight data (maybe fix format)
        size7 = Text(data, font = sizeFont, bd = -2, bg = button_color, fg = main_fg, height=2, width=14)
        size7.insert(INSERT, " 7\" Count: " + str(count7) + "\n    Weight: " + str(weight7) + " lbs")
        size7.place(x=510,y=20)
        size10 = Text(data, font = sizeFont, bd = -2, bg = button_color, fg = main_fg, height=2, width=14)
        size10.insert(INSERT, " 10\" Count: " + str(count10) + "\n    Weight: " + str(weight10) + " lbs")
        size10.place(x=510,y=107)
        size12 = Text(data, font = sizeFont, bd = -2, bg = button_color, fg = main_fg, height=2, width=14)
        size12.insert(INSERT, " 12\" Count: " + str(count12) + "\n    Weight: " + str(weight12) + " lbs")
        size12.place(x=510,y=194)
        size14 = Text(data, font = sizeFont, bd = -2, bg = button_color, fg = main_fg, height=2, width=14)
        size14.insert(INSERT, " 14\" Count: " + str(count14) + "\n    Weight: " + str(weight14) + " lbs")
        size14.place(x=510,y=280)
    else:
        error = Text(data, font = sizeFont, bd = -2, bg = main_bg, fg = main_fg, height=1, width=40)
        error.insert(INSERT, "ERROR: NO INTERNET CONNECTION")
        error.place(x=360,y=170)
    

#***********************************OTHER SCREEN SET UP*************************************

# Function setting up ... screen with various helpful features
def troubleshootingScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Saucer Troubleshooting Screen")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')


    #Images
    imgOne = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
    imgTwo = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
    imgThree = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
    imgFour = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
    imgFive = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
    imgSix = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
    imgSeven = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
    imgEight = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
    imgNine = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))

    #Buttons for images
    imageOneButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgOne, command = imageOneScreen, height = 1, width = 8)
    imageOneButton.place(x=460, y=20)

    imageTwoButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgTwo, command = imageOneScreen, height = 1, width = 8)
    imageTwoButton.place(x=460, y=20)

    imageThreeButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgThree, command = imageOneScreen, height = 1, width = 8)
    imageThreeButton.place(x=460, y=20)

    imageFourButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgFour, command = imageOneScreen, height = 1, width = 8)
    imageFourButton.place(x=460, y=20)

    imageFiveButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgFive, command = imageOneScreen, height = 1, width = 8)
    imageFiveButton.place(x=460, y=20)

    imageSixButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgSix, command = imageOneScreen, height = 1, width = 8)
    imageSixButton.place(x=460, y=20)

    imageSevenButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgSeven, command = imageOneScreen, height = 1, width = 8)
    imageSevenButton.place(x=460, y=20)

    imageEightButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgEight, command = imageOneScreen, height = 1, width = 8)
    imageEightButton.place(x=460, y=20)

    imageNineButton  = Button(other, text = "", font = calibFont, bg = button_color, fg = main_fg, image = imgNine, command = imageOneScreen, height = 1, width = 8)
    imageNineButton.place(x=460, y=20)

    #Buttons for calibration
    fourteenCalibrationButton  = Button(other, text = "Calibrate 14 Inch", font = calibFont, bg = button_color, fg = main_fg, command = fourteenCalibrationScreen, height = 1, width = 8)
    fourteenCalibrationButton.place(x=460, y=20)

    twelveCalibrationButton  = Button(other, text = "Calibrate 12 Inch", font = calibFont, bg = button_color, fg = main_fg, command = twelveCalibrationScreen, height = 1, width = 8)
    twelveCalibrationButton.place(x=460, y=20)

    tenCalibrationButton  = Button(other, text = "Calibrate 10 Inch", font = calibFont, bg = button_color, fg = main_fg, command = tenCalibrationScreen, height = 1, width = 8)
    tenCalibrationButton.place(x=460, y=20)

    sevenCalibrationButton  = Button(other, text = "Calibrate 7 Inch", font = calibFont, bg = button_color, fg = main_fg, command = sevenCalibrationScreen, height = 1, width = 8)
    sevenCalibrationButton.place(x=460, y=20)

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)
    
    #TEMPORARY QUIT
    quitButton  = Button(other, text = "Q", font = diagFont, bg = button_color, fg = main_fg, command = screen.destroy, height = 1, width = 1)
    quitButton.place(x=300, y=10)
    


#**************************************SCREENS FOR THE CALIBRATION OF THE SAUCER***************************************


def fourteenCalibrationScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Calibrate 14 Inch Pizza")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)
    
def twelveCalibrationScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Calibrate 12 Inch Pizza")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)
    
def tenCalibrationScreen():

    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Calibrate 10 Inch Pizza")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)
    
def sevenCalibrationScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Calibrate 14 Inch Pizza")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)



#**************************************SCREENS FOR THE IMAGES OF COMMON ISSUES***************************************

def imageOneScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)


def imageTwoScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)


def imageThreeScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)


def imageFourScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)


def imageFiveScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)


def imageSixScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)


def imageSevenScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)


def imageEightScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)
    

def imageNineScreen():
    global speed
        
    # Create window for more menu
    other = Toplevel()
    other.title("Troubleshooting")
    other.geometry('800x480')
    other.configure(bg=main_bg)
    other.overrideredirect(1)
    
    # Fonts for screen
    stopFont = font.Font(family='Helvetica', size=50, weight='bold')
    otherFont = font.Font(family='Helvetica', size=24, weight='normal')
    headingFont = font.Font(family='Helvetica', size=20, weight='normal')
    calibFont = font.Font(family='Helvetica', size=30, weight='normal')
    diagFont = font.Font(family='Helvetica', size=19, weight='normal')

    home  = Button(other, text = "HOME", font = otherFont, bg = button_color, fg = main_fg, command = other.destroy, height = 1, width = 7)
    home.place(x=625, y=380)
    data  = Button(other, text = "DATA", font = otherFont, bg = button_color, fg = main_fg, command = lambda: dataScreen(other), height = 1, width = 7)
    data.place(x=445, y=380)




#**************************************TKINTER SET UP***************************************

# TK screen set up
screen = Tk()
screen.overrideredirect(1)
screen.geometry('800x480')
screen.configure(bg=main_bg)
screen.title("Sm^rt Saucer")

# Fonts for screen
sizeFont = font.Font(family='Helvetica', size=52, weight='bold')
stopFont = font.Font(family='Helvetica', size=50, weight='bold')
otherFont = font.Font(family='Helvetica', size=24, weight='normal')

# Size buttons
fourteenButton  = Button(screen, text = "14\"", font = sizeFont, bg = "lime green", fg = "white", command = lambda: setSize(fourteenButton, 14), height = 2 , width = 3)
fourteenButton.place(x=640, y=15)

twelveButton  = Button(screen, text = "12\"", font = sizeFont, bg = "lime green", fg = "white", command = lambda: setSize(twelveButton, 12), height = 2 , width = 3)
twelveButton.place(x=430, y=15)

tenButton  = Button(screen, text = "10\"", font = sizeFont, bg = "lime green", fg = "white", command = lambda: setSize(tenButton, 10), height = 2 , width = 3)
tenButton.place(x=222, y=15)

sevenButton  = Button(screen, text = "7\"", font = sizeFont, bg = "lime green", fg = "white", command = lambda: setSize(sevenButton, 7), height = 2 , width = 3)
sevenButton.place(x=15, y=15)

# Donatos Image
img = PIL.ImageTk.PhotoImage(PIL.Image.open(donatos_path).resize((114,38), PIL.Image.ANTIALIAS))
logo = Label(screen, image = img, bg=main_bg)
logo.place(x=40, y=255)

# Function button
stopButton  = Button(screen, text = "STOP", font = stopFont, bg = "red2", fg = "white", command = emergencyStop, height = 1, width = 9)
stopButton.place(x=220, y=235)

moreButton  = Button(screen, text = "...", font = stopFont, bg = button_color, fg = main_fg, command = troubleshootingScreen, height = 1, width = 3)
moreButton.place(x=640, y=235)

cleanButton  = Button(screen, text = "CLEAN", font = otherFont, bg = button_color, fg = main_fg, command = lambda: clean(cleanButton), height = 2, width = 10)
cleanButton.place(x=15, y=380)

primeButton  = Button(screen, text = "PRIME", font = otherFont, bg = button_color, fg = main_fg, command = lambda: prime(primeButton), height = 2, width = 10)
primeButton.place(x=575, y=380)

light  = Button(screen, text = "LESS\nSAUCE", font = otherFont, activebackground = "orange", activeforeground = "white", bg = button_color, fg = main_fg, command = lambda: setAmount(lt), height = 2, width = 5)
light.place(x=260, y=380)

extra  = Button(screen, text = "EXTRA\nSAUCE", font = otherFont, activebackground = "DarkOrange2", activeforeground = "white", bg = button_color, fg = main_fg, command = lambda: setAmount(ext), height = 2, width = 5)
extra.place(x=420, y=380)

mainloop()
