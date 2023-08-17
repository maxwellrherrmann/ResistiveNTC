import time
import curses
import datetime
import csv
import sys
import os
import argparse
import RPi.GPIO as GPIO
import numpy as np

sys.dont_write_bytecode = True

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

a_pin = 18
b_pin = 23
c_pin = 24

parser = argparse.ArgumentParser(
        prog='python3 ntc.py',
        description='This program is designed to continuously read out an NTC thermistor temperature for CROC v1',
        epilog='Created by Jesse Harris (University of Tennessee) and Max Herrmann (CU Boulder)')

parser.add_argument('-c', '--calibration', required=True, help="NTC calibration .csv file, as produced by calib.py. Format is A,B,C (the arguments of SH function)")
parser.add_argument('-o', '--output', required=True, help='Output file name (full or relative path)')
parser.add_argument('-p', '--pretty', required=False, help='Flag to enable curses scrolling output', action='store_true')
args = parser.parse_args()

output_file = args.output
calib_file = args.calibration
pretty = args.pretty

def temperature(x, calib_file):
    with open(calib_file, 'r') as f:
        reader = csv.reader(f)
        lines = [line for line in reader]
        temperature_fit = [float(l) for l in lines[0]]

    #temperature_fit = [1.3124088e-03, 3.27939912e-04, -1.63499825e-07]
    a,b,c = temperature_fit[0], temperature_fit[1], temperature_fit[2]
    return 1/(a+b*np.log(x)+c*np.log(x)**3)-273

def dischargeB():
    GPIO.setup(a_pin, GPIO.IN)
    GPIO.setup(b_pin, GPIO.OUT)
    GPIO.output(b_pin, False)
    time.sleep(0.02)

def charge_timeB():
    GPIO.setup(b_pin, GPIO.IN)
    GPIO.setup(a_pin, GPIO.OUT)
    count = 0
    GPIO.output(a_pin, True)
    while not GPIO.input(b_pin):
        count = count + 1
    return count

def analog_readB():
    dischargeB()
    return charge_timeB()

def dischargeC():
    GPIO.setup(a_pin, GPIO.IN)
    GPIO.setup(c_pin, GPIO.OUT)
    GPIO.output(c_pin, False)
    time.sleep(0.02)

def charge_timeC():
    GPIO.setup(c_pin, GPIO.IN)
    GPIO.setup(a_pin, GPIO.OUT)
    count = 0
    GPIO.output(a_pin, True)
    while not GPIO.input(c_pin):
        count = count + 1
    return count

def analog_readC():
    dischargeC()
    return charge_timeC()


def main(screen):
    sum1=0
    sum2=0
    ct=0

    headers = ['Time', 'GPIO23', 'GPIO24', 'Temperature']
    with open(output_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

    screen = curses.initscr()
    screen.clear()

    curses.curs_set(0)
    curses.cbreak()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

    screen.bkgd(' ', curses.color_pair(1) | curses.A_BOLD | curses.A_REVERSE)
    screen.nodelay(1) # Set non-blocking mode for getch()
    screen.refresh()

    height, width = screen.getmaxyx()
    
    header_win = screen.subwin(1, width, 0, 0)
    header_win.clear()
    header_win.addstr(headers[0]+'\t\t\t'+'\t\t'.join(headers[1:]))
    header_win.refresh()

    data_win = screen.subwin(height-2, width, 1, 0)
    data_win.addstr(0, 0, "Initializing... (waiting for first input)")
    data_win.refresh()

    prompt_win = screen.subwin(1, width, height - 1, 0)
    prompt_win.addstr(0, 0, "Hit 'q' to quit")
    prompt_win.refresh()

    data = []
    while True:
        data_win.erase()

        sum1=sum1+analog_readB()
        ct+=1
        time.sleep(1)
        sum2=sum2+analog_readC()
        if(ct>=10):
            e=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ct=0
            data.append([str(e)+'\t'+'\t\t'.join([str(sum1/10), str(sum2/10), str(temperature(sum2/10, calib_file))])])
            with open(output_file, 'a') as f:
                writer = csv.writer(f)
                writer.writerow([e, sum1/10, sum2/10, temperature(sum2/10, calib_file)])
            sum1=0
            sum2=0

        data_win.erase()

        if len(data)> height - 4:
            data = data[1:]

        for i,val in enumerate(data):
            data_win.addstr(i+1, 1, str(val[0])+'\t\t\t'+str('\t\t'.join(val[1:])))

        key = screen.getch()
        if key != -1:
            if key==ord('q'):
                data_win.clear()
                data_win.addstr(1, 1, "You've hit 'q', quitting now...")
                data_win.refresh()
                time.sleep(3)
                break

        data_win.box()
        data_win.refresh()
        prompt_win.refresh()
        header_win.refresh()

        time.sleep(1)
if pretty:
    curses.wrapper(main)
    os.system('clear')

else:
    sum1=0
    sum2=0
    ct=0

    headers = ['Time', 'GPIO23', 'GPIO24', 'Temperature']
    with open(output_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
    print(headers[0]+'\t\t\t'+'\t\t'.join(headers[1:]))

    while True:
        sum1=sum1+analog_readB()
        ct=ct+1
        time.sleep(1)
        sum2=sum2+analog_readC()
        if(ct>=10):
            e=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ct=0
            print(str(e)+'\t'+'\t\t'.join([str(sum1/10), str(sum2/10), str(temperature(sum2/10, calib_file))]))
            with open(output_file, 'a') as f:
                writer = csv.writer(f)
                writer.writerow([e, sum1/10, sum2/10, temperature(sum2/10, calib_file)])
            sum1=0
            sum2=0

        time.sleep(1)
