import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';

interface Props {
  message: string | null;
  onClose: () => void;
}

export default function ErrorBanner({ message, onClose }: Props) {
  if (!message) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Alert severity="error" variant="filled" onClose={onClose} data-testid="error-banner">
        {message}
      </Alert>
    </Box>
  );
}
