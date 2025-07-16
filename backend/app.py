from flask import Flask, jsonify, request
from flask_cors import CORS
import uuid
import random

app = Flask(__name__)
CORS(app)

rooms = {}

ROLES = ["mafia", "detective", "doctor", "villager"]

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
        'roles': {},
        'alive': set(),
        'phase': 'waiting',  # waiting, night, day, ended
        'actions': {},
        'last_result': {},
        'winner': None
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
    player_name = request.args.get('player_name')
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    # Only send role to the player
    role = room['roles'].get(player_name)
    return jsonify({
        'players': room['players'],
        'min_players': room['min_players'],
        'max_players': room['max_players'],
        'started': room['started'],
        'votes': room['votes'],
        'phase': room['phase'],
        'alive': list(room['alive']),
        'role': role,
        'last_result': room['last_result'],
        'winner': room['winner']
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
        assign_roles(room)
        room['alive'] = set(room['players'])
        room['phase'] = 'night'
        room['actions'] = {}
        room['last_result'] = {}
        room['winner'] = None
    return jsonify({'started': room['started'], 'votes': room['votes']})

def assign_roles(room):
    players = room['players'][:]
    random.shuffle(players)
    n = len(players)
    mafia_count = max(1, n // 4)
    roles = ["mafia"] * mafia_count + ["detective", "doctor"] + ["villager"] * (n - mafia_count - 2)
    random.shuffle(roles)
    room['roles'] = {p: r for p, r in zip(players, roles)}

@app.route('/api/night_action', methods=['POST'])
def night_action():
    data = request.get_json()
    room_id = data['room_id']
    player_name = data['player_name']
    target = data['target']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if room['phase'] != 'night' or player_name not in room['alive']:
        return jsonify({'error': 'Not allowed'}), 400
    role = room['roles'].get(player_name)
    if role not in ["mafia", "doctor", "detective"]:
        return jsonify({'error': 'Not allowed'}), 400
    room['actions'][(role, player_name)] = target
    # Check if all actions are in
    mafia = [p for p in room['alive'] if room['roles'][p] == "mafia"]
    doctor = [p for p in room['alive'] if room['roles'][p] == "doctor"]
    detective = [p for p in room['alive'] if room['roles'][p] == "detective"]
    mafia_done = all(("mafia", m) in room['actions'] for m in mafia)
    doctor_done = all(("doctor", d) in room['actions'] for d in doctor)
    detective_done = all(("detective", d) in room['actions'] for d in detective)
    if mafia_done and doctor_done and detective_done:
        resolve_night(room)
    return jsonify({'success': True})

def resolve_night(room):
    mafia_targets = [room['actions'][("mafia", m)] for m in room['roles'] if ("mafia", m) in room['actions']]
    mafia_target = max(set(mafia_targets), key=mafia_targets.count) if mafia_targets else None
    doctor_targets = [room['actions'][("doctor", d)] for d in room['roles'] if ("doctor", d) in room['actions']]
    doctor_save = doctor_targets[0] if doctor_targets else None
    detective_targets = [room['actions'][("detective", d)] for d in room['roles'] if ("detective", d) in room['actions']]
    detective_result = None
    if detective_targets:
        target = detective_targets[0]
        detective_result = {"target": target, "role": room['roles'].get(target)}
    killed = None
    if mafia_target and mafia_target != doctor_save and mafia_target in room['alive']:
        room['alive'].remove(mafia_target)
        killed = mafia_target
    room['last_result'] = {
        'killed': killed,
        'saved': doctor_save if doctor_save == mafia_target else None,
        'investigated': detective_result
    }
    room['phase'] = 'day'
    room['actions'] = {}
    check_winner(room)

@app.route('/api/day_vote', methods=['POST'])
def day_vote():
    data = request.get_json()
    room_id = data['room_id']
    player_name = data['player_name']
    target = data['target']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if room['phase'] != 'day' or player_name not in room['alive']:
        return jsonify({'error': 'Not allowed'}), 400
    room['actions'][player_name] = target
    # If all alive have voted, resolve
    if len(room['actions']) == len(room['alive']):
        resolve_day(room)
    return jsonify({'success': True})

def resolve_day(room):
    votes = list(room['actions'].values())
    if votes:
        voted_out = max(set(votes), key=votes.count)
        if voted_out in room['alive']:
            room['alive'].remove(voted_out)
            room['last_result'] = {'voted_out': voted_out}
    room['phase'] = 'night'
    room['actions'] = {}
    check_winner(room)

def check_winner(room):
    mafia = [p for p in room['alive'] if room['roles'][p] == 'mafia']
    others = [p for p in room['alive'] if room['roles'][p] != 'mafia']
    if not mafia:
        room['phase'] = 'ended'
        room['winner'] = 'villagers'
    elif len(mafia) >= len(others):
        room['phase'] = 'ended'
        room['winner'] = 'mafia'

if __name__ == '__main__':
    app.run(debug=True)
