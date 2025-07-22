import { useState } from "react";

interface Props {
  onSubmit: (file: File, docType: string, visibility: Record<string, boolean>) => void;
  visibility: Record<string, boolean>;
}

export default function UploadPanel({ onSubmit, visibility }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>("Advisory Circular");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (file) onSubmit(file, docType, visibility);
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <input
        type="file"
        accept=".docx"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-700"
        required
      />
      <select
        value={docType}
        onChange={e => setDocType(e.target.value)}
        className="block w-full border rounded p-2"
      >
        <option>Advisory Circular</option>
        <option>Order</option>
        <option>Federal Register Notice</option>
        <option>Policy Statement</option>
        <option>Rule</option>
        <option>Technical Standard Order</option>
        <option>Other</option>
      </select>
      <button
        type="submit"
        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
      >
        Check Document
      </button>
    </form>
  );
}