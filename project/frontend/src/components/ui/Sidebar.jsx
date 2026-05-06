import React from 'react';
import { Plus, MessageSquare, FolderOpen, Settings, Plug, History, User, Activity } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { icon: Plus, label: 'New Chat', key: 'new-chat' },
    { icon: MessageSquare, label: 'Chats', key: 'chats' },
    { icon: FolderOpen, label: 'Workspaces', key: 'workspaces' },
    { icon: Plug, label: 'Connected Apps', key: 'apps' },
    { icon: Activity, label: 'Activity Feed', key: 'activity' },
    { icon: History, label: 'History', key: 'history' },
    { icon: Settings, label: 'Settings', key: 'settings' },
  ];

  return (
    <aside className="w-[240px] h-full flex flex-col bg-black/30 backdrop-blur-xl border-r border-white/5">
      <div className="p-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <span className="text-white font-semibold text-lg">Driver AI</span>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.key}>
              <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 hover:text-white transition-all duration-200">
                <item.icon className="w-5 h-5" />
                <span className="text-sm font-medium">{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-white/5">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-white/5 hover:text-white transition-all duration-200">
          <div className="w-6 h-6 rounded-full bg-indigo-600/20 flex items-center justify-center">
            <User className="w-4 h-4 text-indigo-400" />
          </div>
          <span className="text-sm font-medium">Profile</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;