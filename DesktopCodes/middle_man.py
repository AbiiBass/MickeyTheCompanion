import threading
import paho.mqtt.client as mqtt
import pandas as pd
import time

# File path to store data
file_path = "Manage_Data.csv"
file_path2 = "data.csv"

# Ensure the CSV file exists and has the correct structure
try:
    df = pd.read_csv(file_path)
    df2 = pd.read_csv(file_path2)
except FileNotFoundError:
    # Create a DataFrame with the required structure
    df = pd.DataFrame(columns=["ExerciseChoice", "chooseMusic"])
    df2 = pd.DataFrame(columns=["BodyData"])
    df.loc[0] = [0, 0]  # Initialize the first row with default values
    df2.loc[0] = [0]
    df.to_csv(file_path, index=False)
    df2.to_csv(file_path2, index=False)

# MQTT configurations
broker = "test.mosquitto.org"
port = 1883

# Shared variables
ExerciseChoice = 0
stop_event = threading.Event()

# Function for the ExerciseChoice subscriber
def on_exercise_message(client, userdata, msg):
    global ExerciseChoice
    ExerciseChoice = int(msg.payload.decode())
    print(f"Received ExerciseChoice: {ExerciseChoice}")
    df.loc[0, "ExerciseChoice"] = ExerciseChoice
    df.to_csv(file_path, index=False)

    if ExerciseChoice == 0:
        stop_event.clear()  # Allow publishing
    else:
        stop_event.set()  # Stop publishing

# Function for the chooseMusic subscriber
def on_music_message(client, userdata, msg):
    chooseMusic = msg.payload.decode()
    print(f"Received chooseMusic: {chooseMusic}")
    df.loc[0, "chooseMusic"] = chooseMusic
    df.to_csv(file_path, index=False)

# Publisher function for BodyData
def publish_body_data():
    while True:
        stop_event.wait()  # Wait until publishing is allowed
        BodyData = df2.loc[0, "BodyData"]
        print(f"Publishing BodyData: {BodyData}")
        client_sendBodyData.publish("pos", str(BodyData))
        time.sleep(0.5)  # Adjust publishing frequency as needed

# Initialize MQTT clients
client_chooseExercise = mqtt.Client()
client_chooseMusic = mqtt.Client()
client_sendBodyData = mqtt.Client()

# Assign callbacks
client_chooseExercise.on_message = on_exercise_message
client_chooseMusic.on_message = on_music_message

# Connect to the broker
client_chooseExercise.connect(broker, port, 60)
client_chooseMusic.connect(broker, port, 60)
client_sendBodyData.connect(broker, port, 60)

# Subscribe to topics
client_chooseExercise.subscribe("exercise")
client_chooseMusic.subscribe("music")

# Start MQTT client loops in separate threads
exercise_thread = threading.Thread(target=client_chooseExercise.loop_forever)
music_thread = threading.Thread(target=client_chooseMusic.loop_forever)
publish_thread = threading.Thread(target=publish_body_data, daemon=True)

exercise_thread.start()
music_thread.start()
publish_thread.start()
