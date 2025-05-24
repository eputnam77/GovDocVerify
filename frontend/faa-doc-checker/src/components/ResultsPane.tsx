interface Props {
  html: string;
}

export default function ResultsPane({ html }: Props) {
  return (
    <div className="bg-white rounded shadow p-4 min-h-[300px] lg:col-span-2">
      <h2 className="font-semibold mb-2">Results</h2>
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}