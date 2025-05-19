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
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Eye, MoreHorizontal, Pencil, Plus, Trash, Upload, Search, Filter, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

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
    <div className="space-y-8">
      <div className="flex flex-col space-y-2 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Articles</h2>
          <p className="text-muted-foreground mt-1">Manage and publish your Medium articles</p>
        </div>
        <Button asChild className="gap-2">
          <Link to="/articles/new">
            <Plus className="h-4 w-4" /> New Article
          </Link>
        </Button>
      </div>
      
      <Card className="border-border/50">
        <CardContent className="p-6">
          {/* Filters */}
          <div className="flex flex-col space-y-4 sm:flex-row sm:space-y-0 sm:space-x-4 sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search articles..."
                value={searchFilter}
                onChange={e => setSearchFilter(e.target.value)}
                className="pl-9 w-full"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
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
          </div>
        </CardContent>
      </Card>
      
      {/* Articles Table */}
      {isLoading ? (
        <Card>
          <CardContent className="p-32 flex items-center justify-center">
            <div className="animate-pulse flex flex-col items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-muted"></div>
              <p className="text-muted-foreground">Loading articles...</p>
            </div>
          </CardContent>
        </Card>
      ) : filteredArticles && filteredArticles.length > 0 ? (
        <Card className="border-border/50">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[40%]">Title</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Published</TableHead>
                <TableHead className="w-[100px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredArticles.map((article, idx) => (
                <TableRow key={article.id} className="group">
                  <TableCell className="font-medium py-4">
                    <Link to={`/articles/${article.id}`} className="hover:underline block transition-colors group-hover:text-primary">
                      <span className="line-clamp-1">{article.title}</span>
                      {article.subtitle && (
                        <p className="text-sm text-muted-foreground truncate max-w-xs mt-1 font-normal">
                          {article.subtitle}
                        </p>
                      )}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={article.status === 'public' ? 'default' : 'outline'} className="font-normal">
                      {article.status === 'public' ? 'Published' : article.status === 'draft' ? 'Draft' : 'Unlisted'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(article.created_at)}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {article.published_at ? (
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(article.published_at)}
                      </div>
                    ) : '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                          <span className="sr-only">Actions</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-40">
                        <DropdownMenuItem onClick={() => navigate(`/articles/${article.id}`)} className="cursor-pointer">
                          <Eye className="mr-2 h-4 w-4" /> View
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => navigate(`/articles/${article.id}/edit`)} className="cursor-pointer">
                          <Pencil className="mr-2 h-4 w-4" /> Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => publishArticle(article.id)}
                          disabled={isPublishing}
                          className="cursor-pointer"
                        >
                          <Upload className="mr-2 h-4 w-4" /> Publish
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => setConfirmDelete(article.id)}
                          className="text-destructive focus:text-destructive cursor-pointer"
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
        </Card>
      ) : (
        <Card className="border-dashed border-2 bg-transparent">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <div className="rounded-full bg-primary/10 h-16 w-16 flex items-center justify-center mb-4">
              <Pencil className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No articles found</h3>
            <CardDescription className="max-w-md mb-6">
              {searchFilter || statusFilter !== 'all'
                ? "Try adjusting your filters or create a new article."
                : "Get started by creating your first article."}
            </CardDescription>
            <Button asChild className="gap-2">
              <Link to="/articles/new">
                <Plus className="h-4 w-4" /> New Article
              </Link>
            </Button>
          </CardContent>
        </Card>
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
          <Separator className="my-4" />
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setConfirmDelete(null)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={() => confirmDelete && deleteArticle(confirmDelete)}
              disabled={isDeleting}
              className="gap-2"
            >
              {isDeleting ? 'Deleting...' : (
                <>
                  <Trash className="h-4 w-4" />
                  Delete
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
} 