'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { UploadCloud, File as FileIcon, Loader2, XCircle, FileText, Image as ImageIcon } from 'lucide-react';
import { verificationService } from '@/services/api';

export default function UploadForm() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle Drag Events
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  // Handle File Input
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    // Accept PDF and Images
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(selectedFile.type)) {
      setError('Invalid file type. Please upload a PDF, PNG, or JPG file.');
      return;
    }
    
    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (selectedFile.size > maxSize) {
      setError('File size exceeds 10MB. Please upload a smaller file.');
      return;
    }
    
    setFile(selectedFile);
    setError(null);
  };

  // Handle Submission
  const handleVerification = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const data = await verificationService.uploadCertificate(file);
      
      // Store the result in sessionStorage to access on the next page
      sessionStorage.setItem('verificationResult', JSON.stringify(data));
      
      // Redirect to results page
      router.push('/verify-result');
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please ensure the backend server is running.');
      setIsUploading(false);
    }
  };

  // Get file icon based on type
  const getFileIcon = () => {
    if (!file) return <UploadCloud className="w-10 h-10 text-gray-400" />;
    
    if (file.type === 'application/pdf') {
      return <FileText className="w-10 h-10 text-red-600" />;
    }
    return <ImageIcon className="w-10 h-10 text-blue-600" />;
  };

  return (
    <div className="w-full max-w-md mx-auto bg-white rounded-xl shadow-lg border border-gray-100 p-6">
      
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${file ? 'bg-gray-50' : ''}
        `}
      >
        <input
          type="file"
          id="certificate-upload"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          onChange={handleFileChange}
          accept=".pdf,.png,.jpg,.jpeg"
          disabled={isUploading}
        />

        <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
          {file ? (
            <>
              {getFileIcon()}
              <div className="text-sm text-gray-700 font-medium truncate max-w-[200px]">
                {file.name}
              </div>
              <p className="text-xs text-gray-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <p className="text-xs text-blue-600 mt-2">
                {file.type === 'application/pdf' ? '📄 PDF' : '🖼️ Image'} • Click to change
              </p>
            </>
          ) : (
            <>
              <UploadCloud className="w-10 h-10 text-gray-400" />
              <div className="text-gray-600">
                <span className="font-semibold text-blue-600">Click to upload</span> or drag and drop
              </div>
              <p className="text-xs text-gray-500">
                📄 PDF or 🖼️ Image (PNG, JPG)
              </p>
              <p className="text-xs text-gray-400">Max file size: 10MB</p>
            </>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-600 text-sm rounded-md flex items-start gap-2">
          <XCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Error</p>
            <p className="text-xs mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={handleVerification}
        disabled={!file || isUploading}
        className={`
          w-full mt-6 flex items-center justify-center py-2.5 px-4 rounded-lg font-medium text-white transition-all
          ${!file || isUploading ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'}
        `}
      >
        {isUploading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Verifying Certificate...
          </>
        ) : (
          'Verify Certificate'
        )}
      </button>

      {/* Processing Info */}
      {isUploading && (
        <p className="text-center text-xs text-gray-500 mt-3">
          This may take 10-30 seconds. Please wait...
        </p>
      )}

      {/* Supported Formats Info */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-xs text-blue-800 font-medium mb-1">✓ Supported Formats:</p>
        <div className="text-xs text-blue-700 space-y-0.5">
          <p>• PDF certificates (converted automatically)</p>
          <p>• PNG, JPG, JPEG images</p>
          <p>• Maximum file size: 10MB</p>
        </div>
      </div>
    </div>
  );
}