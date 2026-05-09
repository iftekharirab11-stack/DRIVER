import { useEffect } from 'react';
import { useMemoryStore } from '../store/memoryStore';
import { useActivityStore, ACTIVITY_TYPES } from '../store/activityStore';

/**
 * Hook to integrate memory system with session lifecycle
 */
export const useMemoryIntegration = () => {
  const { addToMemoryArray, getMemory } = useMemoryStore();
  const { addActivity } = useActivityStore();

  // Initialize memory system when component mounts
  useEffect(() => {
    // Add initial memory activity
    addActivity({
      type: ACTIVITY_TYPES.MEMORY,
      text: 'Memory system initialized',
    });

    // Check if we have existing memory data
    const username = getMemory('username');
    if (username) {
      addActivity({
        type: ACTIVITY_TYPES.MEMORY,
        text: `Welcome back, ${username}! Memory restored.`,
      });
    } else {
      addActivity({
        type: ACTIVITY_TYPES.MEMORY,
        text: 'New session started. Memory system ready.',
      });
    }
  }, [addActivity, getMemory]);

  /**
   * Set username in memory
   * @param {string} username
   */
  const setUsername = (username) => {
    addToMemoryArray('username', username);
    addActivity({
      type: ACTIVITY_TYPES.MEMORY,
      text: `Username set: ${username}`,
    });
  };

  /**
   * Add recent task to memory
   * @param {string} taskDescription
   */
  const rememberTask = (taskDescription) => {
    addToMemoryArray('recentTasks', taskDescription);
  };

  /**
   * Add project name to memory
   * @param {string} projectName
   */
  const rememberProject = (projectName) => {
    addToMemoryArray('projectNames', projectName);
  };

  /**
   * Add topic to memory
   * @param {string} topic
   */
  const rememberTopic = (topic) => {
    addToMemoryArray('previousTopics', topic);
  };

  /**
   * Set user preference
   * @param {string} key
   * @param {any} value
   */
  const setPreference = (key, value) => {
    useMemoryStore.getState().saveMemory('preferences', {
      ...getMemory('preferences'),
      [key]: value
    });
  };

  return {
    setUsername,
    rememberTask,
    rememberProject,
    rememberTopic,
    setPreference,
    getMemory,
  };
};