import { useArticleForm } from '@/lib/hooks';
import { type Article } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { RichTextEditor } from '../articles/RichTextEditor';
import ArticleEditorLayout from '../layout/ArticleEditorLayout';
import { DraftSaveIndicator } from './DraftSaveIndicator';
import '@/components/articles/editor.css';
import { showInfo } from '@/components/ui/sonner';
import { toast } from 'sonner';
import { useEffect } from 'react';

interface ArticleFormProps {
  article?: Article;
  isEditing?: boolean;
}

type ArticleStatus = 'draft' | 'public' | 'unlisted';

export default function ArticleForm({ article, isEditing = false }: ArticleFormProps) {
  // Use our custom hook to manage all form state and logic
  const {
    // Form state
    title,
    setTitle,
    subtitle,
    setSubtitle,
    content,
    setContent,
    tags,
    setTags,
    status,
    setStatus,
    publicationId,
    setPublicationId,
    showAPIWarning,
    setShowAPIWarning,
    
    // Draft recovery
    isRecovered,
    showDraftRecoveryNotice,
    discardRecoveredDraft,
    lastSavedFormatted,
    triggerSaveDraft,
    
    // AI Assistant state
    isAssistantOpen,
    toggleAssistantPanel,
    
    // Data
    publications,
    isSubmitting,
    
    // Handlers
    handleSubmit,
    handleInsertContent,
    
    // Navigation
    goBack
  } = useArticleForm(article, isEditing);
  
  // Show API warning using sonner
  useEffect(() => {
    const warningKey = 'mediumApiWarningDismissed';
    const hasBeenDismissed = localStorage.getItem(warningKey);
    const toastId = 'medium-api-deprecated-warning'; // Static ID for this specific warning

    if (showAPIWarning && !hasBeenDismissed) {
      toast.warning(
        "Medium API Notice: Medium's official API was archived in March 2023. Scribley is currently using it in a limited capacity, but it may stop functioning at any time. Consider saving a backup of your content.",
        {
          id: toastId,
          duration: Infinity,
          action: {
            label: "Dismiss",
            onClick: () => {
              localStorage.setItem(warningKey, 'true');
              setShowAPIWarning(false);
              toast.dismiss(toastId);
            }
          }
        }
      );
    }
  }, [showAPIWarning, setShowAPIWarning]);
  
  // Show draft recovery notice using sonner
  useEffect(() => {
    if (isRecovered && showDraftRecoveryNotice) {
      showInfo(
        "A previously unsaved draft has been recovered. You can continue editing or discard it.",
        "Draft Recovered",
        {
          action: {
            label: "Discard Draft",
            onClick: discardRecoveredDraft
          }
        }
      );
    }
  }, [isRecovered, showDraftRecoveryNotice, discardRecoveredDraft]);
  
  return (
    <div className="space-y-6 min-w-0 w-full">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1"
            onClick={goBack}
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          <div className="ml-4">
            <h1 className="text-2xl font-bold">
              {isEditing ? 'Edit Article' : 'Create New Article'}
            </h1>
          </div>
        </div>
        
        {/* Draft save indicator */}
        <DraftSaveIndicator 
          lastSaved={lastSavedFormatted}
          isRecovered={isRecovered && showDraftRecoveryNotice}
          onDiscard={discardRecoveredDraft}
        />
      </div>
      
      {/* Use ArticleEditorLayout for layout management */}
      <ArticleEditorLayout 
        onInsertContent={handleInsertContent}
        onInsertTitle={setTitle}
        isAssistantOpen={isAssistantOpen}
        onAssistantToggle={toggleAssistantPanel}
        saveDraft={triggerSaveDraft}
      >
        <form onSubmit={handleSubmit} className="space-y-4 min-w-0 w-full">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="Enter the article title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="min-w-0"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="subtitle">Subtitle (optional)</Label>
            <Input
              id="subtitle"
              placeholder="Enter a subtitle or brief description"
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
              className="min-w-0"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="content">Content</Label>
            <RichTextEditor
              value={content}
              onChange={setContent}
              placeholder="Write your article content..."
              isAssistantOpen={isAssistantOpen}
              onAssistantToggle={toggleAssistantPanel}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              placeholder="productivity, writing, tips, programming"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="min-w-0"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={status} onValueChange={(value: ArticleStatus) => setStatus(value)}>
                <SelectTrigger id="status">
                  <SelectValue placeholder="Select a status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="public">Public</SelectItem>
                  <SelectItem value="unlisted">Unlisted</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="publication">Publication (optional)</Label>
              <Select 
                value={publicationId} 
                onValueChange={setPublicationId}
              >
                <SelectTrigger id="publication">
                  <SelectValue placeholder="Select a publication" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None (Personal Blog)</SelectItem>
                  {publications?.map(pub => (
                    <SelectItem key={pub.id} value={pub.id}>
                      {pub.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button 
              type="button" 
              variant="outline" 
              onClick={goBack}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {isEditing ? 'Update' : 'Create'} Article
            </Button>
          </div>
        </form>
      </ArticleEditorLayout>
    </div>
  );
} 