import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileSpreadsheet, CheckCircle } from 'lucide-react'
import { importApi } from '../services/api'

interface Preview {
  detected_columns: string[]
  sample_rows: Record<string, string>[]
  detected_encoding: string
  total_rows: number
  suggested_mappings: { source_column: string; target_field: string }[]
}

export default function ImportPage() {
  const [preview, setPreview] = useState<Preview | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setUploading(true)
    setError(null)
    try {
      const response = await importApi.preview(file)
      setPreview(response.data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      setError(message)
    } finally {
      setUploading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
  })

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Import Portfolio</h1>

      {/* Upload zone */}
      {!preview && (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400'
          }`}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <div className="text-gray-500">Processing file...</div>
          ) : (
            <>
              <Upload size={48} className="mx-auto text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-700">
                Drag & drop Excel or CSV file here
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Supports .xlsx, .xls, .csv (max 100MB)
              </p>
            </>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg">{error}</div>
      )}

      {/* Preview */}
      {preview && (
        <div className="space-y-6">
          <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
            <CheckCircle className="text-green-600" size={24} />
            <div>
              <p className="font-medium text-green-800">File parsed successfully</p>
              <p className="text-sm text-green-600">
                {preview.total_rows.toLocaleString()} rows detected |{' '}
                {preview.detected_columns.length} columns | Encoding: {preview.detected_encoding}
              </p>
            </div>
          </div>

          {/* Detected columns */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Detected Columns</h2>
            <div className="flex flex-wrap gap-2">
              {preview.detected_columns.map((col) => (
                <span
                  key={col}
                  className="px-3 py-1 bg-gray-100 rounded-full text-sm font-mono"
                >
                  {col}
                </span>
              ))}
            </div>
          </div>

          {/* Suggested mappings */}
          {preview.suggested_mappings.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold mb-4">
                <FileSpreadsheet className="inline mr-2" size={20} />
                Suggested Column Mappings
              </h2>
              <div className="grid grid-cols-2 gap-2">
                {preview.suggested_mappings.map((m) => (
                  <div
                    key={m.source_column}
                    className="flex items-center gap-2 p-2 bg-blue-50 rounded text-sm"
                  >
                    <span className="font-mono">{m.source_column}</span>
                    <span className="text-gray-400">&rarr;</span>
                    <span className="font-medium text-primary-700">{m.target_field}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sample data */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <h2 className="text-lg font-semibold p-6 pb-0">Preview (first 20 rows)</h2>
            <div className="overflow-x-auto p-6 pt-4">
              <table className="text-xs">
                <thead>
                  <tr>
                    {preview.detected_columns.map((col) => (
                      <th key={col} className="px-3 py-2 text-left font-medium text-gray-500 whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.sample_rows.map((row, i) => (
                    <tr key={i} className="border-t">
                      {preview.detected_columns.map((col) => (
                        <td key={col} className="px-3 py-2 whitespace-nowrap max-w-[200px] truncate">
                          {String(row[col] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => setPreview(null)}
              className="px-6 py-2 border rounded-lg text-sm hover:bg-gray-50"
            >
              Upload Different File
            </button>
            <button className="px-6 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
              Start Import
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
