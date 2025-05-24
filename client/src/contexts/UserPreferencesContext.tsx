import React, { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useUserPreferences } from '@/lib/hooks';

// Default preferences structure
export interface UserPreferences extends Record<string, unknown> {
  // Editor preferences
  editorFontSize: number;
  editorLineHeight: number;
  editorAutosaveEnabled: boolean;
  editorShowWordCount: boolean;
  
  // Theme preferences
  theme: 'light' | 'dark' | 'system';
  
  // AI Assistant preferences
  aiProviderPreference: string;
  aiModelPreference: string;
  
  // UI preferences
  sidebarCollapsed: boolean;
  tableDensity: 'compact' | 'normal' | 'spacious';
}

// Default preferences values
const defaultPreferences: UserPreferences = {
  // Editor preferences
  editorFontSize: 16,
  editorLineHeight: 1.6,
  editorAutosaveEnabled: true,
  editorShowWordCount: true,
  
  // Theme preferences
  theme: 'system',
  
  // AI Assistant preferences
  aiProviderPreference: 'ollama',
  aiModelPreference: 'llama3',
  
  // UI preferences
  sidebarCollapsed: false,
  tableDensity: 'normal',
};

// Context type
interface UserPreferencesContextType {
  preferences: UserPreferences;
  setPreferences: (prefs: UserPreferences | ((prev: UserPreferences) => UserPreferences)) => void;
  updatePreference: <K extends keyof UserPreferences>(key: K, value: UserPreferences[K]) => void;
  resetPreferences: () => void;
}

// Create context
const UserPreferencesContext = createContext<UserPreferencesContextType | undefined>(undefined);

// Provider component
export function UserPreferencesProvider({ children }: { children: ReactNode }) {
  const preferencesData = useUserPreferences<UserPreferences>(defaultPreferences);
  
  return (
    <UserPreferencesContext.Provider value={preferencesData}>
      {children}
    </UserPreferencesContext.Provider>
  );
}

// Hook for using the preferences context
export function usePreferences() {
  const context = useContext(UserPreferencesContext);
  
  if (context === undefined) {
    throw new Error('usePreferences must be used within a UserPreferencesProvider');
  }
  
  return context;
}

// Utility hook for using a specific preference
export function usePreference<K extends keyof UserPreferences>(key: K) {
  const { preferences, updatePreference } = usePreferences();
  
  const setValue = React.useCallback(
    (value: UserPreferences[K]) => {
      updatePreference(key, value);
    },
    [key, updatePreference]
  );
  
  return [preferences[key], setValue] as const;
} 