import React from "react";

export default function Toolbar({ setBlocks, setTemplate, setColor }) {
  // Ajoute boutons template, couleur, importer/exporter, etc.
  return (
    <aside className="toolbar">
      <button onClick={() => setBlocks([])}>Nouveau catalogue</button>
      {/* Ajoute templates, couleurs, import/export ici */}
    </aside>
  );
}
