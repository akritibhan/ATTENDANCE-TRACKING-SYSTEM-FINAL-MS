
import email
import imp
from flask import Flask, Response, redirect, render_template, request, redirect, session
import mysql.connector
import os
import cv2
import face_recognition
import numpy as np
from datetime import datetime


app = Flask(__name__)
app.secret_key = os.urandom(24)

conn = mysql.connector.connect(
    host="remotemysql.com", user="LiaEFUqIZe", password="1MXaxpeEbc", database="LiaEFUqIZe")
cursor = conn.cursor()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/admin')
def admin():
    if 'sno' in session:
        return render_template('admin.html')
    else:
        return redirect('/register')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/attendance')
def attendance():
    return render_template('attendance.html')


camera = cv2.VideoCapture(0)

path = 'face_images'
images = []
known_face_names = []
myList = os.listdir(path)

for i in myList:
    currentImg = cv2.imread(f'{path}/{i}')
    images.append(currentImg)
    known_face_names.append(os.path.splitext(i)[0])


def markAttendance(roll):
    with open('Attendance_Sheet.csv', 'r+') as f:
        myDataList = f.readlines()
        rollList = []
        for line in myDataList:
            entry = line.split(',')
            rollList.append(entry[0])
        if roll not in rollList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{roll},{dtString}')


def encodings(images):
    encoding_list = []
    for i in images:
        i = cv2.cvtColor(i, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(i)[0]
        encoding_list.append(encode)
    return encoding_list


known_face_encodings = encodings(images)

face_locations = []
face_encodings = []
face_names = []
process_this_frame = True


def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
               
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)
                name = "Unknown"

                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                face_names.append(name)

   
            for (top, right, bottom, left), name in zip(face_locations, face_names):
               
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

       
                cv2.rectangle(frame, (left, top),
                              (right, bottom), (0, 0, 255), 2)

        
                cv2.rectangle(frame, (left, bottom - 35),
                              (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6),
                            font, 1.0, (255, 255, 255), 1)
                markAttendance(name)
               

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('email')
    pin = request.form.get('pin')

    cursor.execute(
        """SELECT * FROM `users` WHERE `email` LIKE '{}' AND `pin` LIKE '{}' """.format(email, pin))
    users = cursor.fetchall()

    if len(users) > 0:
        session['sno'] = users[0][0]
        return redirect('/admin')
    else:
        return redirect('/register')


@app.route('/insert_data', methods=['POST'])
def insert_data():
    name = request.form.get('name')
    email = request.form.get('email')
    pin = request.form.get('pin')

    cursor.execute("""INSERT INTO `users` (`sno`,`name`,`email`,`pin`) VALUES (NULL,'{}','{}','{}') """.format(
        name, email, pin))
    conn.commit()

    cursor.execute(
        """SELECT * FROM `users` WHERE `email` LIKE '{}' """.format(email))
    myuser = cursor.fetchall()
    session['sno'] = myuser[0][0]

    return redirect('/admin')


@app.route('/logout')
def logout():
    session.pop('sno')
    return redirect('/register')

@app.route('/excel')
def open_excel():
    return os.startfile('Attendance_Sheet.csv')



if __name__ == "__main__":
    app.run(debug=True)
