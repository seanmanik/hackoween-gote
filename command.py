import subprocess

from flask import Flask, request, jsonify
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/feedback', methods=['GET'])
def get_feedback():
    # if request.method == 'GET':
    #     # Handle GET request
    #     data = {"message": "This is a GET request."}
    # elif request.method == 'POST':
    #     # Handle POST request
    #     data = request.json
    command = "near view nycsuggestions1.testnet get_messages"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return(result.stdout)

@app.route('/feedback', methods=['POST'])
def add_feedback():

    data = request.json

    command = '''near call nycsuggestions1.testnet add_message '{"text": "''' + data["text"] + '''"}' --accountId nycsuggestions1.testnet'''
    print(command)
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout



# params = location: string, text: string
@app.route('/upvote', methods=['POST'])
def upvote():
    data = request.json
    command = '''near call postednotes.testnet upvote '{"location": "''' + data["location"] + '''", "text": "''' + data["text"] + '''"}' --accountId pointstracker.testnet'''
    print(command)
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout


# params = points: int, user: string
@app.route('/redeem_points', methods=['POST'])
def redeem_points():
    data = request.json
    command = '''near call pointstracker.testnet redeem_points '{"points": ''' + str(data["points"]) + '''}' --accountId pointstracker.testnet'''
    print(command)
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout

# params = location: string, text: string, user: string
@app.route('/leave_note', methods=['POST'])
def leave_note():
    data = request.json
    command = '''near call postednotes.testnet leave_note '{"location": "''' + data["location"] + '''", "text": "''' + data["text"] + '''", "user": "''' + data["user"] + '''"}' --accountId pointstracker.testnet'''
    print(command)
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)


