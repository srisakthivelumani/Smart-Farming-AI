
import { useEffect, useState } from 'react'
import {
  uploadKnowledgeDocument,
  fetchKnowledgeDocuments,
} from '../services/api'

type DocumentItem = {
  filename?: string
  file_name?: string
  name?: string
}

function getDocuments(data: unknown): DocumentItem[] {
  if (Array.isArray(data)) return data as DocumentItem[]

  if (data && typeof data === 'object') {
    const result = data as {
      documents?: DocumentItem[]
      files?: DocumentItem[]
    }

    return result.documents ?? result.files ?? []
  }

  return []
}

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  async function loadDocuments() {
    try {
      const data = await fetchKnowledgeDocuments()
      setDocuments(getDocuments(data))
    } catch {
      setMessage('Could not load documents. Check that the backend is running.')
    }
  }

  useEffect(() => {
    void loadDocuments()
  }, [])

  async function handleUpload() {
    if (!file) {
      setMessage('Please select a PDF or TXT file.')
      return
    }

    setLoading(true)
    setMessage('')

    try {
      await uploadKnowledgeDocument(file)
      setMessage('Document uploaded successfully!')
      setFile(null)
      await loadDocuments()
    } catch (error: any) {
      console.error('Knowledge Base upload error:', error)

      setMessage(
        error.response?.data?.detail ||
        error.message ||
        'Upload failed. Please check the backend.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-2 text-3xl font-bold text-green-800">
          Knowledge Base
        </h1>

        <p className="mb-8 text-gray-600">
          Upload agricultural documents to help the AI provide
          information based on your knowledge base.
        </p>

        <div className="mb-8 rounded-xl bg-white p-6 shadow">
          <h2 className="mb-4 text-xl font-semibold">
            Upload Document
          </h2>

          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(event) =>
              setFile(event.target.files?.[0] ?? null)
            }
            className="mb-4 block w-full"
          />

          <button
            onClick={handleUpload}
            disabled={loading}
            className="rounded-lg bg-green-700 px-5 py-2 text-white disabled:opacity-50"
          >
            {loading ? 'Uploading...' : 'Upload Document'}
          </button>

          {message && (
            <p className="mt-4 text-sm text-gray-700">{message}</p>
          )}
        </div>

        <div className="rounded-xl bg-white p-6 shadow">
          <h2 className="mb-4 text-xl font-semibold">
            Stored Documents
          </h2>

          {documents.length === 0 ? (
            <p className="text-gray-500">No documents found.</p>
          ) : (
            <ul className="space-y-3">
              {documents.map((doc, index) => (
                <li
                  key={index}
                  className="rounded-lg border p-3"
                >
                  {doc.filename ?? doc.file_name ?? doc.name ?? 'Document'}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
