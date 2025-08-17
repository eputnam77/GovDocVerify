interface Props {
  severity: Record<string, boolean>;
  setSeverity: (v: Record<string, boolean>) => void;
}

const levels = [
  { key: "error", label: "Errors" },
  { key: "warning", label: "Warnings" },
  { key: "info", label: "Info" },
];

export default function SeverityToggles({ severity, setSeverity }: Props) {
  const handleToggle = (key: string) => {
    setSeverity({ ...severity, [key]: !severity[key] });
  };

  return (
    <div className="bg-white rounded shadow p-4 mt-4">
      <h2 className="font-semibold mb-2">Severity Filters</h2>
      <div className="flex flex-col space-y-1">
        {levels.map((lvl) => (
          <label key={lvl.key} className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={severity[lvl.key]}
              onChange={() => handleToggle(lvl.key)}
            />
            <span>{lvl.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
