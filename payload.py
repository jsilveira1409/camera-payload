import os
import time
import serial
import struct
from picamera2 import Picamera2

STATES = {
    'IDLE': 0x00,
    'RUN_INFERENCE': 0x01,
    'STOP_INFERENCE': 0x02,
    'DOWNLINK': 0x03,
    'POWER_OFF': 0xFF,
}

SERIAL_PORT = "/dev/ttyS0"  
BAUD_RATE = 115200
CHUNK_SIZE = 8192
IMAGE_PATH = "payload_image.jpg"

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (1920, 1080)})
picam2.configure(config)

def take_picture():
    """Capture an image using Picamera2."""
    picam2.start()
    time.sleep(1)  # Let the camera stabilize
    picam2.capture_file(IMAGE_PATH)
    picam2.stop()
    print(f"Image captured and saved as {IMAGE_PATH}")

def downlink_image():
    """Send the captured image over serial in chunks."""
    if not os.path.exists(IMAGE_PATH):
        print("No image to downlink.")
        return

    img_size = os.path.getsize(IMAGE_PATH)
    start_word = 0xDEADBEEF

    header = struct.pack(">II", start_word, img_size)
    ser.write(header)

    with open(IMAGE_PATH, "rb") as img_file:
        sent_bytes = 0
        while chunk := img_file.read(CHUNK_SIZE):
            ser.write(chunk)
            sent_bytes += len(chunk)
            print(f"Sent {sent_bytes}/{img_size} bytes...")

    print("Image successfully downlinked.")

def move_files_to_data_directory():
    """Move processed files to the data directory."""
    data_directory = './data/'
    os.makedirs(data_directory, exist_ok=True)

    try:
        for file in os.listdir('.'):
            source_file_path = os.path.join('.', file)
            if os.path.isfile(source_file_path) and file.endswith('.jpg'):
                destination_file_path = os.path.join(data_directory, file)
                os.rename(source_file_path, destination_file_path)
                print(f"Moved {file} to {data_directory}")
    except Exception as e:
        print(f"Failed to move files: {e}")

def main():
    """Main loop to handle states."""
    ser.flush()
    print("Waiting for commands...")

    while True:
        if ser.in_waiting > 0:
            state = ser.read(1)
            if not state:
                continue
            state = ord(state)
            print(f"Received state: {state}")

            if state == STATES['IDLE']:
                print("State: IDLE")
            elif state == STATES['RUN_INFERENCE']:
                print("State: RUN_INFERENCE - Capturing image.")
                take_picture()
            elif state == STATES['STOP_INFERENCE']:
                print("State: STOP_INFERENCE")
            elif state == STATES['DOWNLINK']:
                print("State: DOWNLINK - Sending image.")
                downlink_image()
            elif state == STATES['POWER_OFF']:
                print("State: POWER_OFF - Shutting down.")
                break
            else:
                print(f"Unknown state: {state}")    
    move_files_to_data_directory()

if __name__ == "__main__":
    try:
        ser.flushInput()  
        ser.flushOutput() 
        main()
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        ser.close()
