import { useState } from 'react';
import type { ReactNode } from 'react';
import { Button } from '../ui/button';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  BookOpen, 
  Settings, 
  Menu, 
  X,
  LogOut,
  PlusCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFetch } from '@/lib/hooks';
import { userService, type User } from '@/lib/api';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { toast } from 'sonner';
import { Skeleton } from '../ui/skeleton';

// Navigation item type definition
type NavItem = {
  icon: ReactNode;
  label: string;
  href: string;
};

// Sidebar navigation items
const NAV_ITEMS: NavItem[] = [
  { icon: <LayoutDashboard size={20} />, label: 'Dashboard', href: '/dashboard' },
  { icon: <FileText size={20} />, label: 'Articles', href: '/articles' },
  { icon: <BookOpen size={20} />, label: 'Publications', href: '/publications' },
  { icon: <Settings size={20} />, label: 'Settings', href: '/settings' },
];

interface SidebarItemProps {
  icon: ReactNode;
  label: string;
  href: string;
  active?: boolean;
}

function SidebarItem({ icon, label, href, active }: SidebarItemProps) {
  return (
    <Link to={href} className="w-full">
      <Button
        variant={active ? "default" : "ghost"}
        className={cn(
          "w-full justify-start gap-2 pl-2",
          active ? "bg-primary text-primary-foreground hover:bg-primary/90" : ""
        )}
      >
        {icon}
        <span>{label}</span>
      </Button>
    </Link>
  );
}

// Sidebar component
function Sidebar({ 
  isOpen, 
  onClose, 
  activePath 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  activePath: string;
}) {
  const navigate = useNavigate();
  
  return (
    <>
      {/* Mobile sidebar backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black/50 lg:hidden" 
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside 
        className={cn(
          "fixed top-0 left-0 z-30 h-full w-64 bg-card transform transition-transform duration-200 ease-in-out lg:static lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full border-r">
          <div className="p-4 flex items-center justify-between border-b">
            <h1 className="text-xl font-semibold">Scribley</h1>
            <Button variant="ghost" size="icon" onClick={onClose} className="lg:hidden">
              <X size={20} />
            </Button>
          </div>
          
          <div className="flex-1 py-4 space-y-1 px-3">
            {NAV_ITEMS.map((item) => (
              <SidebarItem 
                key={item.href}
                icon={item.icon} 
                label={item.label} 
                href={item.href} 
                active={activePath === item.href || (item.href !== '/dashboard' && activePath.startsWith(item.href))}
              />
            ))}
          </div>
          
          <div className="p-4 border-t">
            <Button 
              className="w-full justify-start gap-2"
              onClick={() => navigate('/articles/new')}
            >
              <PlusCircle size={20} />
              <span>New Article</span>
            </Button>
          </div>
        </div>
      </aside>
    </>
  );
}

// User menu component
function UserMenu({ 
  user, 
  isLoading, 
  onLogout 
}: { 
  user: User | null; 
  isLoading: boolean;
  onLogout: () => void;
}) {
  const getInitials = () => {
    if (!user?.name) return 'U';
    return user.name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  return (
    <div className="flex items-center gap-2">
      {isLoading ? (
        <Skeleton className="h-8 w-8 rounded-full" />
      ) : user ? (
        <>
          <Avatar>
            <AvatarImage src={user.image_url} alt={user.name} />
            <AvatarFallback>{getInitials()}</AvatarFallback>
          </Avatar>
          <span className="hidden md:inline-block font-medium">{user.name}</span>
        </>
      ) : (
        <span className="text-sm text-muted-foreground">Not connected</span>
      )}
      <Button variant="ghost" size="icon" onClick={onLogout} title="Logout">
        <LogOut size={20} />
      </Button>
    </div>
  );
}

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  
  const { data: user, loading: isLoading } = useFetch(
    userService.getCurrentUser,
    []
  );
  
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const closeSidebar = () => setSidebarOpen(false);
  
  const handleLogout = () => {
    localStorage.removeItem('MEDIUM_API_TOKEN');
    toast.success('Logged out successfully');
    
    setTimeout(() => {
      window.location.reload();
    }, 500);
  };
  
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={closeSidebar} 
        activePath={location.pathname}
      />
      
      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 border-b flex items-center justify-between px-4 lg:px-6">
          <Button variant="ghost" size="icon" onClick={toggleSidebar} className="lg:hidden">
            <Menu size={20} />
          </Button>
          
          <div className="ml-auto">
            <UserMenu 
              user={user} 
              isLoading={isLoading} 
              onLogout={handleLogout} 
            />
          </div>
        </header>
        
        {/* Main content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
} 