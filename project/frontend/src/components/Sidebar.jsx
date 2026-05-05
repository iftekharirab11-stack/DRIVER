import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAppContext } from '../state/appState';

const Sidebar = () => {
  const { sidebarOpen, closeSidebar } = useAppContext();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'MCP Connections', path: '/connections' },
    { name: 'Chat History', path: '/history' }
  ];

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={closeSidebar}
        />
      )}
      
      <aside className={`
        fixed top-0 left-0 h-full w-64 bg-gray-900 text-white z-30
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:z-0
      `}>
        <div className="p-4 border-b border-gray-800">
          <h2 className="text-xl font-bold">MCP Dashboard</h2>
        </div>
        
        <nav className="p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  onClick={closeSidebar}
                  className={({ isActive }) => `
                    block px-4 py-2 rounded-lg transition-colors
                    ${isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'}
                  `}
                >
                  {item.name}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;