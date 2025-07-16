import React from "react";

export default function CreateRoom({
  minPlayers,
  maxPlayers,
  setMinPlayers,
  setMaxPlayers,
  onCreate,
  onBack,
}) {
  return (
    <form onSubmit={onCreate}>
      <h2>Create Room</h2>
      <label>
        Min Players:
        <input
          type="number"
          value={minPlayers}
          min={3}
          max={maxPlayers}
          onChange={(e) => setMinPlayers(Number(e.target.value))}
          required
        />
      </label>
      <label>
        Max Players:
        <input
          type="number"
          value={maxPlayers}
          min={minPlayers}
          max={20}
          onChange={(e) => setMaxPlayers(Number(e.target.value))}
          required
        />
      </label>
      <button type="submit">Create</button>
      <button type="button" onClick={onBack}>
        Back
      </button>
    </form>
  );
}
