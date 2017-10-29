# -*- coding: utf-8 -*-

import os
import io
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug import secure_filename
#from os import makedirs

from google.cloud import vision
from google.cloud.vision import types

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

#RESULTS_DIR = 'jsons'
#makedirs(RESULTS_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def detect_labels(file):
    """Detects labels in the file."""
    content = file.read()

    image = types.Image(content=content)

    client = vision.ImageAnnotatorClient()
    response = client.label_detection(image=image)
    labels = response.label_annotations

    return labels

def detect_faces(file):
    # coding:utf-8
    """Detects faces in an image."""
    content = file.read()

    client = vision.ImageAnnotatorClient()

    # [START migration_face_detection]
    # [START migration_image_file]
    image = types.Image(content=content)
    # [END migration_image_file]

    response = client.face_detection(image=image)
    faces = response.face_annotations

    # Names of likelihood from google.cloud.vision.enums
    likelihood_name = ('UNKNOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE',
                       'LIKELY', 'VERY_LIKELY')
    print('Faces:')

    for face in faces:
        print('anger: {}'.format(likelihood_name[face.anger_likelihood]))
        print('joy: {}'.format(likelihood_name[face.joy_likelihood]))
        print('surprise: {}'.format(likelihood_name[face.surprise_likelihood]))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in face.bounding_poly.vertices])

        print('face bounds: {}'.format(','.join(vertices)))

    return faces

def qrmaker(code):
    '''https://teratail.com/questions/84507'''

    qr_img = qr.make(str(code))

    buf = BytesIO()
    qr_img.save(buf, format="png")

    qr_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")

    qr_b64data = "data:image/png;base64,{}".format(qr_b64str)

    return qr_b64data


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':

        file = request.files['file']
        type = request.form['type']
        if file and allowed_file(file.filename):
            image_filenames = request.files['file'].filename

            if type == 'label detection':
                rtn = detect_labels(file)
                rtn_page = 'result.html'
            elif type == 'face detection':
                rtn = detect_faces(file)
            elif type == 'web':
                rtn = detect_labels(file)
                print(type)

        else:
            rtn = 'File extension is invalid!!'

        return render_template('result.html', type=type, results=rtn, filename=image_filenames)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
