import React, { useEffect } from 'react';
import { useChatStore } from '../../store/chatStore';
import { useTaskStore } from '../../store/taskStore';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Loader, AlertCircle, Info, FileText, RefreshCw } from 'lucide-react';

const ActivityFeed = () => {
  const { activities } = useChatStore();
  const { activeJobs, loading } = useTaskStore();

  const getIcon = (type) => {
    switch (type) {
      case 'success': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'loading': return <Loader className="w-4 h-4 text-indigo-400 animate-spin" />;
      case 'update': return <RefreshCw className="w-4 h-4 text-blue-400" />;
      case 'user': return <FileText className="w-4 h-4 text-gray-400" />;
      case 'upload': return <FileText className="w-4 h-4 text-indigo-400" />;
      default: return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  const jobEntries = Object.entries(activeJobs);

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b border-white/5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-gray-300">Activity Feed</h2>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {jobEntries.length > 0 && (
          <div className="mb-3">
            <div className="px-2 py-1 text-xs text-gray-500 uppercase tracking-wider">Background Tasks</div>
            <div className="mt-1 space-y-1">
              {jobEntries.map(([jobName, status]) => (
                <motion.div
                  key={jobName}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5"
                >
                  <Loader className="w-3 h-3 text-indigo-400 animate-spin" />
                  <span className="flex-1 text-sm text-gray-300 truncate">{jobName}</span>
                  <span className="text-xs text-gray-500">{status}</span>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {activities.length === 0 && jobEntries.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-gray-500 text-sm">
              No recent activity
            </div>
          ) : (
            activities.map((activity) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex items-start gap-3 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
              >
                {getIcon(activity.type)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300">{activity.text}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">
                    {new Date(activity.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ActivityFeed;