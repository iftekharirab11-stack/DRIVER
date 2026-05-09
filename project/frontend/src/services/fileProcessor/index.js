/**
 * File Processor Service - Main Entry Point
 * Handles file upload, processing, and intelligence extraction
 */

import { PDFProcessor } from './pdfProcessor';
import { DOCProcessor } from './docProcessor';
import { CSVProcessor } from './csvProcessor';
import { ExcelProcessor } from './excelProcessor';
import { TextProcessor } from './textProcessor';

export class FileProcessor {
  static async processFile(file, options = {}) {
    const fileType = this.detectFileType(file);

    try {
      let processor;

      switch (fileType) {
        case 'pdf':
          processor = new PDFProcessor();
          break;
        case 'docx':
        case 'doc':
          processor = new DOCProcessor();
          break;
        case 'csv':
          processor = new CSVProcessor();
          break;
        case 'xlsx':
        case 'xls':
          processor = new ExcelProcessor();
          break;
        case 'txt':
        case 'md':
        case 'markdown':
          processor = new TextProcessor();
          break;
        default:
          throw new Error(`Unsupported file type: ${fileType}`);
      }

      return await processor.process(file, options);
    } catch (error) {
      console.error(`File processing failed for ${file.name}:`, error);
      throw new Error(`Failed to process ${fileType} file: ${error.message}`);
    }
  }

  static detectFileType(file) {
    if (!file || !file.name) {
      throw new Error('Invalid file object');
    }

    const extension = file.name.split('.').pop().toLowerCase();
    return extension;
  }

  static validateFile(file, maxSize = 10 * 1024 * 1024) {
    if (!file) {
      throw new Error('No file provided');
    }

    if (file.size > maxSize) {
      throw new Error(`File too large. Maximum size: ${maxSize / 1024 / 1024}MB`);
    }

    const allowedTypes = ['pdf', 'docx', 'doc', 'csv', 'xlsx', 'xls', 'txt', 'md', 'markdown'];
    const fileType = this.detectFileType(file);

    if (!allowedTypes.includes(fileType)) {
      throw new Error(`Unsupported file type: ${fileType}. Allowed: ${allowedTypes.join(', ')}`);
    }

    return true;
  }

  static getFileIcon(fileType) {
    const icons = {
      pdf: '📄',
      docx: '📝',
      doc: '📝',
      csv: '📊',
      xlsx: '📊',
      xls: '📊',
      txt: '📋',
      md: '📋',
      markdown: '📋'
    };

    return icons[fileType] || '📁';
  }
}