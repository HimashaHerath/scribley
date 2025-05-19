import { useState, useEffect } from 'react';
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
          "w-full justify-start gap-3 pl-3 py-6 transition-all hover:translate-x-1",
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
  
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024 && isOpen) {
        onClose();
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isOpen, onClose]);
  
  return (
    <>
      {/* Mobile sidebar backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm transition-opacity lg:hidden" 
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside 
        className={cn(
          "fixed top-0 left-0 z-30 h-full w-72 bg-card shadow-lg transform transition-transform duration-300 ease-in-out lg:shadow-none lg:static lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full border-r">
          <div className="p-5 flex items-center justify-between border-b">
            <h1 className="text-2xl font-bold tracking-tight">Scribley</h1>
            <Button variant="ghost" size="icon" onClick={onClose} className="lg:hidden hover:bg-background/10">
              <X size={20} />
            </Button>
          </div>
          
          <div className="flex-1 py-6 space-y-2 px-4">
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
              className="w-full justify-start gap-2 py-6 bg-primary/10 hover:bg-primary/20 text-primary"
              variant="ghost"
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
    <div className="flex items-center gap-3">
      {isLoading ? (
        <Skeleton className="h-10 w-10 rounded-full" />
      ) : user ? (
        <>
          <Avatar className="h-10 w-10 border-2 border-primary/10">
            <AvatarImage src={user.image_url} alt={user.name} />
            <AvatarFallback className="bg-primary/10 text-primary font-medium">{getInitials()}</AvatarFallback>
          </Avatar>
          <div className="hidden md:block">
            <span className="font-medium">{user.name}</span>
          </div>
        </>
      ) : (
        <span className="text-sm text-muted-foreground">Not connected</span>
      )}
      <Button variant="ghost" size="icon" onClick={onLogout} title="Logout" className="hover:bg-destructive/10 hover:text-destructive">
        <LogOut size={18} />
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
  
  // Close sidebar when navigating
  useEffect(() => {
    closeSidebar();
  }, [location.pathname]);
  
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
        <header className="h-16 border-b flex items-center justify-between px-4 lg:px-6 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <Button variant="ghost" size="icon" onClick={toggleSidebar} className="lg:hidden hover:bg-background/10">
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
        <main className="flex-1 p-4 lg:p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
} 