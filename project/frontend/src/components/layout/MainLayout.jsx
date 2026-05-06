import React from 'react';
import Sidebar from '../ui/Sidebar';
import ChatWindow from '../chat/index';
import ChatInput from '../chat/ChatInput';
import ActivityFeed from '../ui/ActivityFeed';

const MainLayout = () => {
  return (
    <div className="flex h-screen w-full bg-black text-white overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <ChatWindow />
        <ChatInput />
      </div>
      
      <aside className="w-[300px] h-full border-l border-white/5 bg-black/20 backdrop-blur-xl">
        <ActivityFeed />
      </aside>
    </div>
  );
};

export default MainLayout;