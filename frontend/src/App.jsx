import { useState, useEffect } from "react";
import "./App.css";
import Menu from "./components/Menu";
import CreateRoom from "./components/CreateRoom";
import JoinRoom from "./components/JoinRoom";
import Lobby from "./components/Lobby";
import NightActions from "./components/NightActions";
import DayActions from "./components/DayActions";
import GameOver from "./components/GameOver";
import RoleDisplay from "./components/RoleDisplay";

function App() {
  const [step, setStep] = useState("menu");
  const [roomId, setRoomId] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [minPlayers, setMinPlayers] = useState(5);
  const [maxPlayers, setMaxPlayers] = useState(10);
  const [players, setPlayers] = useState([]);
  const [votes, setVotes] = useState({});
  const [started, setStarted] = useState(false);
  const [vote, setVote] = useState(false);
  const [error, setError] = useState("");
  const [phase, setPhase] = useState("waiting");
  const [role, setRole] = useState("");
  const [alive, setAlive] = useState([]);
  const [lastResult, setLastResult] = useState({});
  const [winner, setWinner] = useState(null);
  const [nightTarget, setNightTarget] = useState("");
  const [dayTarget, setDayTarget] = useState("");

  // Create a room
  const handleCreateRoom = async (e) => {
    e.preventDefault();
    setError("");
    const res = await fetch("http://localhost:5000/api/create_room", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        min_players: minPlayers,
        max_players: maxPlayers,
      }),
    });
    const data = await res.json();
    if (data.room_id) {
      setRoomId(data.room_id);
      setStep("join");
    } else {
      setError("Failed to create room");
    }
  };

  // Join a room
  const handleJoinRoom = async (e) => {
    e.preventDefault();
    setError("");
    const res = await fetch("http://localhost:5000/api/join_room", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ room_id: roomId, player_name: playerName }),
    });
    const data = await res.json();
    if (data.success) {
      setStep("lobby");
      fetchRoomStatus(roomId);
    } else {
      setError(data.error || "Failed to join room");
    }
  };

  // Fetch room status (with playerName)
  const fetchRoomStatus = async (id) => {
    const res = await fetch(
      `http://localhost:5000/api/room_status?room_id=${id}&player_name=${playerName}`
    );
    const data = await res.json();
    if (!data.error) {
      setPlayers(data.players);
      setVotes(data.votes);
      setStarted(data.started);
      setPhase(data.phase);
      setRole(data.role);
      setAlive(data.alive);
      setLastResult(data.last_result || {});
      setWinner(data.winner);
    }
  };

  // Vote to start
  const handleVote = async (v) => {
    setVote(v);
    const res = await fetch("http://localhost:5000/api/vote_start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: roomId,
        player_name: playerName,
        vote: v,
      }),
    });
    const data = await res.json();
    setVotes(data.votes);
    setStarted(data.started);
  };

  // Night action
  const handleNightAction = async () => {
    if (!nightTarget) return;
    await fetch("http://localhost:5000/api/night_action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: roomId,
        player_name: playerName,
        target: nightTarget,
      }),
    });
    setNightTarget("");
  };

  // Day vote
  const handleDayVote = async () => {
    if (!dayTarget) return;
    await fetch("http://localhost:5000/api/day_vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: roomId,
        player_name: playerName,
        target: dayTarget,
      }),
    });
    setDayTarget("");
  };

  // Poll room status in lobby/game
  useEffect(() => {
    let interval;
    const poll = () => fetchRoomStatus(roomId);
    if ((step === "lobby" || step === "game") && roomId) {
      interval = setInterval(poll, 2000);
    }
    return () => clearInterval(interval);
  }, [step, roomId]);

  return (
    <div className="App">
      <h1>Mafia Game</h1>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {step === "menu" && (
        <Menu
          onCreate={() => setStep("create")}
          onJoin={() => setStep("join")}
        />
      )}
      {step === "create" && (
        <CreateRoom
          minPlayers={minPlayers}
          maxPlayers={maxPlayers}
          setMinPlayers={setMinPlayers}
          setMaxPlayers={setMaxPlayers}
          onCreate={handleCreateRoom}
          onBack={() => setStep("menu")}
        />
      )}
      {step === "join" && (
        <JoinRoom
          roomId={roomId}
          setRoomId={setRoomId}
          playerName={playerName}
          setPlayerName={setPlayerName}
          onJoin={handleJoinRoom}
          onBack={() => setStep("menu")}
        />
      )}
      {step === "lobby" && (
        <Lobby
          roomId={roomId}
          players={players}
          votes={votes}
          vote={vote}
          started={started}
          onVote={handleVote}
          onEnterGame={() => setStep("game")}
        />
      )}
      {step === "game" && (
        <div>
          <RoleDisplay playerName={playerName} role={role} alive={alive} />
          {winner && <GameOver winner={winner} />}
          {phase === "night" && alive.includes(playerName) && (
            <NightActions
              role={role}
              alive={alive}
              playerName={playerName}
              nightTarget={nightTarget}
              setNightTarget={setNightTarget}
              onSubmit={handleNightAction}
              lastResult={lastResult}
            />
          )}
          {phase === "day" && alive.includes(playerName) && (
            <DayActions
              alive={alive}
              playerName={playerName}
              dayTarget={dayTarget}
              setDayTarget={setDayTarget}
              onSubmit={handleDayVote}
              lastResult={lastResult}
            />
          )}
          {phase === "ended" && <GameOver winner={winner} />}
        </div>
      )}
    </div>
  );
}

export default App;
