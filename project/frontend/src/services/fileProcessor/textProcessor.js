/**
 * Text File Processor
 * Handles plain text, markdown, and similar file formats
 */

export class TextProcessor {
  async process(file, options = {}) {
    try {
      const fileContent = await this.readTextFile(file);
      const summary = this.generateSummary(fileContent);
      const insights = this.extractInsights(fileContent);
      const metadata = this.analyzeTextMetadata(fileContent);

      return {
        fileId: this.generateFileId(file),
        fileName: file.name,
        fileType: this.detectTextType(file),
        fileSize: file.size,
        content: fileContent,
        summary: summary,
        insights: insights,
        metadata: {
          ...metadata,
          processedAt: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error('Text processing error:', error);
      throw new Error(`Text processing failed: ${error.message}`);
    }
  }

  async readTextFile(file) {
    return new Promise((resolve) => {
      setTimeout(() => {
        // Simulate file reading
        resolve(`Content of ${file.name}:\n\nThis is the text content that would be extracted from the file. In a real implementation, this would contain the actual file contents.`);
      }, 100);
    });
  }

  generateSummary(content) {
    const lines = content.split('\n').filter(line => line.trim().length > 0);
    const previewLines = lines.slice(0, 3).map(line => line.trim());

    return `Text Summary: ${previewLines.join(' ')}...`;
  }

  extractInsights(content) {
    const insights = [];

    if (content.includes('# ') || content.includes('## ') || content.includes('### ')) {
      insights.push('Markdown formatting detected');
    }

    if (content.includes('function ') || content.includes('def ') || content.includes('class ')) {
      insights.push('Code content detected');
    }

    if (content.split('\n').length > 100) {
      insights.push('Long document detected');
    }

    return insights.length > 0 ? insights : ['General text content'];
  }

  analyzeTextMetadata(content) {
    const lines = content.split('\n');
    const words = content.split(/\s+/).filter(word => word.length > 0);

    return {
      lineCount: lines.length,
      wordCount: words.length,
      charCount: content.length,
      hasMarkdown: content.includes('# ') || content.includes('## ') || content.includes('### ')
    };
  }

  generateFileId(file) {
    return `txt_${Date.now()}_${file.name.replace(/\s+/g, '_')}`;
  }

  detectTextType(file) {
    const extension = file.name.split('.').pop().toLowerCase();
    return extension === 'md' || extension === 'markdown' ? 'markdown' : 'text';
  }
}