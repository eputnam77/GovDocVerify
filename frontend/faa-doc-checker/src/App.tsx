import { useState } from "react";
import axios from "axios";
import UploadPanel from "./components/UploadPanel";
import VisibilityToggles from "./components/VisibilityToggles";
import ResultsPane from "./components/ResultsPane";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export default function App() {
  const [html, setHtml] = useState<string>("");
  const [visibility, setVisibility] = useState<Record<string, boolean>>({
    readability: true,
    paragraph_length: true,
    terminology: true,
    headings: true,
    structure: true,
    format: true,
    accessibility: true,
    document_status: true,
  });

  const handleSubmit = async (
    file: File,
    docType: string,
    vis: Record<string, boolean>
  ) => {
    const data = new FormData();
    data.append("doc_file", file);
    data.append("doc_type", docType);
    data.append("visibility_json", JSON.stringify(vis));

    const { data: resp } = await axios.post(`${API_BASE}/process`, data, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    setHtml(resp.html);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 md:p-12">
      <h1 className="text-3xl font-semibold text-center text-blue-700 mb-8">
        FAA Document Checker
      </h1>
      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-6">
          <UploadPanel onSubmit={handleSubmit} visibility={visibility} />
          <VisibilityToggles visibility={visibility} setVisibility={setVisibility} />
        </div>
        <ResultsPane html={html} />
      </div>
    </div>
  );
}
