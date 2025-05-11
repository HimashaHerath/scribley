import { useState, useMemo } from 'react';
import { useFetch } from '@/lib/hooks';
import { publicationService, type Publication } from '@/lib/api';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  ExternalLink, 
  Users, 
  BookOpen, 
  Loader2, 
  ChevronDown, 
  ChevronRight, 
  Globe 
} from 'lucide-react';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Skeleton } from '../components/ui/skeleton';

// Types and interfaces
type Contributor = {
  userId: string;
  role: string;
};

type ContributorsByRole = Record<string, Contributor[]>;
type ExpandedRoles = Record<string, boolean>;

// Helper functions
const formatUserId = (userId: string): string => {
  if (userId.length > 12) {
    return `${userId.substring(0, 6)}...${userId.substring(userId.length - 4)}`;
  }
  return userId;
};

const getUserInitials = (userId: string): string => {
  return userId.substring(0, 2).toUpperCase();
};

// Role badge component
function RoleBadge({ role }: { role: string }) {
  const variant = role === 'editor' ? 'success' : 'secondary';
  return <Badge variant={variant}>{role}</Badge>;
}

// Contributor avatar component
function ContributorAvatar({ userId }: { userId: string }) {
  return (
    <Avatar className="h-7 w-7 bg-primary/10">
      <AvatarFallback className="text-xs">
        {getUserInitials(userId)}
      </AvatarFallback>
    </Avatar>
  );
}

// Contributors list component
function ContributorsList({ contributors }: { contributors: Contributor[] }) {
  const [expandedRoles, setExpandedRoles] = useState<ExpandedRoles>({
    editor: true,
    writer: true
  });
  
  // Group contributors by role
  const contributorsByRole = useMemo<ContributorsByRole>(() => {
    if (!contributors) return {};
    
    return contributors.reduce((acc, contributor) => {
      const role = contributor.role || 'other';
      if (!acc[role]) acc[role] = [];
      acc[role].push(contributor);
      return acc;
    }, {} as ContributorsByRole);
  }, [contributors]);
  
  // Toggle role expansion
  const toggleRoleExpansion = (role: string) => {
    setExpandedRoles(prev => ({
      ...prev,
      [role]: !prev[role]
    }));
  };
  
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-medium">Contributors:</h4>
        <span className="text-xs text-muted-foreground">
          Total: {contributors.length}
        </span>
      </div>
      
      <p className="text-xs text-muted-foreground mb-3">
        Medium API only provides user IDs for contributors, not usernames or profile images.
      </p>
      
      {/* Display contributor groups by role */}
      {Object.entries(contributorsByRole).map(([role, roleContributors]) => (
        <div key={role} className="border rounded-md overflow-hidden transition-all">
          <button 
            className="w-full flex justify-between items-center p-2 bg-muted/30 hover:bg-muted/50 text-left"
            onClick={() => toggleRoleExpansion(role)}
            aria-expanded={expandedRoles[role]}
            aria-controls={`role-${role}-panel`}
          >
            <div className="flex items-center gap-2">
              {expandedRoles[role] ? 
                <ChevronDown className="h-4 w-4" /> : 
                <ChevronRight className="h-4 w-4" />
              }
              <RoleBadge role={role} />
            </div>
            <span className="text-xs text-muted-foreground">
              {roleContributors.length} {roleContributors.length === 1 ? 'member' : 'members'}
            </span>
          </button>
          
          {expandedRoles[role] && (
            <div 
              className="space-y-1 p-2 animate-fadeIn"
              id={`role-${role}-panel`}
              role="region"
            >
              {roleContributors.slice(0, 5).map(contributor => (
                <div 
                  key={contributor.userId} 
                  className="flex items-center justify-between p-1.5 rounded bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <ContributorAvatar userId={contributor.userId} />
                    <span className="text-xs text-muted-foreground">
                      {formatUserId(contributor.userId)}
                    </span>
                  </div>
                </div>
              ))}
              
              {/* Show message if there are more contributors in this role */}
              {roleContributors.length > 5 && (
                <div className="py-1 px-2 text-xs text-center text-muted-foreground">
                  +{roleContributors.length - 5} more {role}s not shown
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// Publication card component
function PublicationCard({ publication }: { publication: Publication }) {
  const [showContributors, setShowContributors] = useState(false);
  
  const { 
    data: contributors, 
    loading: loadingContributors,
    error: contributorsError 
  } = useFetch<Contributor[]>(
    () => showContributors ? publicationService.getContributors(publication.id) : Promise.resolve([]),
    [showContributors, publication.id]
  );

  return (
    <Card className="h-full flex flex-col shadow-sm hover:shadow transition-shadow">
      <CardHeader>
        <div className="flex items-start gap-4">
          {publication.image_url ? (
            <img 
              src={publication.image_url} 
              alt={publication.name} 
              className="w-16 h-16 rounded-md object-cover border"
            />
          ) : (
            <div className="w-16 h-16 rounded-md bg-muted flex items-center justify-center">
              <Globe className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
          <div className="flex-1">
            <CardTitle>{publication.name}</CardTitle>
            {publication.description && (
              <CardDescription className="mt-1 line-clamp-2">
                {publication.description}
              </CardDescription>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1">
        <div className="space-y-4">
          <a 
            href={publication.url} 
            target="_blank"
            rel="noopener noreferrer" 
            className="text-sm text-blue-600 hover:underline flex items-center"
          >
            <ExternalLink className="mr-1 h-3 w-3" /> View on Medium
          </a>
          
          {showContributors && (
            <div className="mt-4">
              {loadingContributors ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : contributorsError ? (
                <div className="p-3 text-sm text-destructive border border-destructive/20 rounded-md bg-destructive/10">
                  Error loading contributors: {contributorsError.message}
                </div>
              ) : contributors && contributors.length > 0 ? (
                <ContributorsList contributors={contributors} />
              ) : (
                <p className="text-sm text-muted-foreground">No contributor data available</p>
              )}
            </div>
          )}
        </div>
      </CardContent>
      
      <CardFooter>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setShowContributors(!showContributors)}
          className="w-full"
          aria-expanded={showContributors}
        >
          <Users className="mr-2 h-4 w-4" />
          {showContributors ? 'Hide Contributors' : 'Show Contributors'}
        </Button>
      </CardFooter>
    </Card>
  );
}

// Publication skeleton for loading state
function PublicationSkeleton() {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-start gap-4">
          <Skeleton className="w-16 h-16 rounded-md" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <Skeleton className="h-4 w-1/3 mb-4" />
      </CardContent>
      <CardFooter>
        <Skeleton className="h-9 w-full" />
      </CardFooter>
    </Card>
  );
}

// Main component
export default function Publications() {
  const { 
    data: publications, 
    loading, 
    error, 
    refetch 
  } = useFetch<Publication[]>(
    publicationService.getAll,
    []
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Publications</h1>
          <p className="text-muted-foreground">Manage your Medium publications</p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => refetch()} 
          disabled={loading}
          aria-label={loading ? "Refreshing publications" : "Refresh publications"}
        >
          {loading ? 
            <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : 
            <BookOpen className="mr-2 h-4 w-4" />
          }
          {loading ? 'Refreshing...' : 'Refresh Publications'}
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => <PublicationSkeleton key={i} />)}
        </div>
      ) : error ? (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Publications</CardTitle>
            <CardDescription>
              There was an error loading your publications. Please try again.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{error.message}</p>
          </CardContent>
          <CardFooter>
            <Button variant="outline" onClick={() => refetch()}>
              Try Again
            </Button>
          </CardFooter>
        </Card>
      ) : publications && publications.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {publications.map(publication => (
            <PublicationCard key={publication.id} publication={publication} />
          ))}
        </div>
      ) : (
        <Card className="border-dashed border-2">
          <CardHeader>
            <CardTitle>No Publications Found</CardTitle>
            <CardDescription>
              You don't have any publications associated with your Medium account yet.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Publications allow you to collaborate with other writers and publish under a shared brand.
              You can create a publication on Medium's website.
            </p>
          </CardContent>
          <CardFooter>
            <Button asChild variant="outline">
              <a href="https://medium.com/new-story" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                Go to Medium
              </a>
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
} 