import React from "react";
import BlockItem from "./BlockItem";
// Pour le drag&drop, tu pourras utiliser dnd-kit ici

export default function BlockList({ blocks, setBlocks, color, template }) {
  // Affiche chaque bloc, gère drag&drop, édition, suppression
  return (
    <div className="block-list">
      {blocks.map((block, idx) => (
        <BlockItem
          key={idx}
          block={block}
          idx={idx}
          setBlocks={setBlocks}
          color={color}
          template={template}
        />
      ))}
      <button onClick={() => setBlocks([...blocks, { type: "texte", contenu: "" }])}>
        Ajouter un bloc texte
      </button>
    </div>
  );
}
