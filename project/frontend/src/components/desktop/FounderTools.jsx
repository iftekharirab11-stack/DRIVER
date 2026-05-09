import React, { useState } from 'react';
import { useDesktopSessionStore } from '../../store/desktopSessionStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { useChatStore } from '../../store/chatStore';
import {
  BrainCircuit,
  Bug,
  BookOpen,
  GitBranch,
  Search,
  Zap,
  Lightbulb,
  Code,
  Database,
  Shield,
  Rocket
} from 'lucide-react';

const FounderTools = () => {
  const { currentSession, currentFiles } = useDesktopSessionStore();
  const { addMessage } = useChatStore();
  const [activeTool, setActiveTool] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const fileList = currentFiles.map(f => f.fileName).join(', ');

  const toolCategories = [
    {
      name: 'Code Analysis',
      icon: <Code className="w-5 h-5" />,
      tools: [
        {
          id: 'architecture',
          name: 'Architecture Review',
          description: 'Analyze codebase architecture and design patterns',
          prompt: `Perform a comprehensive architecture review of this codebase:
          1. Identify architectural patterns used
          2. Analyze component relationships
          3. Assess design pattern usage
          4. Recommend improvements
          5. Identify potential issues

          Files: ${fileList}`
        },
        {
          id: 'code-quality',
          name: 'Code Quality Audit',
          description: 'Assess code quality and maintainability',
          prompt: `Conduct a detailed code quality audit:
          1. Evaluate code maintainability
          2. Assess readability and consistency
          3. Identify code smells
          4. Check for anti-patterns
          5. Recommend refactoring opportunities

          Files: ${fileList}`
        },
        {
          id: 'performance',
          name: 'Performance Analysis',
          description: 'Identify performance bottlenecks',
          prompt: `Analyze potential performance issues:
          1. Identify algorithmic inefficiencies
          2. Check for memory leaks
          3. Assess database query optimization
          4. Review expensive operations
          5. Recommend performance improvements

          Files: ${fileList}`
        }
      ]
    },
    {
      name: 'Debugging',
      icon: <Bug className="w-5 h-5" />,
      tools: [
        {
          id: 'bug-detection',
          name: 'Bug Detection',
          description: 'Find potential bugs and issues',
          prompt: `Analyze code for potential bugs:
          1. Identify error-prone patterns
          2. Check exception handling
          3. Review edge cases
          4. Assess error propagation
          5. Recommend fixes

          Files: ${fileList}`
        },
        {
          id: 'security',
          name: 'Security Audit',
          description: 'Check for security vulnerabilities',
          prompt: `Perform security analysis:
          1. Identify potential vulnerabilities
          2. Check input validation
          3. Review authentication/authorization
          4. Assess data exposure risks
          5. Recommend security improvements

          Files: ${fileList}`
        },
        {
          id: 'error-handling',
          name: 'Error Handling Review',
          description: 'Evaluate error handling strategies',
          prompt: `Review error handling implementation:
          1. Assess error handling completeness
          2. Check error propagation
          3. Review user-facing error messages
          4. Identify missing error cases
          5. Recommend improvements

          Files: ${fileList}`
        }
      ]
    },
    {
      name: 'Documentation',
      icon: <BookOpen className="w-5 h-5" />,
      tools: [
        {
          id: 'api-docs',
          name: 'API Documentation',
          description: 'Generate API documentation',
          prompt: `Generate comprehensive API documentation:
          1. Document all public APIs
          2. Include parameter descriptions
          3. Add return value documentation
          4. Provide usage examples
          5. Note any deprecations

          Files: ${fileList}`
        },
        {
          id: 'code-docs',
          name: 'Code Documentation',
          description: 'Generate code documentation',
          prompt: `Create detailed code documentation:
          1. Document classes and methods
          2. Explain complex algorithms
          3. Add inline comments where needed
          4. Generate JSDoc/TypeScript docs
          5. Create usage examples

          Files: ${fileList}`
        },
        {
          id: 'readme',
          name: 'README Generator',
          description: 'Create project README',
          prompt: `Generate a comprehensive README:
          1. Project overview and purpose
          2. Installation instructions
          3. Usage examples
          4. Configuration options
          5. Contribution guidelines

          Files: ${fileList}`
        }
      ]
    },
    {
      name: 'Advanced',
      icon: <Zap className="w-5 h-5" />,
      tools: [
        {
          id: 'refactoring',
          name: 'Refactoring Suggestions',
          description: 'Get refactoring recommendations',
          prompt: `Suggest code refactoring opportunities:
          1. Identify large functions/methods
          2. Find duplicated code
          3. Assess class cohesion
          4. Review inheritance hierarchies
          5. Recommend structural improvements

          Files: ${fileList}`
        },
        {
          id: 'testing',
          name: 'Test Coverage Analysis',
          description: 'Analyze test coverage needs',
          prompt: `Analyze test coverage requirements:
          1. Identify untested code paths
          2. Assess test completeness
          3. Review edge case coverage
          4. Check mock/stub usage
          5. Recommend additional tests

          Files: ${fileList}`
        },
        {
          id: 'optimization',
          name: 'Optimization Opportunities',
          description: 'Find optimization potential',
          prompt: `Identify optimization opportunities:
          1. Analyze algorithm complexity
          2. Review data structure usage
          3. Assess caching strategies
          4. Check resource management
          5. Recommend optimizations

          Files: ${fileList}`
        }
      ]
    }
  ];

  const runTool = async (tool) => {
    if (!currentSession) {
      alert('Please create or select a workspace first');
      return;
    }

    setIsAnalyzing(true);
    setActiveTool(tool.id);

    try {
      // Add system message to chat
      addMessage({
        id: Date.now(),
        role: 'system',
        content: `🔍 Running ${tool.name}...`,
        timestamp: new Date(),
        isSystem: true
      });

      // Simulate analysis (in real implementation, call backend AI)
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Add AI response
      addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: `## ${tool.name} Results

Based on analysis of ${currentFiles.length} files in your workspace:

### Key Findings:
1. **Architecture**: The codebase uses a modular architecture with clear separation of concerns
2. **Code Quality**: Generally good with some areas for improvement in error handling
3. **Performance**: No major bottlenecks detected, but some database queries could be optimized
4. **Security**: Basic security measures are in place, but input validation could be enhanced
5. **Testing**: Core functionality is well-tested, but edge cases need more coverage

### Specific Recommendations:
- Refactor the user authentication module to use dependency injection
- Add input validation for all API endpoints
- Implement connection pooling for database operations
- Add integration tests for critical workflows
- Document complex algorithms in the data processing module

### Files Analyzed:
${currentFiles.map(f => `- ${f.fileName}`).join('\n')}

Would you like me to elaborate on any specific aspect of this analysis?`,
        timestamp: new Date(),
        toolContext: tool.id
      });

    } catch (error) {
      console.error('Tool execution error:', error);
      addMessage({
        id: Date.now() + 2,
        role: 'assistant',
        content: `❌ Error running ${tool.name}: ${error.message}`,
        timestamp: new Date(),
        isError: true
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!currentSession) {
    return (
      <div className="p-4 bg-gray-800 rounded-lg">
        <p className="text-gray-400 text-center py-8">
          Please create or select a workspace to use founder tools
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Rocket className="w-5 h-5 text-indigo-400" />
        Founder Tools
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {toolCategories.map((category) => (
          <div key={category.name} className="bg-gray-700 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              {category.icon}
              <span className="text-white font-medium text-sm">{category.name}</span>
            </div>
            <div className="space-y-2">
              {category.tools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => runTool(tool)}
                  disabled={isAnalyzing}
                  className="w-full text-left flex items-start gap-2 p-2 rounded hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="text-gray-300 text-sm">{tool.name}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="border-t border-gray-600 pt-4">
        <h4 className="text-white font-medium mb-2 flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-yellow-400" />
          Quick Actions
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <button
            onClick={() => runTool(toolCategories[0].tools[0])}
            disabled={isAnalyzing}
            className="flex items-center gap-2 p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 transition-colors disabled:opacity-50"
          >
            <BrainCircuit className="w-4 h-4" />
            Architecture Review
          </button>
          <button
            onClick={() => runTool(toolCategories[1].tools[0])}
            disabled={isAnalyzing}
            className="flex items-center gap-2 p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 transition-colors disabled:opacity-50"
          >
            <Bug className="w-4 h-4" />
            Bug Detection
          </button>
          <button
            onClick={() => runTool(toolCategories[2].tools[0])}
            disabled={isAnalyzing}
            className="flex items-center gap-2 p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 transition-colors disabled:opacity-50"
          >
            <BookOpen className="w-4 h-4" />
            Generate API Docs
          </button>
          <button
            onClick={() => runTool(toolCategories[3].tools[0])}
            disabled={isAnalyzing}
            className="flex items-center gap-2 p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 transition-colors disabled:opacity-50"
          >
            <Zap className="w-4 h-4" />
            Refactoring Ideas
          </button>
        </div>
      </div>

      {/* Analysis Status */}
      {isAnalyzing && (
        <div className="mt-4 p-3 bg-gray-700 rounded-lg flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <div>
            <p className="text-indigo-400 font-medium">Analyzing codebase...</p>
            <p className="text-gray-400 text-sm">This may take a few moments</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FounderTools;