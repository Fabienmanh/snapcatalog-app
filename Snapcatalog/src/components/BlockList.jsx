import React from "react";
import BlockItem from "./BlockItem";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  useSortable,
  verticalListSortingStrategy
} from "@dnd-kit/sortable";
import {CSS} from "@dnd-kit/utilities";

export default function BlockList({ blocks, setBlocks, color, template }) {
  const sensors = useSensors(useSensor(PointerSensor));

  function handleDragEnd(event) {
    const { active, over } = event;
    if (active.id !== over?.id) {
      const oldIndex = blocks.findIndex(b => b._id === active.id);
      const newIndex = blocks.findIndex(b => b._id === over.id);
      setBlocks(arrayMove(blocks, oldIndex, newIndex));
    }
  }

  // Ajoute un identifiant unique à chaque bloc si non présent
  React.useEffect(() => {
    if (blocks.some(b => !b._id)) {
      setBlocks(blocks.map((b, i) => ({ _id: b._id || `block_${i}_${Math.random()}`, ...b })));
    }
    // eslint-disable-next-line
  }, []);

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext
        items={blocks.map(b => b._id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="block-list">
          {blocks.map((block, idx) => (
            <SortableBlock
              key={block._id}
              id={block._id}
              block={block}
              idx={idx}
              setBlocks={setBlocks}
              color={color}
              template={template}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}

function SortableBlock({ id, block, idx, setBlocks, color, template }) {
  const {attributes, listeners, setNodeRef, transform, transition, isDragging} = useSortable({id});
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    cursor: "grab"
  };
  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <BlockItem block={block} idx={idx} setBlocks={setBlocks} color={color} template={template} />
    </div>
  );
}
