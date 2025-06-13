interface Props {
  visibility: Record<string, boolean>;
  setVisibility: (v: Record<string, boolean>) => void;
}

const categories = [
  { key: "readability", label: "Readability" },
  { key: "paragraph_length", label: "Paragraph Length" },
  { key: "terminology", label: "Terminology" },
  { key: "acronym", label: "Acronym" },
  { key: "headings", label: "Headings" },
  { key: "structure", label: "Structure" },
  { key: "format", label: "Format" },
  { key: "accessibility", label: "Accessibility" },
  { key: "document_status", label: "Document Status" },
];

export default function VisibilityToggles({ visibility, setVisibility }: Props) {
  const handleToggle = (key: string) => {
    setVisibility({ ...visibility, [key]: !visibility[key] });
  };

  return (
    <div className="bg-white rounded shadow p-4">
      <h2 className="font-semibold mb-2">Show/Hide Checks</h2>
      <div className="grid grid-cols-2 gap-2">
        {categories.map(cat => (
          <label key={cat.key} className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={visibility[cat.key]}
              onChange={() => handleToggle(cat.key)}
            />
            <span>{cat.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}