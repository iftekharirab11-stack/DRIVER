import React, { useState, useEffect, useCallback } from 'react';
import { useDesktopSessionStore } from '../../store/desktopSessionStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { FileProcessor } from '../../services/fileProcessor';
import { showOpenDialog } from '../../electron';
import {
  FolderOpen,
  FileText,
  Code,
  Pdf,
  Database,
  Plus,
  Trash2,
  Search,
  LayoutGrid,
  List,
  MoreVertical
} from 'lucide-react';

const EnhancedWorkspace = () => {
  const [viewMode, setViewMode] = useState('grid');
  const [isDragging, setIsDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [contextMenu, setContextMenu] = useState(null);
  const [showFilePreview, setShowFilePreview] = useState(false);
  const [previewFile, setPreviewFile] = useState(null);

  const {
    currentSession,
    addFileToWorkspace,
    createLocalSession,
    deleteLocalSession
  } = useDesktopSessionStore();

  const { currentFiles, setCurrentFiles } = useWorkspaceStore();

  // Filter files based on search query
  const filteredFiles = currentFiles.filter(file =>
    file.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (file.content && file.content.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      for (let i = 0; i < e.dataTransfer.files.length; i++) {
        const file = e.dataTransfer.files[i];
        try {
          const processedFile = await FileProcessor.processFile(file);
          await addFileToWorkspace(processedFile);

          // Add to recent files if in Electron
          if (window.electronAPI) {
            window.electronAPI.addRecentFile(file.path);
          }
        } catch (error) {
          console.error('File processing error:', error);
        }
      }
    }
  }, [addFileToWorkspace]);

  const handleFileUpload = useCallback(async () => {
    try {
      const options = {
        properties: ['openFile', 'multiSelections'],
        filters: [
          { name: 'All Files', extensions: ['*'] },
          { name: 'Text Files', extensions: ['txt', 'md', 'json', 'csv'] },
          { name: 'Code Files', extensions: ['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rust', 'php', 'rb'] },
          { name: 'PDF Files', extensions: ['pdf'] },
          { name: 'Document Files', extensions: ['docx', 'doc'] }
        ]
      };

      const result = await showOpenDialog(options);
      if (result && result.filePaths && result.filePaths.length > 0) {
        for (const filePath of result.filePaths) {
          // In a real implementation, we would read the file content
          // For now, we'll create a mock file object
          const fileName = filePath.split('/').pop() || filePath.split('\\').pop();
          const fileType = fileName.split('.').pop().toLowerCase();

          const mockFile = {
            fileId: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            fileName: fileName,
            fileType: getFileType(fileType),
            filePath: filePath,
            size: '1.2 MB', // Mock size
            content: `[Content of ${fileName}]`, // Mock content
            summary: `Summary of ${fileName}`,
            insights: [`Insight 1 about ${fileName}`, `Insight 2 about ${fileName}`],
            metadata: {
              lastModified: new Date().toISOString(),
              created: new Date().toISOString()
            }
          };

          await addFileToWorkspace(mockFile);

          // Add to recent files if in Electron
          if (window.electronAPI) {
            window.electronAPI.addRecentFile(filePath);
          }
        }
      }
    } catch (error) {
      console.error('File upload error:', error);
    }
  }, [addFileToWorkspace]);

  const handleFileClick = useCallback((file) => {
    setPreviewFile(file);
    setShowFilePreview(true);
  }, []);

  const handleFileDelete = useCallback(async (file, e) => {
    e.stopPropagation();
    try {
      const confirmed = window.confirm(`Delete ${file.fileName}?`);
      if (confirmed) {
        const updatedFiles = currentFiles.filter(f => f.fileId !== file.fileId);
        setCurrentFiles(updatedFiles);

        // Update in session store
        const currentSession = useDesktopSessionStore.getState().currentSession;
        if (currentSession) {
          await useDesktopSessionStore.getState().saveLocalSession(
            currentSession.id,
            {
              ...currentSession,
              files: updatedFiles
            }
          );
        }
      }
    } catch (error) {
      console.error('Failed to delete file:', error);
    }
  }, [currentFiles, setCurrentFiles]);

  const handleContextMenu = useCallback((e, file) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      file: file
    });
  }, []);

  const closeContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  useEffect(() => {
    window.addEventListener('click', closeContextMenu);
    return () => {
      window.removeEventListener('click', closeContextMenu);
    };
  }, [closeContextMenu]);

  const getFileType = (extension) => {
    const codeExtensions = ['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rust', 'php', 'rb'];
    const textExtensions = ['txt', 'md', 'json', 'csv', 'xml', 'html', 'css'];
    const pdfExtensions = ['pdf'];
    const docExtensions = ['docx', 'doc'];

    if (codeExtensions.includes(extension)) return 'code';
    if (textExtensions.includes(extension)) return 'text';
    if (pdfExtensions.includes(extension)) return 'pdf';
    if (docExtensions.includes(extension)) return 'document';
    return 'other';
  };

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'code': return <Code className="w-8 h-8 text-blue-400" />;
      case 'text': return <FileText className="w-8 h-8 text-green-400" />;
      case 'pdf': return <Pdf className="w-8 h-8 text-red-400" />;
      case 'document': return <FileText className="w-8 h-8 text-indigo-400" />;
      default: return <FileText className="w-8 h-8 text-gray-400" />;
    }
  };

  if (!currentSession) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <div className="text-center">
          <FolderOpen className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-200 mb-2">No Workspace Selected</h3>
          <p className="text-gray-400 mb-4">Create or select a workspace to get started</p>
          <button
            onClick={() => createLocalSession('My Workspace')}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white font-medium transition-colors"
          >
            Create Workspace
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Workspace Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-white">{currentSession.name}</h2>
          <span className="text-sm text-gray-400">
            {filteredFiles.length} files • {currentSession.history.length} messages
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-gray-800 text-white px-3 py-1 rounded-lg text-sm w-48 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <Search className="absolute right-2 top-1.5 w-4 h-4 text-gray-400" />
          </div>

          <button
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            className="p-2 text-gray-400 hover:text-white transition-colors"
            title={viewMode === 'grid' ? 'List View' : 'Grid View'}
          >
            {viewMode === 'grid' ? <List className="w-5 h-5" /> : <LayoutGrid className="w-5 h-5" />}
          </button>

          <button
            onClick={handleFileUpload}
            className="flex items-center gap-2 px-3 py-1 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Files
          </button>
        </div>
      </div>

      {/* Workspace Content */}
      <div
        className={`flex-1 overflow-auto p-4 ${isDragging ? 'bg-gray-800/50' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {filteredFiles.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400">
            <div className="w-32 h-32 border-2 border-dashed border-gray-600 rounded-lg flex items-center justify-center mb-4">
              <FolderOpen className="w-12 h-12" />
            </div>
            <p className="mb-2">No files in this workspace</p>
            <p className="text-sm mb-4">Drag files here or click "Add Files"</p>
            {isDragging && (
              <div className="absolute inset-0 bg-indigo-600/20 rounded-lg border-2 border-indigo-500 border-dashed flex items-center justify-center">
                <p className="text-indigo-200 font-medium">Drop files to add to workspace</p>
              </div>
            )}
          </div>
        ) : (
          <div className={`${viewMode === 'grid' ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4' : 'space-y-2'}`}>
            {filteredFiles.map((file) => (
              <div
                key={file.fileId}
                className={`bg-gray-800 rounded-lg p-3 hover:bg-gray-700 transition-colors cursor-pointer relative ${viewMode === 'list' ? 'flex items-center gap-3' : ''}`}
                onClick={() => handleFileClick(file)}
                onContextMenu={(e) => handleContextMenu(e, file)}
              >
                <div className={viewMode === 'list' ? 'flex-shrink-0' : 'mb-2'}>
                  {getFileIcon(file.fileType)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="text-white font-medium truncate" title={file.fileName}>
                      {file.fileName}
                    </span>
                    <span className="text-xs text-gray-400 flex-shrink-0">
                      {file.metadata?.lastModified ? new Date(file.metadata.lastModified).toLocaleDateString() : ''}
                    </span>
                  </div>
                  {viewMode !== 'list' && (
                    <div className="text-xs text-gray-400 truncate" title={file.summary}>
                      {file.summary}
                    </div>
                  )}
                </div>
                {viewMode !== 'list' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleFileDelete(file, e);
                    }}
                    className="absolute top-2 right-2 p-1 text-gray-400 hover:text-red-400 transition-colors"
                    title="Delete file"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Context Menu */}
        {contextMenu && (
          <div
            className="absolute bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50"
            style={{
              top: `${contextMenu.y}px`,
              left: `${contextMenu.x}px`
            }}
          >
            <div className="p-2">
              <div className="text-white font-medium text-sm mb-1">{contextMenu.file.fileName}</div>
              <button
                onClick={() => handleFileClick(contextMenu.file)}
                className="w-full text-left px-3 py-1 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
              >
                Open
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleFileDelete(contextMenu.file, e);
                }}
                className="w-full text-left px-3 py-1 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        )}
      </div>

      {/* File Preview Modal */}
      {showFilePreview && previewFile && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold text-white">{previewFile.fileName}</h3>
              <button
                onClick={() => setShowFilePreview(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className="prose prose-invert max-w-none">
                <pre className="bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto">
                  {previewFile.content}
                </pre>

                {previewFile.summary && (
                  <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                    <h4 className="font-medium text-white mb-2">Analysis Summary:</h4>
                    <p className="text-gray-300">{previewFile.summary}</p>
                  </div>
                )}

                {previewFile.insights && previewFile.insights.length > 0 && (
                  <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                    <h4 className="font-medium text-white mb-2">Key Insights:</h4>
                    <ul className="list-disc list-inside text-gray-300 space-y-1">
                      {previewFile.insights.map((insight, index) => (
                        <li key={index}>{insight}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
            <div className="p-4 border-t border-gray-700 flex justify-end gap-2">
              <button
                onClick={() => setShowFilePreview(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  // Analyze file action
                  console.log('Analyze file:', previewFile);
                  setShowFilePreview(false);
                }}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white transition-colors"
              >
                Analyze Further
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedWorkspace;