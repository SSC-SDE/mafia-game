from flask import Flask, jsonify, request
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

rooms = {}

@app.route('/api/hello')
def hello():
    return jsonify({'message': 'Hello from Flask backend!'})

@app.route('/api/create_room', methods=['POST'])
def create_room():
    data = request.get_json()
    min_players = data.get('min_players', 5)
    max_players = data.get('max_players', 10)
    room_id = str(uuid.uuid4())[:8]
    rooms[room_id] = {
        'players': [],
        'min_players': min_players,
        'max_players': max_players,
        'started': False,
        'votes': {},
    }
    return jsonify({'room_id': room_id})

@app.route('/api/join_room', methods=['POST'])
def join_room():
    data = request.get_json()
    room_id = data['room_id']
    player_name = data['player_name']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if len(room['players']) >= room['max_players']:
        return jsonify({'error': 'Room is full'}), 400
    if player_name in room['players']:
        return jsonify({'error': 'Name already taken'}), 400
    room['players'].append(player_name)
    return jsonify({'success': True, 'players': room['players']})

@app.route('/api/room_status', methods=['GET'])
def room_status():
    room_id = request.args.get('room_id')
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    return jsonify({
        'players': room['players'],
        'min_players': room['min_players'],
        'max_players': room['max_players'],
        'started': room['started'],
        'votes': room['votes'],
    })

@app.route('/api/vote_start', methods=['POST'])
def vote_start():
    data = request.get_json()
    room_id = data['room_id']
    player_name = data['player_name']
    vote = data['vote']  # True/False
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if player_name not in room['players']:
        return jsonify({'error': 'Player not in room'}), 400
    room['votes'][player_name] = vote
    # If all players have voted True and min_players reached, start game
    if (len(room['players']) >= room['min_players'] and
        all(room['votes'].get(p) for p in room['players'])):
        room['started'] = True
    return jsonify({'started': room['started'], 'votes': room['votes']})

if __name__ == '__main__':
    app.run(debug=True)
