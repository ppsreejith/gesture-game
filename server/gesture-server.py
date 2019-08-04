import time

import cv2
from flask import Flask, request, g, Response
import uuid
import numpy as np
import tensorflow as tf
from werkzeug.utils import secure_filename

app = Flask(__name__)

current_total_players = 0
current_uuid = ""

user_score_dict = {}

matches = {'ABC': {
    "vivek": {
        "state": -1
    },
    "sam": {
        "state": -1
    }
}}


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/login", methods=['GET'])
def login():
    username = request.args['username']
    if username in user_score_dict:
        return username, user_score_dict[username]
    else:
        user_score_dict[username] = 0
    print(user_score_dict)
    return_result = str(username + ":" + str(user_score_dict[username]))
    return return_result


@app.route("/pair", methods=['GET'])
def pair():
    global current_total_players, current_uuid
    if current_total_players % 2 == 0:
        current_uuid = uuid.uuid4().hex
        current_total_players = current_total_players + 1
        return current_uuid
    else:
        current_total_players = current_total_players + 1
        return current_uuid


def isReady(match_id, player1, player2):
    global matches
    current_match = matches.get(match_id)
    player_1_dict = current_match[player1]
    player_2_dict = current_match[player2]
    if (player_1_dict['state'] == player_2_dict['state']) and (player_1_dict['state'] == 'waiting'):
        return "True"
    elif(player_1_dict['state'] == player_2_dict['state']) and (player_1_dict['state'] == 'sent_images'):
        return "False"


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        filename = secure_filename(f.filename)
        f.save(filename)
        print(infer(filename))
        return 'file uploaded successfully'


# @app.route("/infer", methods=['GET'])
def infer(filename):
    # Load TFLite model and allocate tensors.
    interpreter = tf.contrib.lite.Interpreter(model_path="converted_model.tflite")
    interpreter.allocate_tensors()

    # Get input and output tensors.
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Test model on random input data.
    input_shape = input_details[0]['shape']
    # change the following line to feed into your own data.
    # input_data = np.array(np.random.random_sample(input_shape), dtype=np.float32)
    input_data = cv2.imread(filename)
    interpreter.set_tensor(input_details[0]['index'], input_data)

    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data


@app.route("/sync", methods=['GET'])
def sync():
    global matches
    match_id = request.args['match_id']
    username = request.args['username']
    state = request.args['state']
    matches[match_id][username]["state"] = state
    return isReady(match_id, *list(matches[match_id].keys()))


@app.route("/check", methods=['GET'])
def check():
    match_id = request.args['match_id']
    batting = request.args['batting']
    player1_number = request.args['player1']
    player2_number = request.args['player2']
    if player1_number == player2_number:
        return


##out or run send


@app.route("/endgame", methods=['GET'])
def end_game():
    global current_total_players
    current_total_players -= 1
    return str(current_total_players)


@app.route("/getcurrentplayers", methods=['GET'])
def get_current_total_players():
    global current_total_players
    return str(current_total_players)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, threaded=False, processes=1)
