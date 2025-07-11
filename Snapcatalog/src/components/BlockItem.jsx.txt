import React from "react";

export default function BlockItem({ block, idx, setBlocks, color, template }) {
  // Rendu conditionnel selon type (texte, image, icône, diagramme...)
  const updateBlock = (update) => {
    setBlocks((blocs) =>
      blocs.map((b, i) => (i === idx ? { ...b, ...update } : b))
    );
  };

  return (
    <div className="block-item" style={{ background: color, margin: 8, padding: 12 }}>
      {block.type === "texte" && (
        <textarea
          value={block.contenu}
          onChange={e => updateBlock({ contenu: e.target.value })}
          style={{ width: "100%", minHeight: 60 }}
        />
      )}
      {/* ...autres types de blocs */}
      <button onClick={() => setBlocks(blocs => blocs.filter((_, i) => i !== idx))}>
        Supprimer
      </button>
    </div>
  );
}
