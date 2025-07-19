from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import uuid
import random
import redis
import os
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

REDIS_URL = os.environ.get("UPSTASH_REDIS_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN")
redis_client = redis.Redis.from_url(
    REDIS_URL,
    password=REDIS_TOKEN,
    decode_responses=True
)

ROLES = ["mafia", "detective", "doctor", "villager"]

# Helper functions for Redis

def get_room(room_id):
    data = redis_client.get(f"room:{room_id}")
    return json.loads(data) if data else None

def save_room(room_id, room):
    redis_client.set(f"room:{room_id}", json.dumps(room))

@app.route('/api/hello')
def hello():
    return jsonify({'message': 'Hello from Flask backend!'})

@app.route('/api/create_room', methods=['POST'])
def create_room():
    data = request.get_json()
    min_players = data.get('min_players', 5)
    max_players = data.get('max_players', 10)
    room_id = str(uuid.uuid4())[:8]
    room = {
        'room_id': room_id,  # Add this line
        'players': [],
        'min_players': min_players,
        'max_players': max_players,
        'started': False,
        'votes': {},
        'roles': {},
        'alive': [],
        'phase': 'waiting',
        'actions': {},
        'last_result': {},
        'winner': None
    }
    save_room(room_id, room)
    return jsonify({'room_id': room_id})

@app.route('/api/join_room', methods=['POST'])
def join_room():
    data = request.get_json()
    room_id = data['room_id']
    player_name = data['player_name']
    room = get_room(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    if player_name != "god":
        if len(room['players']) >= room['max_players']:
            return jsonify({'error': 'Room is full'}), 400
        if player_name in room['players']:
            return jsonify({'error': 'Name already taken'}), 400
        room['players'].append(player_name)
    # god can join any room, but is not added to players list
    save_room(room_id, room)
    return jsonify({'success': True, 'players': room['players']})

@app.route('/api/room_status', methods=['GET'])
def room_status():
    room_id = request.args.get('room_id')
    player_name = request.args.get('player_name')
    room = get_room(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    if player_name == "god":
        # god sees everything, but add a summary of all player roles for convenience
        god_view = dict(room)
        god_view['player_roles'] = [{ 'name': p, 'role': r } for p, r in room.get('roles', {}).items()]
        return jsonify(god_view)
    role = room['roles'].get(player_name)
    return jsonify({
        'players': room['players'],
        'min_players': room['min_players'],
        'max_players': room['max_players'],
        'started': room['started'],
        'votes': room['votes'],
        'phase': room['phase'],
        'alive': room['alive'],
        'role': role,
        'last_result': room['last_result'],
        'winner': room['winner']
    })

@app.route('/api/vote_start', methods=['POST'])
def vote_start():
    data = request.get_json()
    room_id = data['room_id']
    player_name = data['player_name']
    vote = data['vote']
    room = get_room(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    if player_name not in room['players']:
        return jsonify({'error': 'Player not in room'}), 400
    room['votes'][player_name] = vote
    if (len(room['players']) >= room['min_players'] and
        all(room['votes'].get(p) for p in room['players'])):
        room['started'] = True
        assign_roles(room)
        room['alive'] = list(room['players'])
        room['phase'] = 'night'
        room['actions'] = {}
        room['last_result'] = {}
        room['winner'] = None
    save_room(room_id, room)
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
    room = get_room(room_id)
    if not room or room['phase'] != 'night' or player_name not in room['alive']:
        return jsonify({'error': 'Not allowed'}), 400
    role = room['roles'].get(player_name)
    if role not in ["mafia", "doctor", "detective"]:
        return jsonify({'error': 'Not allowed'}), 400
    # Use string keys instead of tuple keys
    room['actions'][f"{role}:{player_name}"] = target
    mafia = [p for p in room['alive'] if room['roles'][p] == "mafia"]
    doctor = [p for p in room['alive'] if room['roles'][p] == "doctor"]
    detective = [p for p in room['alive'] if room['roles'][p] == "detective"]
    mafia_done = all(f"mafia:{m}" in room['actions'] for m in mafia)
    doctor_done = all(f"doctor:{d}" in room['actions'] for d in doctor)
    detective_done = all(f"detective:{d}" in room['actions'] for d in detective)
    if mafia_done and doctor_done and detective_done:
        resolve_night(room)
    save_room(room_id, room)
    return jsonify({'success': True})

def resolve_night(room):
    # Use string keys instead of tuple keys
    mafia_targets = [room['actions'][f"mafia:{m}"] for m in room['roles'] if f"mafia:{m}" in room['actions']]
    mafia_target = max(set(mafia_targets), key=mafia_targets.count) if mafia_targets else None
    doctor_targets = [room['actions'][f"doctor:{d}"] for d in room['roles'] if f"doctor:{d}" in room['actions']]
    doctor_save = doctor_targets[0] if doctor_targets else None
    detective_targets = [room['actions'][f"detective:{d}"] for d in room['roles'] if f"detective:{d}" in room['actions']]
    detective_result = None
    detective_win = False
    if detective_targets:
        target = detective_targets[0]
        target_role = room['roles'].get(target)
        detective_result = {"target": target, "role": target_role}
        # If detective catches mafia, detective wins
        if target_role == "mafia":
            room['phase'] = 'ended'
            room['winner'] = 'detective'
            room['last_result'] = {
                'killed': None,
                'saved': None,
                'investigated': detective_result,
                'detective_win': True
            }
            room['actions'] = {}
            save_room(room['room_id'], room)
            return  # End the function early
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
    room = get_room(room_id)
    if not room or room['phase'] != 'day' or player_name not in room['alive']:
        return jsonify({'error': 'Not allowed'}), 400
    room['actions'][player_name] = target
    if len(room['actions']) == len(room['alive']):
        resolve_day(room)
    save_room(room_id, room)
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
    save_room(room['room_id'], room)

if __name__ == '__main__':
    app.run(debug=True)
