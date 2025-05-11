import { useState } from 'react';
import { useFetch, useSubmit } from '@/lib/hooks';
import { articleService, type Article, type ArticleCreate } from '@/lib/api';
import { formatDate, getStatusColor } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Eye, MoreHorizontal, Pencil, Plus, Trash, Upload } from 'lucide-react';

export default function Articles() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  
  const navigate = useNavigate();
  
  // Fetch articles with filters
  const { data: articles, loading: isLoading, refetch } = useFetch(
    () => articleService.getAll({ status: statusFilter !== 'all' ? statusFilter : undefined }),
    [statusFilter]
  );
  
  // Delete article handler
  const { submit: deleteArticle, isSubmitting: isDeleting } = useSubmit<string, string>(
    async (id) => {
      await articleService.delete(id!);
      setConfirmDelete(null);
      return id!;
    },
    {
      onSuccess: () => {
        refetch();
        toast.success('Article deleted successfully');
      }
    }
  );
  
  // Publish article handler
  const { submit: publishArticle, isSubmitting: isPublishing } = useSubmit<Article, string>(
    (id) => articleService.publish(id!),
    {
      onSuccess: () => {
        refetch();
        toast.success('Article published to Medium');
      }
    }
  );
  
  // Filter articles by search term
  const filteredArticles = articles?.filter(article => 
    article.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
    (article.subtitle && article.subtitle.toLowerCase().includes(searchFilter.toLowerCase()))
  );
  
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Articles</h2>
          <p className="text-muted-foreground">Manage your Medium articles</p>
        </div>
        <Button asChild>
          <Link to="/articles/new">
            <Plus className="mr-2 h-4 w-4" /> New Article
          </Link>
        </Button>
      </div>
      
      {/* Filters */}
      <div className="flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-2">
        <Input
          placeholder="Search articles..."
          value={searchFilter}
          onChange={e => setSearchFilter(e.target.value)}
          className="sm:max-w-xs"
        />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="sm:w-[180px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="public">Published</SelectItem>
            <SelectItem value="unlisted">Unlisted</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Articles Table */}
      {isLoading ? (
        <div className="flex items-center justify-center h-60">
          <p>Loading articles...</p>
        </div>
      ) : filteredArticles && filteredArticles.length > 0 ? (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Published</TableHead>
                <TableHead className="w-[100px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredArticles.map(article => (
                <TableRow key={article.id}>
                  <TableCell className="font-medium">
                    <Link to={`/articles/${article.id}`} className="hover:underline">
                      {article.title}
                    </Link>
                    {article.subtitle && (
                      <p className="text-sm text-muted-foreground truncate max-w-xs">
                        {article.subtitle}
                      </p>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(article.status)}`}>
                      {article.status}
                    </span>
                  </TableCell>
                  <TableCell>{formatDate(article.created_at)}</TableCell>
                  <TableCell>
                    {article.published_at ? formatDate(article.published_at) : '-'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                          <span className="sr-only">Actions</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => navigate(`/articles/${article.id}`)}>
                          <Eye className="mr-2 h-4 w-4" /> View
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => navigate(`/articles/${article.id}/edit`)}>
                          <Pencil className="mr-2 h-4 w-4" /> Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => publishArticle(article.id)}
                          disabled={isPublishing}
                        >
                          <Upload className="mr-2 h-4 w-4" /> Publish to Medium
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => setConfirmDelete(article.id)}
                          className="text-destructive focus:text-destructive"
                        >
                          <Trash className="mr-2 h-4 w-4" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center">
          <div className="mx-auto flex max-w-[420px] flex-col items-center justify-center text-center">
            <h3 className="mt-4 text-lg font-semibold">No articles found</h3>
            <p className="mb-4 mt-2 text-sm text-muted-foreground">
              {searchFilter || statusFilter 
                ? "Try adjusting your filters or create a new article."
                : "Get started by creating your first article."}
            </p>
            <Button asChild>
              <Link to="/articles/new">
                <Plus className="mr-2 h-4 w-4" /> New Article
              </Link>
            </Button>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Dialog */}
      <Dialog open={!!confirmDelete} onOpenChange={(open) => !open && setConfirmDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Are you sure?</DialogTitle>
            <DialogDescription>
              This action cannot be undone. This will permanently delete the article
              from our servers.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(null)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={() => confirmDelete && deleteArticle(confirmDelete)}
              disabled={isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
} 