import React from 'react';
import { cn } from '@/lib/utils';
import { Check, Save } from 'lucide-react';

interface DraftSaveIndicatorProps {
  lastSaved: string;
  isSaving?: boolean;
  isRecovered?: boolean;
  onDiscard?: () => void;
  className?: string;
}

export function DraftSaveIndicator({
  lastSaved,
  isSaving = false,
  isRecovered = false,
  onDiscard,
  className
}: DraftSaveIndicatorProps) {
  return (
    <div className={cn(
      "flex items-center gap-2 text-sm text-muted-foreground",
      className
    )}>
      {isSaving ? (
        <>
          <Save className="h-3.5 w-3.5 animate-pulse" />
          <span>Saving...</span>
        </>
      ) : lastSaved ? (
        <>
          <Check className="h-3.5 w-3.5 text-green-500" />
          <span>
            {isRecovered ? (
              <>
                Draft recovered - last saved {lastSaved}
                {onDiscard && (
                  <button 
                    onClick={onDiscard}
                    className="ml-2 text-primary hover:underline focus:outline-none"
                  >
                    Discard
                  </button>
                )}
              </>
            ) : (
              <>Saved {lastSaved}</>
            )}
          </span>
        </>
      ) : null}
    </div>
  );
} 