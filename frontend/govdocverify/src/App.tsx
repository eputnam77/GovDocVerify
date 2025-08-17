import { useState } from "react";
import axios from "axios";
import UploadPanel from "./components/UploadPanel";
import VisibilityToggles from "./components/VisibilityToggles";
import ResultsPane from "./components/ResultsPane";
import DownloadButtons from "./components/DownloadButtons";
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

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
    setHtml(resp.rendered || resp.html || "");
    setResultId(resp.result_id);
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
        <Grid container spacing={4} alignItems="flex-start">
          <Grid item xs={12} md={4}>
            <UploadPanel onSubmit={handleSubmit} visibility={visibility} />
            <VisibilityToggles visibility={visibility} setVisibility={setVisibility} />
          </Grid>
          <Grid item xs={12} md={8}>
            <ResultsPane html={html} />
            {resultId && <DownloadButtons resultId={resultId} />}
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}
