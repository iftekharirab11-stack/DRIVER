import React from 'react';

const ConnectedApps = () => {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Connected Apps</h2>
        <p className="text-gray-400">Manage your connected applications and integrations.</p>

        <div className="mt-6 bg-black/20 rounded-lg p-4">
          <div className="text-center py-8 text-gray-500">
            <p>No connected apps found</p>
            <p className="text-sm mt-2">Connect apps to extend functionality</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectedApps;