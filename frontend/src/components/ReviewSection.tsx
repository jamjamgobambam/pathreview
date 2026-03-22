import React, { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { FeedbackSection } from '../types'

interface ReviewSectionProps {
  section: FeedbackSection
}

export const ReviewSection: React.FC<ReviewSectionProps> = ({ section }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const isLowConfidence = section.confidence < 0.3

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      setIsExpanded(!isExpanded)
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg">
      <button
        role="button"
        aria-expanded={isExpanded}
        aria-controls={`section-${section.section_name}`}
        onClick={() => setIsExpanded(!isExpanded)}
        onKeyPress={handleKeyPress}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3 text-left">
          <ChevronDown
            className={`w-5 h-5 text-gray-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          />
          <h3 className="text-lg font-semibold text-gray-900">{section.section_name}</h3>
          <div className="flex items-center gap-2">
            <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
              {(section.confidence * 100).toFixed(0)}%
            </span>
            {isLowConfidence && (
              <span className="inline-block px-2 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded">
                Low confidence
              </span>
            )}
          </div>
        </div>
      </button>

      {isExpanded && (
        <div id={`section-${section.section_name}`} className="p-4 border-t border-gray-200 bg-white">
          <p className="text-gray-700 whitespace-pre-wrap mb-4">{section.content}</p>

          {section.suggestions && section.suggestions.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold text-gray-900 mb-2">Suggestions:</h4>
              <ul className="space-y-2">
                {section.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex gap-3 text-gray-700">
                    <span className="text-blue-600 font-semibold flex-shrink-0">•</span>
                    <div>
                      <p className="font-medium">{suggestion.title}</p>
                      <p className="text-sm text-gray-600">{suggestion.description}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
