import React from "react";

export default function JoinRoom({
  roomId,
  setRoomId,
  playerName,
  setPlayerName,
  onJoin,
  onBack,
}) {
  return (
    <form onSubmit={onJoin}>
      <h2>Join Room</h2>
      <label>
        Room ID:
        <input
          type="text"
          value={roomId}
          onChange={(e) => setRoomId(e.target.value)}
          required
        />
      </label>
      <label>
        Name:
        <input
          type="text"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          required
        />
      </label>
      <button type="submit">Join</button>
      <button type="button" onClick={onBack}>
        Back
      </button>
    </form>
  );
}
