import type { Review, FeedbackSection } from '../types'

export type LineDiffType = 'added' | 'removed' | 'unchanged'

export interface LineDiff {
  type: LineDiffType
  text: string
}

export interface SectionDiff {
  section_name: string
  presentInA: boolean
  presentInB: boolean
  confidenceA?: number
  confidenceB?: number
  confidenceDelta?: number
  contentDiff: LineDiff[]
  suggestionsDiff: LineDiff[]
  isIdentical: boolean
}

export interface ReviewComparison {
  older: Review
  newer: Review
  overallScoreDelta?: number
  sections: SectionDiff[]
  hasAnyDiff: boolean
}

function diffArrays(oldItems: string[], newItems: string[]): LineDiff[] {
  let start = 0
  while (
    start < oldItems.length &&
    start < newItems.length &&
    oldItems[start] === newItems[start]
  ) {
    start++
  }

  let endOld = oldItems.length - 1
  let endNew = newItems.length - 1
  while (endOld >= start && endNew >= start && oldItems[endOld] === newItems[endNew]) {
    endOld--
    endNew--
  }

  const result: LineDiff[] = []
  for (let i = 0; i < start; i++) {
    result.push({ type: 'unchanged', text: oldItems[i] })
  }
  for (let i = start; i <= endOld; i++) {
    result.push({ type: 'removed', text: oldItems[i] })
  }
  for (let i = start; i <= endNew; i++) {
    result.push({ type: 'added', text: newItems[i] })
  }
  for (let i = endOld + 1; i < oldItems.length; i++) {
    result.push({ type: 'unchanged', text: oldItems[i] })
  }

  return result
}

export function diffLines(oldText: string, newText: string): LineDiff[] {
  return diffArrays(oldText.split('\n'), newText.split('\n'))
}

export function diffSections(
  a: FeedbackSection[] | undefined,
  b: FeedbackSection[] | undefined
): SectionDiff[] {
  const sectionsA = a ?? []
  const sectionsB = b ?? []
  const mapA = new Map(sectionsA.map((s) => [s.section_name, s]))
  const mapB = new Map(sectionsB.map((s) => [s.section_name, s]))

  const orderedNames: string[] = []
  for (const s of sectionsA) orderedNames.push(s.section_name)
  for (const s of sectionsB) {
    if (!mapA.has(s.section_name)) orderedNames.push(s.section_name)
  }

  return orderedNames.map((name) => {
    const sectionA = mapA.get(name)
    const sectionB = mapB.get(name)
    const presentInA = !!sectionA
    const presentInB = !!sectionB

    let contentDiff: LineDiff[]
    let suggestionsDiff: LineDiff[]

    if (sectionA && sectionB) {
      contentDiff = diffLines(sectionA.content, sectionB.content)
      suggestionsDiff = diffArrays(sectionA.suggestions, sectionB.suggestions)
    } else if (sectionA) {
      contentDiff = sectionA.content.split('\n').map((text) => ({ type: 'removed' as const, text }))
      suggestionsDiff = sectionA.suggestions.map((text) => ({ type: 'removed' as const, text }))
    } else {
      contentDiff = sectionB!.content.split('\n').map((text) => ({ type: 'added' as const, text }))
      suggestionsDiff = sectionB!.suggestions.map((text) => ({ type: 'added' as const, text }))
    }

    const confidenceA = sectionA?.confidence
    const confidenceB = sectionB?.confidence
    const confidenceDelta =
      presentInA && presentInB ? (confidenceB as number) - (confidenceA as number) : undefined

    const isIdentical =
      presentInA &&
      presentInB &&
      confidenceDelta === 0 &&
      contentDiff.every((d) => d.type === 'unchanged') &&
      suggestionsDiff.every((d) => d.type === 'unchanged')

    return {
      section_name: name,
      presentInA,
      presentInB,
      confidenceA,
      confidenceB,
      confidenceDelta,
      contentDiff,
      suggestionsDiff,
      isIdentical
    }
  })
}

export function compareReviews(older: Review, newer: Review): ReviewComparison {
  const overallScoreDelta =
    older.overall_score !== undefined && newer.overall_score !== undefined
      ? newer.overall_score - older.overall_score
      : undefined

  const sections = diffSections(older.sections, newer.sections)

  const hasAnyDiff =
    (overallScoreDelta !== undefined && overallScoreDelta !== 0) ||
    sections.some((s) => !s.isIdentical)

  return { older, newer, overallScoreDelta, sections, hasAnyDiff }
}
