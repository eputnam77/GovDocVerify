import { useState } from "react";
import axios from "axios";
import UploadPanel from "./components/UploadPanel";
import VisibilityToggles from "./components/VisibilityToggles";
import SeverityToggles from "./components/SeverityToggles";
import ResultsPane from "./components/ResultsPane";
import DownloadButtons from "./components/DownloadButtons";
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import ErrorBanner from "./components/ErrorBanner";

// Allow the API base to be configured at build time via Vite but fall back to
// the current origin so that the frontend can talk to a co-hosted backend
// without additional configuration.
const API_BASE =
  import.meta.env.VITE_API_BASE || window.location.origin || "http://127.0.0.1:8000";

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#7c3aed',
    },
    background: {
      default: '#f3f4f6',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
});

export default function App() {
  const [html, setHtml] = useState<string>("");
  const [resultId, setResultId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [visibility, setVisibility] = useState<Record<string, boolean>>({
    readability: true,
    analysis: true,
    paragraph_length: true,
    terminology: true,
    acronym: true,
    headings: true,
    structure: true,
    format: true,
    accessibility: true,
    document_status: true,
  });
  const [severity, setSeverity] = useState<Record<string, boolean>>({
    error: true,
    warning: true,
    info: true,
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
    // Explicitly request category grouping so that downloads work consistently
    // with the backend's default behavior.
    data.append("group_by", "category");

    try {
      const { data: resp } = await axios.post(`${API_BASE}/process`, data, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      // The backend may return either ``rendered`` or ``html`` depending on the
      // processing path. Prefer the fully rendered HTML but fall back to raw
      // content when necessary.
      setHtml(resp.rendered || resp.html || "");
      setResultId(resp.result_id);
      setError(null);
    } catch (err: any) {
      const message =
        err.response?.data?.detail || err.message || "An unexpected error occurred";
      setError(message);
      setHtml("");
      setResultId(null);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" color="primary" elevation={2}>
        <Toolbar>
          <Typography variant="h5" component="div" sx={{ flexGrow: 1, textAlign: 'center', fontWeight: 600 }}>
            GovDocVerify
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 6, mb: 6 }}>
        <ErrorBanner message={error} onClose={() => setError(null)} />
        <Grid container spacing={4} alignItems="flex-start">
          <Grid item xs={12} md={4}>
            <UploadPanel onSubmit={handleSubmit} visibility={visibility} />
            <VisibilityToggles visibility={visibility} setVisibility={setVisibility} />
            <SeverityToggles severity={severity} setSeverity={setSeverity} />
          </Grid>
          <Grid item xs={12} md={8}>
            <ResultsPane html={html} severityFilters={severity} />
            {resultId && <DownloadButtons resultId={resultId} />}
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}
