import React, { useState } from "react";
import BlockList from "./components/BlockList";
import Toolbar from "./components/Toolbar";

export default function App() {
  const [blocks, setBlocks] = useState([]);
  const [template, setTemplate] = useState(0);
  const [color, setColor] = useState("#aee2fb");

  return (
    <div className="app-root">
      <Toolbar setBlocks={setBlocks} setTemplate={setTemplate} setColor={setColor} />
      <main>
        <BlockList blocks={blocks} setBlocks={setBlocks} color={color} template={template} />
      </main>
    </div>
  );
}
