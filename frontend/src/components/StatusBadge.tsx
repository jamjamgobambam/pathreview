import React from 'react'
import { Loader } from 'lucide-react'

interface StatusBadgeProps {
  status: 'pending' | 'processing' | 'complete' | 'failed'
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const statusConfig = {
    pending: {
      bgColor: 'bg-gray-100',
      textColor: 'text-gray-800',
      label: 'Pending'
    },
    processing: {
      bgColor: 'bg-yellow-100',
      textColor: 'text-yellow-800',
      label: 'Processing'
    },
    complete: {
      bgColor: 'bg-green-100',
      textColor: 'text-green-800',
      label: 'Complete'
    },
    failed: {
      bgColor: 'bg-red-100',
      textColor: 'text-red-800',
      label: 'Failed'
    }
  }

  const config = statusConfig[status]

  return (
    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.textColor}`}>
      {status === 'processing' && <Loader className="w-4 h-4 animate-spin" />}
      {config.label}
    </span>
  )
}
