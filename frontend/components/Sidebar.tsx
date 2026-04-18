'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Users, 
  Building2, 
  CheckSquare, 
  BarChart3,
  Settings,
  LogOut
} from 'lucide-react';
import { useRouter } from 'next/navigation';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/contacts', label: 'Contacts', icon: Users },
  { href: '/opportunities', label: 'Opportunities', icon: Building2 },
  { href: '/tasks', label: 'Tasks', icon: CheckSquare },
  { href: '/reports', label: 'Reports', icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/');
  };

  return (
    <aside className="w-full md:w-72 md:h-screen md:sticky md:top-0">
      <div className="panel h-full flex flex-col gap-4 md:gap-6 p-4 md:p-6">
        <div className="flex items-center justify-between md:justify-start gap-3">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white flex items-center justify-center shadow-soft">
              <span className="text-sm font-semibold">UM</span>
            </div>
            <div>
              <div className="page-kicker">CRM</div>
              <div className="text-lg font-semibold text-ink">Studio</div>
            </div>
          </div>
          <span className="pill hidden md:inline-flex">All Teams</span>
        </div>

        <nav className="flex md:flex-col gap-2 overflow-x-auto md:overflow-visible pb-2 md:pb-0">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-blue-700 text-white shadow-soft'
                    : 'text-muted hover:bg-white/70'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-white' : 'text-muted'} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-2">
          <Link
            href="/settings"
            className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold text-muted hover:bg-white/70 transition-colors"
          >
            <Settings size={18} />
            Settings
          </Link>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-semibold text-rose-700 hover:bg-rose-50 transition-colors w-full"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
}