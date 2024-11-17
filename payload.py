import serial
import time
import os
from picamera import PiCamera

# Initialize the camera
camera = PiCamera()

# Set up the serial connection (adjust the port and baudrate as needed)
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
ser.flush()

def take_picture():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    image_path = f"/home/pi/pictures/{timestamp}.jpg"
    camera.capture(image_path)
    print(f"Picture taken and saved as {image_path}")
    return image_path

def send_picture(image_path):
    with open(image_path, 'rb') as image_file:
        ser.write(image_file.read())
    print(f"Picture {image_path} sent over serial")

while True:
    if ser.in_waiting > 0:
        command = ser.readline().decode('utf-8').strip()
        if command == "TAKE_PICTURE":
            image_path = take_picture()
            ser.write(f"PICTURE_TAKEN:{image_path}\n".encode('utf-8'))
        elif command.startswith("SEND_PICTURE:"):
            image_path = command.split(":")[1]
            if os.path.exists(image_path):
                send_picture(image_path)
            else:
                ser.write(f"ERROR:FILE_NOT_FOUND\n".encode('utf-8'))
        else:
            ser.write(f"ERROR:UNKNOWN_COMMAND\n".encode('utf-8'))