import { type ReactNode } from 'react';
import React from 'react';
import { cn } from '@/lib/utils';
import { AIAssistantPanel } from '../articles/AIAssistantPanel';

interface ArticleEditorLayoutProps {
  children: ReactNode;
  onInsertContent: (content: string, title?: string) => void;
  onInsertTitle?: (title: string) => void;
  isAssistantOpen: boolean;
  onAssistantToggle: () => void;
  saveDraft: () => void;
}

export default function ArticleEditorLayout({
  children,
  onInsertContent,
  onInsertTitle,
  isAssistantOpen,
  onAssistantToggle,
  saveDraft
}: ArticleEditorLayoutProps) {
  // Use the parent's state for sidebar width
  const sidebarWidth = isAssistantOpen ? 384 : 0;
  
  // Handle content insertion from AI Assistant
  const handleInsertFromAssistant = (content: string, title?: string) => {
    onInsertContent(content, title);
    
    // If title is provided and we have a callback for it, call it
    if (title && onInsertTitle) {
      onInsertTitle(title);
    }
  };
  
  return (
    <div className="relative w-full">
      {/* Main content area */}
      <div 
        className={cn(
          "w-full transition-all duration-300 ease-in-out"
        )}
        style={{
          marginRight: sidebarWidth > 0 ? `${sidebarWidth}px` : '0',
          width: sidebarWidth > 0 ? `calc(100% - ${sidebarWidth}px)` : '100%',
          maxWidth: '100%',
          overflowX: 'hidden'
        }}
      >
        {/* No need to pass props to children as they're already passed from the parent */}
        {children}
      </div>

      {/* AI Assistant Panel */}
      <AIAssistantPanel 
        isOpen={isAssistantOpen} 
        onClose={onAssistantToggle}
        onInsertContent={handleInsertFromAssistant}
        saveDraft={saveDraft}
        onLayoutChange={() => {}} // No need to handle layout changes as we're using fixed width
      />
    </div>
  );
} 