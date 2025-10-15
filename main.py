import pyvisa
import time
import RPi.GPIO as GPIO
#import pyserial as serial

def readout(instr, output=True, raw=False):
    response = "error"
    try:
        if not raw:
            response = instr.read()
        else: 
            respones = instr.read_raw()
        if output:
            print(response)
        return response
    except pyvisa.VisaIOError as e:
        if output:
            print(f'Readout error: {e}')
        return "error"

def device_setup(addr):
    instrument = rm.open_resource(addr)
    instrument.baud_rate = 9600  # Set the correct baud rate
    instrument.parity = pyvisa.constants.Parity.none  # Set parity
    instrument.stop_bits = pyvisa.constants.StopBits.one  # Set stop bits
    instrument.data_bits = 8  # Set data bits
    instrument.timeout = 500
    print(f'Connected to {addr}')
    return instrument
########################################
#                setup                 #
########################################

#gpio
GPIO.setmode(GPIO.BCM)
base_pin = 18
GPIO.setup(base_pin, GPIO.OUT)
GPIO.output(base_pin, GPIO.HIGH)
#GPIO.output(base_pin, GPIO.LOW)
#time.sleep(10)
#serial comms
rm = pyvisa.ResourceManager()
connections = rm.list_resources()
addr0 = connections[0]
addr1 = connections[1]
ps_string = "Agilent Technologies"
powersupply = ''
PAX = ''
instrument = ''
response = ''
done = False

try:
    # Start by openning first USB device
    instrument = device_setup(addr0)

    # Test to see if power supply or PAX
    command = '*IDN?'  # Query the device ID (Power Supply)
    #command = 'TMID*'  # Query the device ID (PAX Unit)
    instrument.write(command)
    time.sleep(1)
    response = readout(instrument)
    
    # if device is power supply, setup PAX
    if ps_string in response:
        powersupply = instrument
        PAX = device_setup(addr1)
        print("Power supply connected. Connecting to PAX...")
        
    else:
        PAX = instrument
        powersupply = device_setup(addr1)
        print("PAX must be connected to USB0. Connecting to power supply...")
        powersupply.write(command)
        time.sleep(1)
        response = readout(instrument)

except pyvisa.VisaIOError as e:
    print(f'Error: {e}')
    done = True

########################################
#            main procedure            #
########################################
#ensure ps is off to start
response = powersupply.write("OUTP OFF")
time.sleep(0.1)
#Start by shorting the transistor
print("Locking the PAX Board for test mode...")
GPIO.output(base_pin, GPIO.HIGH)
#time.sleep(15)
print("Lock wire is shorted.")
time.sleep(0.1)

#print("DEBUG: POWER BOARD")
#time.sleep(10)

#Power Board
print("\nStarting the board in test mode\n")
response = powersupply.write("OUTP ON")
time.sleep(0.1)
response = powersupply.write("VOLT 19")
time.sleep(6)

#Show that the board goes into customer mode 
print("\nCircuit Unlocked.")
print("Board is now in customer mode...\n")
GPIO.output(base_pin, GPIO.LOW)

time.sleep(2)
# clear buffer
readout(PAX, False)

# send TMIDs
time.sleep(0.1)
print("Getting device ID")
print("Initial TMID:")
PAX.write("TMID*")
time.sleep(0.5)
readout(PAX)


#DO CUSOMER MODE TESTS
#Get id (tmid)
print("Second TMID:")
response = PAX.write("TMID*")
time.sleep(0.5)
response = PAX.read()
print(response)
print("\n*IF YOU SEE A DEVICE ID ABOVE, THE TEST PASSED*\n")

'''
# Enter customer display, get out of test mode
for i in range(2):
    response = PAX.write("TX4*")
    time.sleep(1)
    readout(PAX, output=False)
'''

#show LED functionality
print("Testing LED Display")
cmd = b'\x56\x58\x32\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x2A'
PAX.write_raw(cmd)
print("\n*IF EVERY LED IS ON, THE TEST PASSED*")
time.sleep(3)

#button functionality
print("Testing Button Functionality")
response = PAX.write("TX4*")
time.sleep(1)
readout(PAX, output=False)

'''
b'~\r\n' #DSP
b'}\r\n' #PAR
b'{\r\n' #F1
b'w\r\n' #F2
b'o\r\n' #RST
'''

def test_button(button, PAX, name):
    print(f"\nPlease press the {name} button.")
    done = False
    i = 0
    while not done:
        response = PAX.write("TX2*")
        time.sleep(0.05)
        response = readout(PAX, output=False, raw=False)
        if response != "error":
            response = response.encode('utf-8')
        if response != b'\x7f\r\n': #if response != blank input
            time.sleep(1)
            if response != button:
                print(f"Wrong button pressed. Please press the {name} button.")
                i += 1;
            elif i > 5:
                done = True
                print(f"\nTest Failed: There was a problem verifying {name}'s functionality.\n")
            elif response == 'error':
                pass
            else:
                print(f"\n{name} works! Moving on...")
                done = True

test_button(b'~\r\n', PAX, "DSP")
test_button(b'}\r\n', PAX, "PAR")
test_button(b'{\r\n', PAX, "F1")
test_button(b'w\r\n', PAX, "F2")
test_button(b'o\r\n', PAX, "RST")

print("\nAutomated test complete! Have a nice day.\n")
#NICE TO HAVE: display volatge ranges for board

time.sleep(5)

print("\nPowering Down...\n")
response = powersupply.write("OUTP OFF")
time.sleep(0.1)
GPIO.output(base_pin, GPIO.HIGH)
print("\nCircuit Locked.")



########################################
#                debug                 #
########################################
'''
while not done:
    userin = input("> ")
    if userin == "q":
        done = True
    else:
        try:
            response = instrument.write(userin)
            time.sleep(1)
            print(response)
        except pyvisa.VisaIOError as e:
            print(f"There was a problem: {e}")
'''
