'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Users, 
  Building2, 
  CheckSquare, 
  Calendar,
  BarChart3,
  Bot,
  Settings,
  LogOut,
  Mail,
  BookOpen,
  Network
} from 'lucide-react';
import { useRouter } from 'next/navigation';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/contacts', label: 'Contacts', icon: Users },
  { href: '/opportunities', label: 'Opportunities', icon: Building2 },
  { href: '/tasks', label: 'Tasks', icon: CheckSquare },
  { href: '/calendar', label: 'Calendar', icon: Calendar },
  { href: '/emails', label: 'Emails', icon: Mail },
  { href: '/reports', label: 'Reports', icon: BarChart3 },
  { href: '/business', label: 'Business Background', icon: BookOpen },
  { href: '/knowledge-graph', label: 'Knowledge Graph', icon: Network },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const faceRef = useRef<HTMLDivElement | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [isWaking, setIsWaking] = useState(false);
  const rafRef = useRef<number | null>(null);
  const pupilTargetRef = useRef({ x: 0, y: 0 });
  const pupilCurrentRef = useRef({ x: 0, y: 0 });
  const thinkingTimeoutRef = useRef<number | null>(null);
  const wakeTimeoutRef = useRef<number | null>(null);
  
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/');
  };

  useEffect(() => {
    const animatePupils = () => {
      const current = pupilCurrentRef.current;
      const target = pupilTargetRef.current;
      const nextX = current.x + (target.x - current.x) * 0.2;
      const nextY = current.y + (target.y - current.y) * 0.2;
      pupilCurrentRef.current = { x: nextX, y: nextY };

      if (faceRef.current) {
        faceRef.current.style.setProperty('--pupil-x', `${nextX}px`);
        faceRef.current.style.setProperty('--pupil-y', `${nextY}px`);
      }

      if (Math.hypot(target.x - nextX, target.y - nextY) > 0.05) {
        rafRef.current = window.requestAnimationFrame(animatePupils);
      } else {
        rafRef.current = null;
      }
    };

    const handleMouseMove = (event: MouseEvent) => {
      const face = faceRef.current;
      if (!face) {
        return;
      }
      const rect = face.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const dx = event.clientX - centerX;
      const dy = event.clientY - centerY;
      const distance = Math.hypot(dx, dy) || 1;
      const maxOffset = 3.5;
      const influence = Math.min(1, distance / 80);
      pupilTargetRef.current = {
        x: (dx / distance) * maxOffset * influence,
        y: (dy / distance) * maxOffset * influence,
      };

      if (rafRef.current === null) {
        rafRef.current = window.requestAnimationFrame(animatePupils);
      }
    };

    const handlePointerDown = () => {
      setIsThinking(true);
      if (thinkingTimeoutRef.current) {
        window.clearTimeout(thinkingTimeoutRef.current);
      }
      thinkingTimeoutRef.current = window.setTimeout(() => {
        setIsThinking(false);
        thinkingTimeoutRef.current = null;
      }, 1200);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('pointerdown', handlePointerDown);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('pointerdown', handlePointerDown);
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current);
      }
      if (thinkingTimeoutRef.current) {
        window.clearTimeout(thinkingTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    setIsWaking(true);
    if (wakeTimeoutRef.current) {
      window.clearTimeout(wakeTimeoutRef.current);
    }
    wakeTimeoutRef.current = window.setTimeout(() => {
      setIsWaking(false);
      wakeTimeoutRef.current = null;
    }, 1200);

    return () => {
      if (wakeTimeoutRef.current) {
        window.clearTimeout(wakeTimeoutRef.current);
      }
    };
  }, [pathname]);

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

        <div className="rounded-2xl bg-blue-50/80 border border-blue-100 px-4 py-4 group">
          <div className="flex items-start gap-3">
            <div
              ref={faceRef}
              className={`ai-face animate-float transition-transform duration-300 group-hover:-translate-y-1 ${
                isThinking ? 'is-thinking' : ''
              } ${isWaking ? 'is-waking' : ''}`}
            >
              <span className="ai-hat" />
              <div className="ai-eyes">
                <span className="ai-eye">
                  <span className="ai-pupil" />
                </span>
                <span className="ai-eye">
                  <span className="ai-pupil" />
                </span>
              </div>
              <span className="ai-mouth" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 text-sm font-semibold text-ink">
                <Bot size={16} className="text-blue-600" />
                AI Chatbot (GLM)
              </div>
              <p className="text-xs text-muted mt-2">
                Suggestions adapt to the open page.
              </p>
              <Link 
                href="/agent-manager"
                className="mt-3 inline-flex items-center rounded-full bg-white px-3 py-1 text-[11px] font-semibold text-blue-700 hover:bg-blue-50 transition-colors cursor-pointer"
              >
                Manage Agent
              </Link>
            </div>
          </div>
        </div>

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