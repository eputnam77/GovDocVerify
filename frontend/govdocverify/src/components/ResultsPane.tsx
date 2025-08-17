import { useEffect, useRef } from 'react';
import DOMPurify from 'dompurify';

interface Props {
  html: string;
  severityFilters: Record<string, boolean>;
}

export default function ResultsPane({ html, severityFilters }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const sanitizedHtml = DOMPurify.sanitize(html);

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;
    const doc = iframe.contentDocument;
    if (!doc) return;

    doc.querySelectorAll('li').forEach((li) => {
      const span = li.querySelector('span');
      if (!span) return;
      const text = span.textContent || '';
      if (text.includes('[ERROR]')) li.classList.add('severity-error');
      else if (text.includes('[WARNING]')) li.classList.add('severity-warning');
      else if (text.includes('[INFO]')) li.classList.add('severity-info');
    });

    ['error', 'warning', 'info'].forEach((sev) => {
      const show = severityFilters[sev];
      doc.querySelectorAll(`.severity-${sev}`).forEach((el) => {
        (el as HTMLElement).style.display = show ? '' : 'none';
      });
    });
  }, [html, severityFilters]);

  if (!sanitizedHtml) return null;
  return (
    <iframe
      ref={iframeRef}
      title="document-viewer"
      className="bg-white rounded shadow w-full h-full"
      srcDoc={sanitizedHtml}
    />
  );
}
