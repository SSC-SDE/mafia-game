import React from "react";

function DayActions({
  alive,
  playerName,
  dayTarget,
  setDayTarget,
  onSubmit,
  lastResult,
}) {
  return (
    <div>
      <h3>Day Phase</h3>
      <p>Vote to eliminate a player:</p>
      <select value={dayTarget} onChange={(e) => setDayTarget(e.target.value)}>
        <option value="">Select</option>
        {alive
          .filter((p) => p !== playerName)
          .map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
      </select>
      <button onClick={onSubmit} disabled={!dayTarget}>
        Vote
      </button>
      {lastResult.voted_out && (
        <p>Yesterday: {lastResult.voted_out} was voted out.</p>
      )}
    </div>
  );
}

export default DayActions;
