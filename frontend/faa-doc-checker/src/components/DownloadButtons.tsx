interface Props {
  resultId: string;
}

export default function DownloadButtons({ resultId }: Props) {
  const base = `/api/results/${resultId}`;
  return (
    <div className="mt-4 space-x-2">
      <a
        href={`${base}.docx`}
        className="bg-green-600 text-white px-3 py-1 rounded"
      >
        Download DOCX
      </a>
      <a
        href={`${base}.pdf`}
        className="bg-green-600 text-white px-3 py-1 rounded"
      >
        Download PDF
      </a>
    </div>
  );
}
