import os
import shutil
import time
import serial
import struct

STATES = {
    'IDLE': 0x00,
    'RUN_INFERENCE': 0x01,
    'STOP_INFERENCE': 0x02,
    'DOWNLINK': 0x04,
    'POWER_OFF': 0xFF,
}


def receive_images(image_count):
    global ser
    print(f"Receiving image {image_count}...")
    
    header_size = 8 
    header_data = ser.read(header_size)

    if len(header_data) < header_size:
        print("Failed to read full header")
        return
    else:
        print("Received header, side : ", len(header_data))
        print(header_data)

    start_word, img_size = struct.unpack(">II", header_data)
    
    if start_word != 0xDEADBEEF:
        print(f"Invalid start word: {start_word}")
        return
    
    print(f"Start word: {hex(start_word)}, Image size: {img_size} bytes")

    image_filename = f'image_{image_count}.jpg'
    data_recv = 0

    with open(image_filename, 'wb') as image_file:
        while data_recv < img_size:
            try:
                image_data = ser.read(min(8192, img_size - data_recv))
                if not image_data:
                    print('No more data for this image')
                    break 
                
                data_recv += len(image_data)
                image_file.write(image_data)
                print(f"Image {image_count} received, total received {data_recv}/{img_size} bytes")
                
            except Exception as e:
                print(f"Error receiving image: {e}")
                break

    if data_recv >= img_size:
        print(f"Image {image_count} fully received and saved as {image_filename}")
    else:
        print(f"Image {image_count} was not fully received, only {data_recv}/{img_size} bytes received")

def downlink():
    ser.write(b'\x03')
    receive_images(0)        
    

def move_files_to_data_directory():
    data_directory = './data/'
    os.makedirs(data_directory, exist_ok=True)

    try:
        for file in os.listdir('.'):
            source_file_path = os.path.join('.', file)
            if os.path.isfile(source_file_path):
                destination_file_path = os.path.join(data_directory, file)
                shutil.copy(source_file_path, destination_file_path)
                
    except Exception as e:        
        print(f"Failed to move files to data directory: {str(e)}\n")

if __name__ == "__main__":
    ser = serial.Serial('/dev/ttyUSB0', 115200)
    ser.flushInput()  
    ser.flushOutput() 
    ser.flush()
    ser.timeout = 5
    ser.write(b'\x01')
    time.sleep(2)
    ser.write(b'\x02')
    time.sleep(2)
    downlink()
    move_files_to_data_directory()
    