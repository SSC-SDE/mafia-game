import React from "react";

function NightActions({
  role,
  alive,
  playerName,
  nightTarget,
  setNightTarget,
  onSubmit,
  lastResult,
}) {
  return (
    <div>
      <h3>Night Phase</h3>
      {role === "mafia" && (
        <>
          <p>Choose someone to eliminate:</p>
          <select
            value={nightTarget}
            onChange={(e) => setNightTarget(e.target.value)}
          >
            <option value="">Select</option>
            {alive
              .filter((p) => p !== playerName)
              .map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
          </select>
          <button onClick={onSubmit} disabled={!nightTarget}>
            Submit
          </button>
        </>
      )}
      {role === "doctor" && (
        <>
          <p>Choose someone to save:</p>
          <select
            value={nightTarget}
            onChange={(e) => setNightTarget(e.target.value)}
          >
            <option value="">Select</option>
            {alive.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <button onClick={onSubmit} disabled={!nightTarget}>
            Submit
          </button>
        </>
      )}
      {role === "detective" && (
        <>
          <p>Choose someone to investigate:</p>
          <select
            value={nightTarget}
            onChange={(e) => setNightTarget(e.target.value)}
          >
            <option value="">Select</option>
            {alive
              .filter((p) => p !== playerName)
              .map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
          </select>
          <button onClick={onSubmit} disabled={!nightTarget}>
            Submit
          </button>
        </>
      )}
      {role === "villager" && <p>Waiting for night actions...</p>}
      {lastResult.killed && <p>Last night: {lastResult.killed} was killed.</p>}
      {lastResult.saved && (
        <p>But {lastResult.saved} was saved by the doctor!</p>
      )}
      {lastResult.investigated && role === "detective" && (
        <p>
          Investigation: {lastResult.investigated.target} is a{" "}
          {lastResult.investigated.role}
        </p>
      )}
    </div>
  );
}

export default NightActions;
