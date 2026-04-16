"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Header } from "@/components/Header";
import { uploadDocument, listDocuments, deleteDocument } from "@/lib/api";
import { Document } from "@/lib/types";

export default function KnowledgeBasePage() {
  const { auth, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Check admin access
  useEffect(() => {
    if (authLoading) return; // Wait for auth to load
    if (!auth) {
      router.push("/login");
    } else if (auth.user.role !== "admin") {
      router.push("/");
    } else {
      loadDocuments();
    }
  }, [auth, authLoading, router]);

  const loadDocuments = async () => {
    if (!auth?.token) return;

    try {
      setIsLoadingDocs(true);
      const data = await listDocuments(auth.token);
      setDocuments(data.documents || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!auth?.token) return;

    // Validate file type
    const validTypes = ["application/pdf", "text/plain"];
    if (!validTypes.includes(file.type)) {
      setError("Only PDF and TXT files are supported");
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB");
      return;
    }

    try {
      setIsLoadingDocs(true);
      setError(null);
      setSuccess(null);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => (prev < 90 ? prev + 10 : prev));
      }, 100);

      const result = await uploadDocument(file, auth.token);

      clearInterval(progressInterval);
      setUploadProgress(100);

      setSuccess(`Document "${file.name}" uploaded successfully! Processing...`);
      
      // Reset progress after 2 seconds
      setTimeout(() => {
        setUploadProgress(0);
        setSuccess(null);
      }, 2000);

      // Reload documents
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!auth?.token) return;

    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

    try {
      setError(null);
      await deleteDocument(docId, auth.token);
      setSuccess(`"${filename}" deleted successfully`);
      setTimeout(() => setSuccess(null), 3000);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  if (authLoading || !auth || auth.user.role !== "admin") {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Knowledge Base Management</h1>
            <p className="text-gray-600 mt-2">
              Upload documents to train the AI booking assistant with hotel FAQs, policies, and room information.
            </p>
          </div>

          {/* Upload Section */}
          <div className="bg-white rounded-lg shadow mb-8 p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Document</h2>

            {/* Alerts */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            {success && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
                ✓ {success}
              </div>
            )}

            {/* Drag and Drop Area */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
                isDragging
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-300 bg-gray-50 hover:border-gray-400"
              }`}
            >
              <div className="mb-4">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20m-8-12l-4-4m0 0l-4 4m4-4v16"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>

              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".pdf,.txt"
                onChange={(e) => e.target.files && handleFileUpload(e.target.files[0])}
                disabled={isLoadingDocs}
              />

              <label htmlFor="file-upload" className="cursor-pointer">
                <p className="text-lg font-semibold text-gray-900">
                  {isDragging ? "Drop your file here" : "Drag and drop your file here"}
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  or{" "}
                  <span className="text-blue-600 font-semibold hover:underline">
                    browse to select
                  </span>
                </p>
              </label>

              <p className="text-xs text-gray-500 mt-4">
                Supported: PDF, TXT (max 10MB)
              </p>
            </div>

            {/* Upload Progress */}
            {uploadProgress > 0 && uploadProgress < 100 && (
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Documents List */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-8 py-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Uploaded Documents ({documents.length})
              </h2>
            </div>

            {isLoadingDocs && documents.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <div className="inline-block h-8 w-8 border-4 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
                <p className="mt-4">Loading documents...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <p className="text-lg font-medium">No documents uploaded yet</p>
                <p className="text-sm mt-2">Upload a document to get started</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-8 py-4 text-left text-sm font-semibold text-gray-900">
                        Filename
                      </th>
                      <th className="px-8 py-4 text-left text-sm font-semibold text-gray-900">
                        Type
                      </th>
                      <th className="px-8 py-4 text-left text-sm font-semibold text-gray-900">
                        Chunks
                      </th>
                      <th className="px-8 py-4 text-left text-sm font-semibold text-gray-900">
                        Status
                      </th>
                      <th className="px-8 py-4 text-left text-sm font-semibold text-gray-900">
                        Uploaded
                      </th>
                      <th className="px-8 py-4 text-center text-sm font-semibold text-gray-900">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc) => (
                      <tr
                        key={doc.id}
                        className="border-b border-gray-200 hover:bg-gray-50 transition"
                      >
                        <td className="px-8 py-4 text-sm text-gray-900 font-medium">
                          📄 {doc.filename}
                        </td>
                        <td className="px-8 py-4 text-sm text-gray-500">
                          {doc.sourceType.toUpperCase()}
                        </td>
                        <td className="px-8 py-4 text-sm text-gray-500">
                          {doc.chunks}
                        </td>
                        <td className="px-8 py-4 text-sm">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              doc.status === "stored"
                                ? "bg-green-100 text-green-800"
                                : doc.status === "processing"
                                ? "bg-yellow-100 text-yellow-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {doc.status === "stored"
                              ? "✓ Stored"
                              : doc.status === "processing"
                              ? "⏳ Processing"
                              : "✗ Error"}
                          </span>
                        </td>
                        <td className="px-8 py-4 text-sm text-gray-500">
                          {new Date(doc.uploadedAt).toLocaleDateString()}
                        </td>
                        <td className="px-8 py-4 text-center">
                          <button
                            onClick={() => handleDelete(doc.id, doc.filename)}
                            className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Info Box */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-2">💡 How It Works</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Upload PDFs or text files containing room descriptions, FAQ, or policies</li>
              <li>• Documents are automatically split into chunks and embedded</li>
              <li>• The AI uses these documents to answer user questions accurately</li>
              <li>• Changes take effect immediately after processing completes</li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}
