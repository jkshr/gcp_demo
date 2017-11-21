# -*- coding: utf-8 -*-

import os
import sys
import io
from flask import Flask, request, url_for, send_from_directory, render_template
from werkzeug import secure_filename
from base64 import b64encode
from os.path import join, basename
import json
import requests

# 文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'
UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)


def allowed_file(filename):
    """拡張子チェック

    :filename: ファイル名
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def make_image_data_list(filename, request_type):
    """リクエストの作成

    :filename: ファイル名
    :request_type: APIのタイプ
    :return: リクエストで送信するデータ
    """
    print("make_image_data_list")
    if request_type == 'TEXT_DETECTION':
        max_results = 1
    else:
        max_results = 10

    img_requests = []
#    ctxt = b64encode(image_file.read()).decode()
    with open(os.path.join(UPLOAD_FOLDER, filename), "rb") as file:
        image = file.read()
        ctxt = b64encode(image).decode()

#    print(ctxt)
    if request_type == 'LANDMARK_DETECTION' or request_type == 'LOGO_DETECTION':
        img_requests.append({
                'image': {'content': ctxt},
                'features': [{
#                    'type': 'LABEL_DETECTION',
                    'type': request_type,
#                    'maxResults': max_results
                }]
        })
    else:
        img_requests.append({
                'image': {'content': ctxt},
                'features': [{
#                    'type': 'LABEL_DETECTION',
                    'type': request_type,
                    'maxResults': max_results
                }]
        })
    print(img_requests)
    return img_requests


def send_file_to_cloudvision(api_key, filename, request_type):
    """リクエストの送信

    :api_key: APIキー
    :filename: ファイル名
    :request_type: APIのタイプ
    :return: リクエストで送信するデータ
    """
    imgdict = make_image_data_list(filename, request_type)
    response = requests.post(ENDPOINT_URL,
                             data=json.dumps({"requests": imgdict}).encode(),
                             params={'key': api_key},
                             headers={'Content-Type': 'application/json'})
#    print(response)
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        print("kick")
#        api_key = API_KEY
        api_key = request.form['key']
#        print(api_key)

        image_file = request.files['file']
        print(image_file)

        rtn = filename = ""
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(UPLOAD_FOLDER, filename))

            request_type = request.form['type']

#        *image_file = argv[2:]
            if not api_key or not filename:
                print("""
                    適切にAPIキーとイメージファイルを指定してください。

                    $ python cvapi.py api_key image.jpg""")
            else:
                response = send_file_to_cloudvision(api_key, filename, request_type)
                if response.status_code != 200 or response.json().get('error'):
                    print(response.text)
                else:
                    print(type(response.json()))
                    print(len(response.json()))
                    print(response.json())
                    # マッチしなかった場合は、responseの中身がない
                    if len(response.json()['responses'][0]) == 0:
                        return render_template('result_unmatch.html', type=request_type,\
                            results=None, filepath=os.path.join(UPLOAD_FOLDER, filename))

                    # レスポンス表示
                    print("{}".format(json.dumps(response.json()['responses'], indent=4)))

                    if request_type == 'LABEL_DETECTION':
                        rtn = response.json()['responses'][0]['labelAnnotations']
                        print(type(rtn))
                        print(rtn)
                    elif request_type == 'TEXT_DETECTION':
                        rtn = [
                            {'description':response.json()['responses'][0]['textAnnotations'][0]['description'],
                             'locale':response.json()['responses'][0]['textAnnotations'][0]['locale']}]
                        print(rtn)
                        return render_template('result_text.html', type=request_type,\
                            results=rtn, filepath=os.path.join(UPLOAD_FOLDER, filename))
                    elif request_type == 'FACE_DETECTION':
                        rtn = [
                            {'label':'Joy', 'value':response.json()['responses'][0]['faceAnnotations'][0]['joyLikelihood']},
                            {'label':'Sorrow', 'value':response.json()['responses'][0]['faceAnnotations'][0]['sorrowLikelihood']},
                            {'label':'Anger', 'value':response.json()['responses'][0]['faceAnnotations'][0]['angerLikelihood']},
                            {'label':'Surprise', 'value':response.json()['responses'][0]['faceAnnotations'][0]['surpriseLikelihood']}]
                        print(rtn)
                        return render_template('result_face.html', type=request_type,\
                            results=rtn, filepath=os.path.join(UPLOAD_FOLDER, filename))
#                    elif request_type == 'LANDMARK_DETECTION':
#                        rtn = response.json()['responses'][0]['landmarkAnnotations']
#                        return render_template('result_landmark.html', type=request_type,\
#                            results=rtn, filepath=os.path.join(UPLOAD_FOLDER, filename))
                    elif request_type == 'LOGO_DETECTION':
                        rtn = response.json()['responses'][0]['logoAnnotations']
                        print(rtn)
                    elif request_type == 'SAFE_SEARCH_DETECTION':
                        rtn = [
                            {'label':'Adult', 'value':response.json()['responses'][0]['safeSearchAnnotation']['adult']},
                            {'label':'Spoof', 'value':response.json()['responses'][0]['safeSearchAnnotation']['spoof']},
                            {'label':'Medical', 'value':response.json()['responses'][0]['safeSearchAnnotation']['medical']},
                            {'label':'Violence', 'value':response.json()['responses'][0]['safeSearchAnnotation']['violence']}]
                        print(rtn)
                        return render_template('result_face.html', type=request_type,\
                            results=rtn, filepath=os.path.join(UPLOAD_FOLDER, filename))
                    elif request_type == 'WEB_DETECTION':
                        rtn = response.json()['responses'][0]['safeSearchAnnotation']
                        return render_template('result_safesearch.html', type=request_type,\
                            results=rtn, filepath=os.path.join(UPLOAD_FOLDER, filename))

        print(rtn)
        return render_template('result_label.html', type=request_type, results=rtn,\
#            path=UPLOAD_FOLDER, filename=filename, cwd=os.getcwd())
            filepath=os.path.join(UPLOAD_FOLDER, filename))

if __name__ == '__main__':
    app.run(debug=True, port=8000)
