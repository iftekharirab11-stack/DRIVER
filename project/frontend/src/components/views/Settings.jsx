import React from 'react';

const Settings = () => {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Settings</h2>
        <p className="text-gray-400">Configure your application preferences.</p>

        <div className="mt-6 space-y-6">
          <div className="bg-black/20 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-3">General Settings</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Dark Mode</span>
                <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                  <input type="checkbox" name="toggle" className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer" />
                  <label className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer"></label>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-black/20 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-3">Advanced Settings</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Developer Mode</span>
                <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                  <input type="checkbox" name="toggle" className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer" />
                  <label className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer"></label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;