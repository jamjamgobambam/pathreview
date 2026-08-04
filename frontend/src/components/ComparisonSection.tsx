import React from 'react'
import type { SectionDiff, LineDiff } from '../utils/diffFormatter'

interface ComparisonSectionProps {
  diff: SectionDiff
}

const lineStyles: Record<LineDiff['type'], string> = {
  added: 'bg-green-50 text-green-800',
  removed: 'bg-red-50 text-red-800',
  unchanged: 'text-gray-700'
}

const linePrefix: Record<LineDiff['type'], string> = {
  added: '+',
  removed: '-',
  unchanged: ' '
}

const DiffLines: React.FC<{ lines: LineDiff[] }> = ({ lines }) => (
  <div className="font-mono text-sm rounded border border-gray-200 overflow-hidden">
    {lines.map((line, index) => (
      <div key={index} className={`px-3 py-1 whitespace-pre-wrap ${lineStyles[line.type]}`}>
        <span className="select-none text-gray-400 mr-2">{linePrefix[line.type]}</span>
        {line.text}
      </div>
    ))}
  </div>
)

export const ComparisonSection: React.FC<ComparisonSectionProps> = ({ diff }) => {
  const confidencePct = (value?: number) => (value !== undefined ? `${(value * 100).toFixed(0)}%` : '—')

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{diff.section_name}</h3>
        <div className="flex items-center gap-2 text-sm">
          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-medium">
            {confidencePct(diff.confidenceA)} → {confidencePct(diff.confidenceB)}
          </span>
          {diff.confidenceDelta !== undefined && diff.confidenceDelta !== 0 && (
            <span
              className={`px-2 py-1 rounded font-medium ${
                diff.confidenceDelta > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}
            >
              {diff.confidenceDelta > 0 ? '+' : ''}
              {(diff.confidenceDelta * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      {!diff.presentInA && (
        <p className="text-sm text-green-700 mb-2">New section in this review.</p>
      )}
      {!diff.presentInB && (
        <p className="text-sm text-red-700 mb-2">Section removed in the newer review.</p>
      )}

      <div className="mb-3">
        <DiffLines lines={diff.contentDiff} />
      </div>

      {diff.suggestionsDiff.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-900 mb-2 text-sm">Suggestions</h4>
          <DiffLines lines={diff.suggestionsDiff} />
        </div>
      )}
    </div>
  )
}
