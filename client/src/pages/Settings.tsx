import { useState, useEffect } from 'react';
import { userService } from '@/lib/api';
import { useFetch } from '@/lib/hooks';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { Loader2, Save, Key, User, RefreshCw } from 'lucide-react';

// Helper component for external links
function ExternalLink({ href, children }: { href: string, children: React.ReactNode }) {
  return (
    <a 
      href={href} 
      target="_blank" 
      rel="noreferrer"
      className="text-primary mx-1 underline"
    >
      {children}
    </a>
  );
}

// API Token settings card
function ApiTokenCard({ token, setToken, isTokenSet, onSave, isSaving }: {
  token: string;
  setToken: (token: string) => void;
  isTokenSet: boolean;
  onSave: () => void;
  isSaving: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Medium API Token</CardTitle>
        <CardDescription>
          Enter your Medium API token to connect with your account.
          You can get your token from the 
          <ExternalLink href="https://medium.com/me/settings">
            Medium Settings
          </ExternalLink>
          page under "Integration tokens".
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Label htmlFor="api-token">API Token</Label>
          <div className="flex">
            <Input
              id="api-token"
              type="text"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Enter your Medium API token"
              className="flex-1"
            />
            {isTokenSet && (
              <Button 
                variant="outline" 
                className="ml-2" 
                onClick={() => setToken('')}
              >
                Clear
              </Button>
            )}
          </div>
          {isTokenSet && (
            <p className="text-sm text-muted-foreground">
              Token is set. Leave masked to keep the same token.
            </p>
          )}
        </div>
      </CardContent>
      <CardFooter>
        <Button 
          onClick={onSave} 
          disabled={isSaving}
        >
          {isSaving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
            </>
          ) : (
            <>
              <Key className="mr-2 h-4 w-4" /> Save Token
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}

// API Connection status card
function ConnectionStatusCard({ user, loading, error, onRefresh }: {
  user: any;
  loading: boolean;
  error: Error | null;
  onRefresh: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>API Connection Status</CardTitle>
        <CardDescription>
          Check if your API token is working correctly
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center space-x-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Checking connection...</span>
          </div>
        ) : error ? (
          <div className="text-destructive">
            <p className="font-medium">Connection Error</p>
            <p className="text-sm">{error.message}</p>
          </div>
        ) : user ? (
          <div className="space-y-2">
            <p className="text-green-600 font-medium">✓ Connected to Medium API</p>
            <div className="text-sm space-y-1">
              <p><span className="font-medium">Username:</span> {user.username}</p>
              <p><span className="font-medium">Name:</span> {user.name}</p>
              <p>
                <span className="font-medium">Profile URL:</span> 
                <ExternalLink href={user.url}>{user.url}</ExternalLink>
              </p>
            </div>
          </div>
        ) : (
          <p>No connection information available</p>
        )}
      </CardContent>
      <CardFooter>
        <Button variant="outline" onClick={onRefresh} disabled={loading}>
          <RefreshCw className="mr-2 h-4 w-4" /> 
          Refresh Connection
        </Button>
      </CardFooter>
    </Card>
  );
}

// Account information card
function AccountInfoCard({ user, loading }: { user: any; loading: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Account Information</CardTitle>
        <CardDescription>
          Your Medium account details
        </CardDescription>
      </CardHeader>
      <CardContent>
        {user ? (
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              {user.image_url ? (
                <img 
                  src={user.image_url} 
                  alt={user.name} 
                  className="w-16 h-16 rounded-full"
                />
              ) : (
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                  <User className="h-8 w-8 text-muted-foreground" />
                </div>
              )}
              <div>
                <h3 className="font-medium text-lg">{user.name}</h3>
                <p className="text-muted-foreground">@{user.username}</p>
              </div>
            </div>
            
            <div className="border-t pt-4">
              <p className="text-sm text-muted-foreground">
                To update your profile information, please visit your 
                <ExternalLink href="https://medium.com/me/settings">
                  Medium Settings
                </ExternalLink>
                page.
              </p>
            </div>
          </div>
        ) : loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="py-8 text-center">
            <p>Please set your API token to view account information</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function Settings() {
  const [apiToken, setApiToken] = useState('');
  const [isTokenSet, setIsTokenSet] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Fetch user data
  const { data: user, loading: loadingUser, error: userError, refetch } = useFetch(
    userService.getCurrentUser,
    []
  );

  // Check if token is set
  useEffect(() => {
    const token = localStorage.getItem('MEDIUM_API_TOKEN') || '';
    setApiToken(token ? '••••••••••••••••••••••••••••••' : '');
    setIsTokenSet(!!token);
  }, []);

  const handleTokenSave = () => {
    if (!apiToken) {
      toast.error('Please enter a valid API token');
      return;
    }

    setIsSaving(true);
    
    try {
      // Only save if it's not masked
      if (!apiToken.includes('•')) {
        localStorage.setItem('MEDIUM_API_TOKEN', apiToken);
        toast.success('API token saved successfully');
        
        // Reload the page to apply the new token
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        toast.info('Token unchanged');
      }
    } catch (error) {
      toast.error('Failed to save API token');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage your API token and preferences</p>
      </div>

      <Tabs defaultValue="api">
        <TabsList>
          <TabsTrigger value="api">API Settings</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
        </TabsList>
        
        <TabsContent value="api" className="space-y-4 mt-4">
          <ApiTokenCard 
            token={apiToken}
            setToken={setApiToken}
            isTokenSet={isTokenSet}
            onSave={handleTokenSave}
            isSaving={isSaving}
          />

          <ConnectionStatusCard
            user={user}
            loading={loadingUser}
            error={userError}
            onRefresh={refetch}
          />
        </TabsContent>
        
        <TabsContent value="account" className="mt-4">
          <AccountInfoCard 
            user={user}
            loading={loadingUser}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
} 