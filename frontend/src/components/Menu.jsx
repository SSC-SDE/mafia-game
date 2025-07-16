import React from "react";

export default function Menu({ onCreate, onJoin }) {
  return (
    <>
      <button onClick={onCreate}>Create Room</button>
      <button onClick={onJoin}>Join Room</button>
    </>
  );
}
