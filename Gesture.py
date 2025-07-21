import serial
import speech_recognition as sr
import cv2
import mediapipe as mp
import time

# Initialize Serial Communication to Transmitter Arduino (via HC-12)
SERIAL_PORT = "COM15"  # Update this with the transmitter Arduino's COM port
BAUD_RATE = 9600
arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Allow Arduino to initialize
print(f"✅ Connected to Arduino on {SERIAL_PORT}")

# Initialize MediaPipe for Hand Gesture Recognition
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands()

# Initialize Speech Recognition for Voice Command
recognizer = sr.Recognizer()

# Define Gesture Command Mappings
GESTURE_COMMANDS = {
    "open_palm": "turn on light",
    "closed_palm": "turn off light"
}

# Send command to Arduino
def send_to_arduino(command):
    arduino.write(f"{command}\n".encode())  # Send command as string followed by newline
    print(f"📤 Sent to Arduino: {command}")

# Capture voice command
def capture_voice_command():
    with sr.Microphone() as source:
        print("🎤 Say a command...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            print(f"✅ Recognized Command: {command}")
            send_to_arduino(command)  # Send command to Arduino
            return command
        except sr.UnknownValueError:
            print("❌ Could not understand the command.")
        except sr.RequestError:
            print("❌ Speech Recognition service error.")

# Open Webcam for Gesture Recognition
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Camera not found!")
    exit()

print("🎭 Gesture Recognition Ready | 🎤 Press 'V' for Voice Command | Press 'Q' to Quit")

last_command_time = time.time()
command_interval = 5  # Time interval in seconds

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to capture image")
        break

    # Convert frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process frame with MediaPipe for gesture detection
    results = hands.process(rgb_frame)

    current_time = time.time()
    if current_time - last_command_time >= command_interval:
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Check for gestures
                thumb_tip = hand_landmarks.landmark[4]
                index_tip = hand_landmarks.landmark[8]
                if thumb_tip.y > index_tip.y:  # Closed Palm Gesture
                    send_to_arduino("turn off light")
                else:  # Open Palm Gesture
                    send_to_arduino("turn on light")
        last_command_time = current_time

    # Show frame
    cv2.imshow("Hand Gesture Recognition", frame)

    # Capture voice command when 'V' is pressed
    if cv2.waitKey(1) & 0xFF == ord('v'):
        capture_voice_command()

    # Quit when 'Q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()