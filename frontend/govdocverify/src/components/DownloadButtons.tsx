interface Props {
  resultId: string;
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export default function DownloadButtons({ resultId }: Props) {
  const base = `${API_BASE}/results/${resultId}`;
  return (
    <div className="mt-4 space-x-2">
      <a
        href={`${base}.docx`}
        className="bg-green-600 text-white px-3 py-1 rounded"
        download
      >
        Download DOCX
      </a>
      <a
        href={`${base}.pdf`}
        className="bg-green-600 text-white px-3 py-1 rounded"
        download
      >
        Download PDF
      </a>
    </div>
  );
}
