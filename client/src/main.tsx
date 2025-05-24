import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { ThemeProvider } from './components/theme-provider';
import { UserPreferencesProvider } from './contexts/UserPreferencesContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <UserPreferencesProvider>
      <ThemeProvider defaultTheme="system" storageKey="scribley-theme">
        <App />
      </ThemeProvider>
    </UserPreferencesProvider>
  </React.StrictMode>
);
