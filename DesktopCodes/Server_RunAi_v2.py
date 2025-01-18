import socket
import pickle
import struct ## new
##
import cv2
import mediapipe as mp
import numpy as np
##
import paho.mqtt.client as mqtt
import time
import pandas as pd


# File path to store data
file_path = "data.csv"

# Ensure the CSV file exists and has the correct structure
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    # Create a DataFrame with the required structure
    df = pd.DataFrame(columns=["BodyData"])
    df.loc[0] = [0]  # Initialize the first row with default values
    df.to_csv(file_path, index=False)

### For Socket
HOST=''
PORT=8485

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print('Socket created')

s.bind((HOST,PORT))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

conn,addr=s.accept()

data = b""
payload_size = struct.calcsize(">L")
print("payload_size: {}".format(payload_size))
###########################################################
###########################################################

### For mediapie
# Initialize MediaPipe Pose, and Drawing modules
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Initialize MediaPipe Pose models
Text_to_Display = ''

numr,numl = 0,3
to_push_data = 0



def checkPositions(arm, n):
    ## Position 1 ~--|--~
    if abs(arm[0][1] - arm[1][1]) < 0.15 and abs(arm[0][0] - arm[1][0]) > 0.15:
        n = 0

    ## Position 2 /--|--\
    elif (arm[1][1] - arm[0][1]) > 0.2:
        n = 1

    ## Position 3 \--|--/
    elif (arm[0][1] - arm[1][1]) > 0.2:
        n = 2
    return n


with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while True:
        while len(data) < payload_size:
            # print("Recv: {}".format(len(data)))
            data += conn.recv(4096)

        # print("Done Recv: {}".format(len(data)))
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        # print("msg_size: {}".format(msg_size))
        while len(data) < msg_size:
            data += conn.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        # frame = cv2.resize(frame, (640, 480))  # Resize to match the client resolution



        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process pose detection
        results_pose = pose.process(rgb_frame)

        if results_pose.pose_landmarks:
            # Draw pose landmarks
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=results_pose.pose_landmarks,
                connections=mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)
            )

            ## Right Arm
            right_hand = results_pose.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
            rhx, rhy = 1 - right_hand.x, 1 - right_hand.y

            right_elbow = results_pose.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]
            rex, rey = 1 - right_elbow.x, 1 - right_elbow.y

            right_shoulder = results_pose.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            rsx, rsy = 1 - right_shoulder.x, 1 - right_shoulder.y

            ## Left Arm
            left_hand = results_pose.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
            lhx, lhy = 1 - left_hand.x, 1 - left_hand.y

            left_elbow = results_pose.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW]
            lex, ley = 1 - left_elbow.x, 1 - left_elbow.y

            left_shoulder = results_pose.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            lsx, lsy = 1 - left_shoulder.x, 1 - left_shoulder.y

            right_arm = np.round(np.array([[rhx, rhy], [rex, rey], [rsx, rsy]]),3)
            left_arm = np.round(np.array([[lhx, lhy], [lex, ley], [lsx, lsy]]),3)

            position = ['R-Hands flat', 'R-Resting', 'R-Hands up', 'L-Hands flat', 'L-Resting', 'L-Hands up']

            ## Check Right Hand
            right_pos = checkPositions(right_arm, numr)
            numr = right_pos
            left_pos = 3 + checkPositions(left_arm, numl)
            numl = left_pos - 3
            Text_to_Display = position[right_pos] + " | " + position[left_pos]

            BodyPoseArr = ''
            for i in range(6):
                if (i == right_pos) or (i == left_pos):
                    BodyPoseArr += '1'
                else:
                    BodyPoseArr += '0'
            df.loc[0, "BodyData"] = BodyPoseArr
            df.to_csv(file_path, index=False)
            print(f"Message sent: {BodyPoseArr}")

            cv2.putText(frame, Text_to_Display,
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)

            cv2.putText(frame, str(right_arm[0][1])+" "+str(right_arm[1][1])+" "+str(right_arm[2][1]), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(0, 0, 0), 2, cv2.LINE_AA)

        # cv2.namedWindow('ImageWindow', cv2.WINDOW_NORMAL)  # Allow resizing of the window
        # cv2.resizeWindow('ImageWindow', 800, 600)  # Set the display size to 800x600
        cv2.imshow('ImageWindow',frame)
        cv2.waitKey(1)