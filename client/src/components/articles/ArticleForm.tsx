import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubmit } from '@/lib/hooks';
import { articleService, publicationService, type Article, type ArticleCreate } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useFetch } from '@/lib/hooks';
import { ArrowLeft, Loader2, Image as ImageIcon, AlertTriangle } from 'lucide-react';
import { RichTextEditor } from '../articles/RichTextEditor';
import '@/components/articles/editor.css';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'sonner';

interface ArticleFormProps {
  article?: Article;
  isEditing?: boolean;
}

type ArticleStatus = 'draft' | 'public' | 'unlisted';

export default function ArticleForm({ article, isEditing = false }: ArticleFormProps) {
  const navigate = useNavigate();
  
  // Form state
  const [title, setTitle] = useState(article?.title || '');
  const [subtitle, setSubtitle] = useState(article?.subtitle || '');
  const [content, setContent] = useState(article?.content || '');
  const [tags, setTags] = useState(article?.tags?.join(', ') || '');
  const [status, setStatus] = useState<ArticleStatus>(
    (article?.status as ArticleStatus) || 'draft'
  );
  const [publicationId, setPublicationId] = useState(
    article?.publication_id || 'none'
  );
  const [showAPIWarning, setShowAPIWarning] = useState(true);
  
  // Fetch publications for select box
  const { data: publications } = useFetch(publicationService.getAll, []);
  
  // Create article submission
  const { submit: createArticle, isSubmitting: isCreating } = useSubmit<Article, ArticleCreate>(
    (data) => articleService.create(data!),
    {
      onSuccess: (newArticle) => {
        navigate(`/articles/${newArticle.id}`);
      },
      successMessage: 'Article created successfully'
    }
  );
  
  // Update article submission
  const { submit: updateArticle, isSubmitting: isUpdating } = useSubmit<Article, { id: string; article: ArticleCreate }>(
    (data) => 
      articleService.update(data!.id, data!.article),
    {
      onSuccess: (updatedArticle) => {
        navigate(`/articles/${updatedArticle.id}`);
      },
      successMessage: 'Article updated successfully'
    }
  );
  
  const isSubmitting = isCreating || isUpdating;
  
  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Convert tags string to array
    const tagsArray = tags
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0);
    
    const articleData: ArticleCreate = {
      title,
      subtitle: subtitle || undefined,
      content,
      tags: tagsArray,
      status: status,
      publication_id: publicationId === 'none' ? undefined : publicationId
    };
    
    if (isEditing && article) {
      updateArticle({ id: article.id, article: articleData });
    } else {
      createArticle(articleData);
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="flex items-center">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1"
          onClick={() => navigate(-1)}
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
      
      {showAPIWarning && (
        <Alert variant="warning" className="bg-amber-50 border-amber-200">
          <AlertTriangle className="h-5 w-5 text-amber-600" />
          <AlertTitle className="text-amber-800 font-medium">Medium API Notice</AlertTitle>
          <AlertDescription className="text-amber-700">
            Medium's official API was archived in March 2023. Scribley is currently using it in a limited capacity, but it may stop functioning at any time. Consider saving a backup of your content.
            <Button
              variant="link"
              className="text-amber-800 p-0 h-auto ml-2"
              onClick={() => setShowAPIWarning(false)}
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="Enter the article title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="subtitle">Subtitle (optional)</Label>
            <Input
              id="subtitle"
              placeholder="Enter a subtitle or brief description"
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="content">Content</Label>
            <RichTextEditor
              value={content}
              onChange={setContent}
              placeholder="Write your article content..."
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              placeholder="productivity, writing, tips, programming"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
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
        </div>
        
        <div className="flex justify-end space-x-2">
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => navigate(-1)}
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
    </div>
  );
} 