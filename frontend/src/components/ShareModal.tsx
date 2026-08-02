import React, { useState } from 'react'
import { X, Copy, Check, Loader } from 'lucide-react'
import { copyToClipboard } from '../services/shareService'

interface ShareModalProps {
  isOpen: boolean
  onClose: () => void
  shareUrl: string | null
  isLoading: boolean
  error: string
}

export const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  shareUrl,
  isLoading,
  error
}) => {
  const [copied, setCopied] = useState(false)
  const [copyError, setCopyError] = useState('')

  if (!isOpen) return null

  const handleCopy = async () => {
    if (!shareUrl) return
    setCopyError('')
    try {
      await copyToClipboard(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopyError('Could not copy automatically. Please select the link and copy it manually.')
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="w-full max-w-md bg-white rounded-lg shadow-xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Share this review</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {isLoading && (
          <div className="py-8 text-center">
            <Loader className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-3" />
            <p className="text-gray-600 text-sm">Generating share link...</p>
          </div>
        )}

        {!isLoading && error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {!isLoading && !error && shareUrl && (
          <>
            <p className="text-sm text-gray-600 mb-3">
              Anyone with this link can view a read-only copy of this review. The link expires in
              30 days.
            </p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={shareUrl}
                aria-label="Share link"
                onFocus={(e) => e.target.select()}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors whitespace-nowrap"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            {copyError && <p className="mt-2 text-sm text-red-600">{copyError}</p>}
          </>
        )}
      </div>
    </div>
  )
}
