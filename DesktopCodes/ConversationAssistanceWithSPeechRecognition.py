import threading

import os
import subprocess
import pyttsx3
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play
import tempfile
import requests  # for fetching random facts
import pyjokes  # for random jokes
import re
import google.generativeai as genai

import paho.mqtt.client as mqtt
import time

# MQTT broker details
broker = "test.mosquitto.org"  # Free public MQTT broker
port = 1883
topic = "test/topic"

# Create a client instance
client2 = mqtt.Client()
# Connect to the broker
client2.connect(broker, port, 60)

def speak(text):
    text = "ah..." + text
    """Convert text to speech and speak it."""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 95)  # slower rate 95
    engine.setProperty('volume', 1)  # full volume
    engine.save_to_file(text, "output.wav")  # Save to a temporary file
    engine.runAndWait()

    # Step 2: Modify pitch using PyDub
    sound = AudioSegment.from_wav("output.wav")

    # Increase pitch (for example, by 150%)
    octaves = 0.8  # A higher value increases the pitch more
    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
    pitched_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    pitched_sound = pitched_sound.set_frame_rate(44100)  # 44100

    # Step 3: Play the modified sound
    play(pitched_sound)

    # Clean up the temporary file
    os.remove("output.wav")

def listen():
    """Capture audio input from the user and return it as text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I didn't catch that."
        except sr.RequestError as e:
            return f"Speech Recognition service error: {e}"

def search_web(query):
    """Search the web using the default browser."""
    speak(f"Searching the web for {query}.")
    if os.name == "nt":
        subprocess.run(["start", "https://www.google.com/search?q=" + query], shell=True)
    else:
        subprocess.run(["xdg-open", "https://www.google.com/search?q=" + query])

def get_random_fact():
    """Fetch a random fact from an API."""
    response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en")
    fact_data = response.json()
    return fact_data.get('text', 'I could not find a fact at the moment.')

def get_random_joke():
    """Fetch a random joke using pyjokes."""
    return pyjokes.get_joke()

def gemini(query):
    response = model.generate_content(query+" make your response breif")
    print(response.text)
    return response.text

genai.configure(api_key="AIzaSyA3t3kWXZHbTRzXRfZE_ALhL1QPulE2Lwc")
model = genai.GenerativeModel("gemini-1.5-flash")
def timer(num, type):
    if "hour" in type:
        num *= 60**2
    elif "minute" in type:
        num *= 60
    for i in range(num):
        half = num // 2
        time.sleep(1)
        print(f"Timer: {i+1} seconds")
        if i == half:
            speak("Halfway there!")
    speak("Time is UP Buddy!")
    return "Over"

def main():
    global prev
    while True:
        user_input = listen().lower()
        print(f"You said: {user_input}")

        if (prev == 0) and (("mickey" in user_input) or ("miki" in user_input) or ("mick" in user_input) or ('key' in user_input) or ("nikki" in user_input)):
            User_query = user_input.replace("mickey", "")
            client2.publish("face", "awake")
        elif (prev == 1):
            User_query = user_input
        else:
            continue

        if User_query == "hi " or User_query == "hey " or User_query == "hello ":
            print("nothing said", prev, User_query)
            prev = 1
            continue

        if "how are you" in User_query:
            speak("I am great! I get happy whenever I see you hehe!")

        elif "exercise" in User_query:
            speak("Ow that is great to hear! Let's go have some fun.")

        elif "tell me a joke" in User_query:
            joke = get_random_joke()
            speak(joke)

        elif ("tell me a fact" in User_query) or ("fact" in User_query) or ("effect" in User_query):
            fact = get_random_fact()
            speak(fact)

        elif ("countdown" in User_query) or ("count" in User_query) or ("timer" in User_query):
            find_num = re.findall(r'\d+', User_query)
            num = int(find_num[len(find_num)-1]) if find_num else 0
            while ("second" not in User_query and "minute" not in User_query and "hour" not in User_query):
                speak(f"Could you kindly pick if you need a timer of {str(num)}... in seconds, minutes or hours PLEASE??")
                User_query = listen().lower()
                print(User_query)
            speak("Okay! Starting the timer.")
            # Start the timer in a new thread
            timer_thread = threading.Thread(target=timer, args=(num, User_query))
            timer_thread.start()

        elif ("bye bye" in User_query) or ("quit" in User_query) or ("bye-bye" in User_query):
            speak("Goodbye! Have a great day!")
            break
        else:
            speak(gemini(User_query))
        prev = 0
        client2.publish("face", "sleep")
        print(f"Message sent: sleep")

if __name__ == "__main__":
    prev = 0
    main()
