import React from 'react';
import { useAppContext } from '../state/appState';

const ActivityPanel = () => {
  const { activities } = useAppContext();

  return (
    <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Activity Monitor</h3>
      
      {activities.length === 0 ? (
        <p className="text-gray-500 text-center py-4">No activity yet</p>
      ) : (
        <ul className="space-y-3 max-h-96 overflow-y-auto">
          {activities.map((activity) => (
            <li key={activity.id} className="flex items-start space-x-3 p-2 bg-gray-50 rounded-lg">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-700">{activity.message}</p>
                <span className="text-xs text-gray-500">{activity.timestamp}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ActivityPanel;