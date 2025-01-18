import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
import time
from luma.core.interface.serial import spi
from luma.oled.device import ssd1306
from PIL import Image


# Initialize SPI interface
serial2 = spi(port=0, device=1, gpio_DC=24, gpio_RST=25)
# Initialize the OLED display
device2 = ssd1306(serial2, width=128, height=64)

# Load and display the image
sleep_face = Image.open('Sleep_Face.bmp').convert('1')
talk_1 = Image.open('Talk_Face1.bmp').convert('1')
talk_2 = Image.open('Talk_Face2.bmp').convert('1')


# Shared flag to control the loop
loop_flag = threading.Event()
loop_flag.set()  # Initially set to True

# Function to display a design

# Looping display function
def loop_talk():
    while True:
        loop_flag.wait()  # Block until loop_flag is set
        device2.display(talk_1)
        time.sleep(0.5)
        device2.display(talk_2)
        time.sleep(0.5)

# Start the loop in a separate thread
loop_thread = threading.Thread(target=loop_talk, daemon=True)
loop_thread.start()

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

FREQUENCY = 60
m1, m2,= 17, 27
GPIO.setup(m1, GPIO.OUT)
pwm1 = GPIO.PWM(m1, FREQUENCY)
GPIO.setup(m2, GPIO.OUT)
pwm2 = GPIO.PWM(m2, FREQUENCY)
pwm1.start(0)
pwm2.start(0)


def control_servo(angle, pwm):
    duty_cycle = 2 + (angle / 18)  # Convert angle to duty cycle
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)  # Allow servo to reach position
    pwm.ChangeDutyCycle(0)  # Stop sending signal

# MQTT broker details
broker = "test.mosquitto.org"
port = 1883

# Callback functions
def Hands(client, userdata, msg):
    positions = [180, 90, 0]
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    pos_data = msg.payload.decode()
    right_hand = (pos_data[:3]).index(1)
    left_hand = (pos_data[3:]).index(1)

    # Control servos in separate threads
    threading.Thread(target=control_servo, args=(positions[right_hand], pwm1)).start()
    threading.Thread(target=control_servo, args=(positions[left_hand], pwm2)).start()
def Face(client, userdata, msg):
    global loop_flag
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    face_result = msg.payload.decode()
    if face_result == "sleep":
        loop_flag.clear()  # Stop the loop
        device2.display(sleep_face)
        time.sleep(1)
        device2.display(sleep_face)
    else:
        loop_flag.set()  # Restart the loop

# MQTT client setup
client1 = mqtt.Client()
client2 = mqtt.Client()

client1.on_message = Hands
client2.on_message = Face

client1.connect(broker, port, 60)
client2.connect(broker, port, 60)

client1.subscribe("pos")
client2.subscribe("face")

# Function to start the loop in a separate thread
def start_client_loop(client):
    client.loop_forever()

# Create threads for both clients
thread1 = threading.Thread(target=start_client_loop, args=(client1,))
thread2 = threading.Thread(target=start_client_loop, args=(client2,))

# Start the threads
thread1.start()
thread2.start()

print("Both clients are running.")
