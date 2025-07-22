import DOMPurify from 'dompurify';

interface Props {
  html: string;
}

export default function ResultsPane({ html }: Props) {
  const sanitizedHtml = DOMPurify.sanitize(html);
  return (
    <div
      className="bg-white rounded shadow p-4 overflow-auto"
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  );
}
