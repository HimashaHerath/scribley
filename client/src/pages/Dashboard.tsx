import { useCallback, useMemo } from 'react';
import { useFetch, useArticles, useCurrentUser, usePublications } from '@/lib/hooks';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { formatDate, truncateText } from '@/lib/utils';
import { BarChart3, BookOpen, FileText, Users, Clock, ExternalLink, ArrowUpRight, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';

// Stats card component
const StatCard = ({ title, value, icon, description, trend }: { 
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
  trend?: 'up' | 'down' | 'neutral';
}) => (
  <Card className="overflow-hidden border-border/50 transition-all hover:shadow-md">
    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <div className="h-8 w-8 rounded-md bg-primary/10 flex items-center justify-center text-primary">
        {icon}
      </div>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold">{value}</div>
      {description && (
        <p className="text-sm text-muted-foreground mt-1 flex items-center gap-1">
          {trend === 'up' && <ArrowUpRight className="h-3 w-3 text-emerald-500" />}
          {trend === 'down' && <ArrowUpRight className="h-3 w-3 rotate-90 text-destructive" />}
          {description}
        </p>
      )}
    </CardContent>
  </Card>
);

export default function Dashboard() {
  // Create a stable options object that won't change between renders
  const articleOptions = useMemo(() => ({ limit: 5 }), []);
  
  // Use the custom hooks with memoized options
  const { data: articles, loading: articlesLoading } = useArticles(articleOptions);
  const { data: user } = useCurrentUser();
  const { data: publications } = usePublications();
  
  // Calculate stats
  const totalArticles = articles?.length || 0;
  const publishedArticles = articles?.filter(a => a.status === 'public').length || 0;
  const draftArticles = articles?.filter(a => a.status === 'draft').length || 0;
  
  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground mt-1">Welcome back to your writing dashboard.</p>
        </div>
        <div className="mt-4 md:mt-0">
          <Button asChild className="gap-2">
            <Link to="/articles/new">
              <FileText className="h-4 w-4" />
              Create New Article
            </Link>
          </Button>
        </div>
      </div>
      
      {/* Stats Overview */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Articles"
          value={totalArticles}
          icon={<FileText className="h-4 w-4" />}
          trend="neutral"
        />
        <StatCard
          title="Published"
          value={publishedArticles}
          icon={<BookOpen className="h-4 w-4" />}
          description={`${Math.round((publishedArticles / totalArticles) * 100) || 0}% of total`}
          trend="up"
        />
        <StatCard
          title="Drafts"
          value={draftArticles}
          icon={<AlertCircle className="h-4 w-4" />}
          trend="neutral"
        />
        <StatCard
          title="Publications"
          value={publications?.length || 0}
          icon={<Users className="h-4 w-4" />}
          trend="neutral"
        />
      </div>
      
      {/* Recent Articles */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold">Recent Articles</h3>
          <Button variant="outline" size="sm" asChild>
            <Link to="/articles" className="gap-1">
              View all <ExternalLink className="h-3 w-3 ml-1" />
            </Link>
          </Button>
        </div>
        
        <div className="space-y-4">
          {articlesLoading ? (
            <Card className="p-8">
              <div className="h-8 animate-pulse flex items-center justify-center">
                <p className="text-muted-foreground">Loading articles...</p>
              </div>
            </Card>
          ) : articles && articles.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
              {articles.map(article => (
                <Card key={article.id} className="overflow-hidden hover:shadow-md transition-all">
                  <CardContent className="p-6">
                    <div className="flex flex-col space-y-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Badge variant={article.status === 'public' ? 'default' : 'outline'} className="mb-2">
                            {article.status === 'public' ? 'Published' : 'Draft'}
                          </Badge>
                          <div className="flex items-center text-xs text-muted-foreground">
                            <Clock className="h-3 w-3 mr-1" />
                            <span>{formatDate(article.created_at)}</span>
                          </div>
                        </div>
                        <Link to={`/articles/${article.id}`} className="text-xl font-medium hover:underline line-clamp-1">
                          {article.title}
                        </Link>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {truncateText(article.subtitle || article.content, 120)}
                        </p>
                      </div>
                      <div className="flex items-center justify-between pt-2">
                        <div className="flex items-center">
                          <Button asChild variant="ghost" size="sm" className="px-0 text-primary hover:bg-transparent hover:text-primary/80">
                            <Link to={`/articles/${article.id}/edit`}>
                              Edit
                            </Link>
                          </Button>
                        </div>
                        <Button asChild variant="outline" size="sm">
                          <Link to={`/articles/${article.id}`}>
                            View Article
                          </Link>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <div className="rounded-full bg-primary/10 h-16 w-16 mx-auto flex items-center justify-center mb-4">
                  <FileText className="h-8 w-8 text-primary" />
                </div>
                <CardTitle className="mb-2">No articles yet</CardTitle>
                <CardDescription className="mb-4">Create your first article to get started.</CardDescription>
                <Button asChild>
                  <Link to="/articles/new">Create Your First Article</Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
} 