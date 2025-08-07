'use client'

import { useState } from 'react'

interface UploadStatus {
  uploading: boolean
  progress: number
  jobId?: string
  analysisId?: string
  error?: string
}

export default function VideoUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<UploadStatus>({ uploading: false, progress: 0 })
  const [jobStatus, setJobStatus] = useState<any>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      // Validate file type
      const allowedTypes = ['video/mp4', 'video/avi', 'video/mov']
      if (!allowedTypes.includes(selectedFile.type)) {
        alert('Please select a valid video file (MP4, AVI, or MOV)')
        return
      }
      
      // Validate file size (100MB limit)
      const maxSize = 100 * 1024 * 1024 // 100MB
      if (selectedFile.size > maxSize) {
        alert('File size must be less than 100MB')
        return
      }
      
      setFile(selectedFile)
    }
  }

  const uploadVideo = async () => {
    if (!file) return

    setStatus({ uploading: true, progress: 0 })

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('confidence_threshold', '0.25')
      formData.append('visualize', 'true')

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      
      setStatus({
        uploading: false,
        progress: 100,
        jobId: result.job_id,
        analysisId: result.analysis_id
      })

      // Start polling job status if job_id is available
      if (result.job_id) {
        pollJobStatus(result.job_id)
      }

    } catch (error) {
      setStatus({
        uploading: false,
        progress: 0,
        error: error instanceof Error ? error.message : 'Upload failed'
      })
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    const poll = async () => {
      try {
        const response = await fetch(`${apiUrl}/jobs/${jobId}`)
        if (response.ok) {
          const jobData = await response.json()
          setJobStatus(jobData)
          
          // Continue polling if job is still running
          if (jobData.status === 'started' || jobData.status === 'queued') {
            setTimeout(poll, 2000) // Poll every 2 seconds
          }
        }
      } catch (error) {
        console.error('Error polling job status:', error)
      }
    }
    
    poll()
  }

  const resetUpload = () => {
    setFile(null)
    setStatus({ uploading: false, progress: 0 })
    setJobStatus(null)
  }

  return (
    <div className="card max-w-2xl">
      <h3 className="text-xl font-bold text-white mb-4">Video Upload</h3>
      
      {!file && (
        <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
          <input
            type="file"
            accept="video/mp4,video/avi,video/mov"
            onChange={handleFileSelect}
            className="hidden"
            id="video-upload"
          />
          <label htmlFor="video-upload" className="cursor-pointer">
            <div className="text-basketball-orange text-4xl mb-4">📹</div>
            <p className="text-gray-300 mb-2">Click to select a video file</p>
            <p className="text-sm text-gray-500">MP4, AVI, or MOV (max 100MB)</p>
          </label>
        </div>
      )}

      {file && !status.uploading && !status.jobId && (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
            <div>
              <p className="text-white font-medium">{file.name}</p>
              <p className="text-gray-400 text-sm">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
            </div>
            <button onClick={resetUpload} className="text-red-500 hover:text-red-400">
              ✕
            </button>
          </div>
          
          <div className="flex gap-3">
            <button onClick={uploadVideo} className="btn-primary flex-1">
              Upload & Analyze Video
            </button>
            <button onClick={resetUpload} className="btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      )}

      {status.uploading && (
        <div className="space-y-4">
          <div className="text-white font-medium">Uploading video...</div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-basketball-orange h-2 rounded-full transition-all duration-300"
              style={{ width: `${status.progress}%` }}
            />
          </div>
        </div>
      )}

      {status.error && (
        <div className="bg-red-900 border border-red-600 rounded p-4">
          <p className="text-red-200">Error: {status.error}</p>
          <button onClick={resetUpload} className="mt-2 btn-secondary">
            Try Again
          </button>
        </div>
      )}

      {status.jobId && (
        <div className="space-y-4">
          <div className="bg-green-900 border border-green-600 rounded p-4">
            <p className="text-green-200 font-medium">✅ Video uploaded successfully!</p>
            <p className="text-green-300 text-sm">Analysis ID: {status.analysisId}</p>
            {status.jobId && <p className="text-green-300 text-sm">Job ID: {status.jobId}</p>}
          </div>

          {jobStatus && (
            <div className="bg-blue-900 border border-blue-600 rounded p-4">
              <p className="text-blue-200 font-medium">Processing Status: {jobStatus.status}</p>
              {jobStatus.progress > 0 && (
                <div className="mt-2">
                  <div className="w-full bg-blue-800 rounded-full h-2">
                    <div 
                      className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${jobStatus.progress * 100}%` }}
                    />
                  </div>
                  <p className="text-blue-300 text-sm mt-1">{Math.round(jobStatus.progress * 100)}% complete</p>
                </div>
              )}
              
              {jobStatus.status === 'finished' && (
                <div className="mt-2">
                  <p className="text-green-300">✅ Analysis completed!</p>
                  {jobStatus.result && (
                    <div className="mt-2 text-sm text-gray-300">
                      <p>Enhanced stats calculated</p>
                      {/* Add more result details here */}
                    </div>
                  )}
                </div>
              )}
              
              {jobStatus.status === 'failed' && (
                <p className="text-red-300 mt-2">❌ Analysis failed: {jobStatus.exc_info}</p>
              )}
            </div>
          )}

          <button onClick={resetUpload} className="btn-secondary w-full">
            Upload Another Video
          </button>
        </div>
      )}
    </div>
  )
}