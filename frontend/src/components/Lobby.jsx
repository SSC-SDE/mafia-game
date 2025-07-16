import React from "react";

export default function Lobby({
  roomId,
  players,
  votes,
  vote,
  started,
  onVote,
  onEnterGame,
}) {
  return (
    <div>
      <h2>Room: {roomId}</h2>
      <h3>
        Players ({players.length}): {players.join(", ")}
      </h3>
      <h4>Votes to Start:</h4>
      <ul>
        {players.map((p) => (
          <li key={p}>
            {p}:{" "}
            {votes[p] === undefined ? "Not voted" : votes[p] ? "Yes" : "No"}
          </li>
        ))}
      </ul>
      <div>
        <button
          onClick={() => onVote(true)}
          disabled={vote === true || started}
        >
          Vote Yes
        </button>
        <button
          onClick={() => onVote(false)}
          disabled={vote === false || started}
        >
          Vote No
        </button>
      </div>
      {started && (
        <>
          <h2 style={{ color: "green" }}>Game Started!</h2>
          <button onClick={onEnterGame}>Enter Game</button>
        </>
      )}
    </div>
  );
}
