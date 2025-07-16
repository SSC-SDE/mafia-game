import React from "react";

function RoleDisplay({ playerName, role, alive }) {
  return (
    <>
      <h3>Your Name: {playerName}</h3>
      <h3>
        Your Role: <span style={{ color: "blue" }}>{role}</span>
      </h3>
      <h4>Alive Players: {alive.join(", ")}</h4>
    </>
  );
}

export default RoleDisplay;
