import { useParams, useNavigate, Navigate } from 'react-router-dom';
import { useFetch, useSubmit } from '@/lib/hooks';
import { articleService, publicationService, type Publication } from '@/lib/api';
import { formatDateTime, getStatusColor } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { 
  ArrowLeft, 
  Calendar, 
  Edit, 
  ExternalLink, 
  Loader2, 
  Tag, 
  Trash, 
  Upload,
  Pencil,
  Trash2,
  CheckCircle,
  ArrowUpFromLine,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { toast } from 'sonner';
import { useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';

export default function ArticleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [publishDialogOpen, setPublishDialogOpen] = useState(false);
  const [publishStatus, setPublishStatus] = useState('public');
  const [selectedPublication, setSelectedPublication] = useState<Publication | null>(null);
  const [publishError, setPublishError] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  
  const { data: article, loading: isLoading, error, refetch } = useFetch(
    () => id ? articleService.getById(id) : Promise.reject('No article ID'),
    [id]
  );
  
  const { data: publications, loading: loadingPublications } = useFetch(
    () => publicationService.getAll(),
    []
  );
  
  // Delete article handler
  const { submit: deleteArticle, isSubmitting: isDeleting } = useSubmit(
    async () => {
      if (!id) throw new Error('No article ID');
      await articleService.delete(id);
      return id;
    },
    {
      onSuccess: () => {
        toast.success('Article deleted successfully');
        navigate('/articles');
      }
    }
  );
  
  // Publishing handler
  const { isSubmitting: isPublishing, submit: publishArticle } = useSubmit(
    async () => {
      if (!id) return null;
      const result = await articleService.publish(id);
      return result;
    },
    {
      onSuccess: (updatedArticle) => {
        toast.success('Article published to Medium!');
        if (updatedArticle) {
          refetch();
        }
      },
      onError: (error) => {
        toast.error(`Failed to publish: ${error.message}`);
      }
    }
  );
  
  // Find the publishToMedium function and update it to use the real API
  const publishToMedium = async () => {
    if (!article) return;
    
    try {
      setPublishing(true);
      setPublishError(null);
      
      // Get the selected publication ID
      const publicationId = selectedPublication ? selectedPublication.id : undefined;
      
      // Use the real Medium API to publish
      const publishedArticle = await articleService.publish(
        article.id, 
        { 
          status: publishStatus, 
          publication_id: publicationId 
        }
      );
      
      // Update the article with Medium data
      refetch();
      
      // Show success message
      toast.success("Published to Medium!", {
        description: publishedArticle.medium_url 
          ? <a href={publishedArticle.medium_url} target="_blank" rel="noopener noreferrer" className="underline">View on Medium</a> 
          : "Your article has been published to Medium",
      });
      
      // Close the dialog
      setPublishDialogOpen(false);
    } catch (error) {
      console.error("Failed to publish to Medium:", error);
      setPublishError(error instanceof Error ? error.message : "Failed to publish to Medium");
    } finally {
      setPublishing(false);
    }
  };
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-60">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }
  
  if (error || !id || !article) {
    return <Navigate to="/articles" replace />;
  }
  
  // Handlers
  const handlePublish = () => {
    setPublishDialogOpen(true);
  };
  
  const handleDelete = () => {
    deleteArticle();
  };
  
  return (
    <div className="space-y-6">
      {/* Top navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1"
          onClick={() => navigate('/articles')}
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Articles
        </Button>
        
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => navigate(`/articles/${id}/edit`)}
          >
            <Edit className="h-4 w-4 mr-2" /> Edit
          </Button>
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setConfirmDelete(true)}
          >
            <Trash className="h-4 w-4 mr-2" /> Delete
          </Button>
          {article.status !== 'public' && (
            <Button 
              size="sm" 
              onClick={handlePublish}
              disabled={isPublishing}
            >
              {isPublishing ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Upload className="h-4 w-4 mr-2" />
              )}
              Publish to Medium
            </Button>
          )}
        </div>
      </div>
      
      {/* Article content */}
      <Card className="border rounded-lg shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold">{article.title}</h1>
              {article.subtitle && (
                <p className="text-lg text-muted-foreground mt-1">{article.subtitle}</p>
              )}
            </div>
            <span className={`px-3 py-1 rounded-full text-xs ${getStatusColor(article.status)}`}>
              {article.status}
            </span>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-muted-foreground mt-2">
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>Created: {formatDateTime(article.created_at)}</span>
            </div>
            {article.published_at && (
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>Published: {formatDateTime(article.published_at)}</span>
              </div>
            )}
          </div>
          
          {article.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {article.tags.map(tag => (
                <div 
                  key={tag} 
                  className="bg-secondary text-secondary-foreground px-2 py-1 rounded-md text-xs flex items-center gap-1"
                >
                  <Tag className="h-3 w-3" />
                  {tag}
                </div>
              ))}
            </div>
          )}
        </CardHeader>
        
        <CardContent className="prose dark:prose-invert max-w-none">
          {/* Render the content as formatted Markdown */}
          <ReactMarkdown>{article.content}</ReactMarkdown>
        </CardContent>
        
        {article.medium_url && (
          <CardFooter className="bg-muted/50 rounded-b-lg">
            <div className="flex justify-between items-center w-full">
              <span className="text-sm font-medium">Published on Medium</span>
              <Button variant="outline" size="sm" asChild>
                <a href={article.medium_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-1" /> View on Medium
                </a>
              </Button>
            </div>
          </CardFooter>
        )}
      </Card>
      
      {/* Delete confirmation dialog */}
      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Are you sure?</DialogTitle>
            <DialogDescription>
              This action cannot be undone. This will permanently delete the article
              from our servers.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setConfirmDelete(false)} 
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDelete}
              disabled={isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Publish dialog */}
      <Dialog open={publishDialogOpen} onOpenChange={setPublishDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Publish to Medium</DialogTitle>
            <DialogDescription>
              Choose how you want to publish this article to Medium.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="status">Publish Status</Label>
              <Select value={publishStatus} onValueChange={setPublishStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="public">Public (visible to everyone)</SelectItem>
                  <SelectItem value="unlisted">Unlisted (only visible with link)</SelectItem>
                  <SelectItem value="draft">Draft (save as draft on Medium)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="publication">Publication (optional)</Label>
              <Select 
                value={selectedPublication?.id || "none"} 
                onValueChange={(value) => {
                  const pub = publications?.find(p => p.id === value);
                  setSelectedPublication(pub || null);
                }}
                disabled={loadingPublications}
              >
                <SelectTrigger>
                  <SelectValue placeholder={loadingPublications ? "Loading publications..." : "Select a publication"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None (publish to your profile)</SelectItem>
                  {publications?.map(pub => (
                    <SelectItem key={pub.id} value={pub.id}>{pub.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {publishError && (
              <div className="text-sm text-red-500 mt-2">
                {publishError}
              </div>
            )}
          </div>
          
          <DialogFooter className="sm:justify-between">
            <DialogClose asChild>
              <Button type="button" variant="secondary">
                Cancel
              </Button>
            </DialogClose>
            <Button 
              type="button" 
              onClick={publishToMedium} 
              disabled={publishing}
            >
              {publishing ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Publishing...</> : 'Publish to Medium'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
} 