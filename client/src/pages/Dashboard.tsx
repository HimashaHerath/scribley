import { useCallback, useMemo } from 'react';
import { useFetch, useArticles, useCurrentUser, usePublications } from '@/lib/hooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatDate, truncateText } from '@/lib/utils';
import { BarChart3, BookOpen, FileText, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

// Stats card component
const StatCard = ({ title, value, icon, description }: { 
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
}) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      {icon}
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      {description && <p className="text-xs text-muted-foreground">{description}</p>}
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
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <div className="mt-2 md:mt-0">
          <Button asChild>
            <Link to="/articles/new">
              Create New Article
            </Link>
          </Button>
        </div>
      </div>
      
      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Articles"
          value={totalArticles}
          icon={<FileText className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          title="Published"
          value={publishedArticles}
          icon={<BookOpen className="h-4 w-4 text-muted-foreground" />}
          description={`${Math.round((publishedArticles / totalArticles) * 100) || 0}% of total`}
        />
        <StatCard
          title="Drafts"
          value={draftArticles}
          icon={<FileText className="h-4 w-4 text-muted-foreground" />}
        />
        <StatCard
          title="Publications"
          value={publications?.length || 0}
          icon={<Users className="h-4 w-4 text-muted-foreground" />}
        />
      </div>
      
      {/* Recent Articles */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Recent Articles</h3>
        
        <div className="space-y-4">
          {articlesLoading ? (
            <p>Loading articles...</p>
          ) : articles && articles.length > 0 ? (
            articles.map(article => (
              <Card key={article.id}>
                <CardContent className="p-4">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                    <div className="space-y-1">
                      <Link to={`/articles/${article.id}`} className="text-lg font-medium hover:underline">
                        {article.title}
                      </Link>
                      <p className="text-sm text-muted-foreground">
                        {truncateText(article.subtitle || article.content, 100)}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{formatDate(article.created_at)}</span>
                        <span>•</span>
                        <span className="capitalize">{article.status}</span>
                      </div>
                    </div>
                    <div className="mt-2 md:mt-0 md:ml-4">
                      <Button asChild variant="outline" size="sm">
                        <Link to={`/articles/${article.id}`}>
                          View Article
                        </Link>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="p-6 text-center">
                <p className="mb-2">No articles yet.</p>
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