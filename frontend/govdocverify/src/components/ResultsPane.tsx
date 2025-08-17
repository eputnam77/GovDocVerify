import DOMPurify from 'dompurify';

interface Props {
  html: string;
}

export default function ResultsPane({ html }: Props) {
  const sanitizedHtml = DOMPurify.sanitize(html);
  if (!sanitizedHtml) return null;
  return (
    <iframe
      title="document-viewer"
      className="bg-white rounded shadow w-full h-full"
      srcDoc={sanitizedHtml}
    />
  );
}
