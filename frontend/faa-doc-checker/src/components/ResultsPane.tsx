import React, { useState } from "react";
import axios from "axios";

const API_URL = "/api/process"; // Adjust if needed

const DocumentCheckResults: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("ADVISORY_CIRCULAR");
  const [groupBy, setGroupBy] = useState("category");
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };
  const handleDocTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => setDocType(e.target.value);
  const handleGroupByChange = (e: React.ChangeEvent<HTMLInputElement>) => setGroupBy(e.target.value);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("doc_file", file);
    formData.append("doc_type", docType);
    formData.append("group_by", groupBy);
    try {
      const response = await axios.post(API_URL, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setResults(response.data);
    } catch (err: any) {
      setResults({ rendered: `<div style='color:red'>Error: ${err.message}</div>` });
    } finally {
      setLoading(false);
    }
  };

  // Render results
  const renderResults = () => {
    if (!results) return null;
    return (
      <div>
        <div dangerouslySetInnerHTML={{ __html: results.rendered }} />
        {/* Optionally, render by_category or by_severity details here */}
      </div>
    );
  };

  return (
    <div>
      <form onSubmit={handleSubmit} style={{ marginBottom: 32 }}>
        <div>
          <label>Upload Document:</label>
          <input type="file" accept=".docx" onChange={handleFileChange} />
        </div>
        <div>
          <label>Document Type:</label>
          <select value={docType} onChange={handleDocTypeChange}>
            <option value="ADVISORY_CIRCULAR">Advisory Circular</option>
            <option value="ORDER">Order</option>
            {/* Add more types as needed */}
          </select>
        </div>
        <div>
          <label>Group Results By:</label>
          <label>
            <input
              type="radio"
              value="category"
              checked={groupBy === "category"}
              onChange={handleGroupByChange}
            />
            Category
          </label>
          <label>
            <input
              type="radio"
              value="severity"
              checked={groupBy === "severity"}
              onChange={handleGroupByChange}
            />
            Severity
          </label>
        </div>
        <button type="submit" disabled={loading} style={{ marginTop: 12 }}>
          {loading ? "Checking..." : "Check Document"}
        </button>
      </form>
      <div style={{ marginTop: 32 }}>
        {renderResults()}
      </div>
    </div>
  );
};

export default DocumentCheckResults;