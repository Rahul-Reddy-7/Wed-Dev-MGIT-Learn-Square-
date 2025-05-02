import cv2
import face_recognition
import os
import numpy as np
import sqlite3
from datetime import datetime

# === Load Known Faces ===
print("[INFO] Loading known faces...")
known_face_encodings = []
known_face_names = []

known_faces_dir = "known_faces"
for filename in os.listdir(known_faces_dir):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        name = os.path.splitext(filename)[0]
        path = os.path.join(known_faces_dir, filename)

        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
            known_face_names.append(name)
            print(f"[INFO] Loaded encoding for: {name}")
        else:
            print(f"[WARNING] No face found in {filename}, skipping.")

if not known_face_encodings:
    print("[ERROR] No known faces loaded. Exiting.")
    exit()

# === SQLite Database Setup ===
db_path = "attendance.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL
    )
''')
conn.commit()
conn.close()

# === Attendance Tracking Function ===
def mark_attendance(name):
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    time_string = now.strftime('%H:%M:%S')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the person has already been marked present today
    cursor.execute("SELECT * FROM attendance WHERE name=? AND date=?", (name, date_string))
    result = cursor.fetchone()

    if result is None:
        cursor.execute("INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)",
                       (name, date_string, time_string))
        conn.commit()
        print(f"[INFO] Marked present: {name} on {date_string} at {time_string}")
    else:
        print(f"[DEBUG] Already marked: {name} on {date_string}")

    conn.close()

# === Start Webcam ===
print("[INFO] Starting webcam. Press 'q' to quit.")
video_capture = cv2.VideoCapture(0)

if not video_capture.isOpened():
    print("[ERROR] Cannot access webcam.")
    exit()

try:
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("[ERROR] Failed to read frame.")
            break

        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        face_names = []

        print(f"[DEBUG] Detected {len(face_encodings)} face(s).")

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            name = "Unknown"

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

            face_names.append(name)
            if name != "Unknown":
                mark_attendance(name)

        # Draw results on frame
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 1)

        cv2.imshow("Face Recognition Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Exiting...")
            break

finally:
    video_capture.release()
    cv2.destroyAllWindows()
