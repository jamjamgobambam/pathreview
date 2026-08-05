// frontend/src/utils/diffFormatter.ts

export interface ScoreDiff {
  before: number | undefined;
  after: number | undefined;
  delta: number | null;
  formattedDelta: string;
  trend: 'up' | 'down' | 'flat' | 'unknown';
}

export interface TextDiff {
  before: string | undefined;
  after: string | undefined;
  isChanged: boolean;
}

/**
 * Calculates the difference between two numerical scores.
 * Gracefully handles undefined or null values.
 */
export const calculateScoreDiff = (before?: number, after?: number): ScoreDiff => {
  // Handle edge cases where data might be missing from older reviews
  if (before === undefined || after === undefined || before === null || after === null) {
    return { 
      before, 
      after, 
      delta: null, 
      formattedDelta: '—', 
      trend: 'unknown' 
    };
  }

  const delta = after - before;
  
  let formattedDelta = `${delta}`;
  if (delta > 0) formattedDelta = `+${delta}`;
  if (delta === 0) formattedDelta = '0';

  const trend = delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat';

  return { before, after, delta, formattedDelta, trend };
};

/**
 * Compares two text fields to determine if feedback has changed.
 */
export const calculateTextDiff = (beforeText?: string, afterText?: string): TextDiff => {
  const safeBefore = beforeText || '';
  const safeAfter = afterText || '';

  return {
    before: beforeText,
    after: afterText,
    isChanged: safeBefore.trim() !== safeAfter.trim()
  };
};