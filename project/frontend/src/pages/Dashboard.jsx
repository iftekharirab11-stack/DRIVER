import React from 'react';
import { useAppContext } from '../state/appState';
import MainLayout from '../layout/MainLayout';
import ActivityPanel from '../components/ActivityPanel';

const Dashboard = () => {
  const { connections, activities } = useAppContext();

  const connectedCount = Object.values(connections).filter(c => c.connected).length;

  return (
    <MainLayout>
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Connected Apps</h3>
            <p className="text-3xl font-bold text-gray-900">{connectedCount}/3</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Recent Activity</h3>
            <p className="text-3xl font-bold text-gray-900">{activities.length}</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500 mb-2">System Status</h3>
            <p className="text-lg font-medium text-green-600">Healthy</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ActivityPanel />
          
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full text-left px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">
                Refresh Connections
              </button>
              <button className="w-full text-left px-4 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100">
                Clear Activity Log
              </button>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Dashboard;