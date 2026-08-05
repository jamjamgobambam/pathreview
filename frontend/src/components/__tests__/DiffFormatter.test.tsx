import { describe, it, expect } from 'vitest';
import { calculateScoreDiff, calculateTextDiff } from '../../utils/diffFormatter';

describe('diffFormatter utility', () => {
  
  describe('calculateScoreDiff', () => {
    it('calculates a positive improvement correctly', () => {
      const result = calculateScoreDiff(70, 85);
      expect(result.delta).toBe(15);
      expect(result.formattedDelta).toBe('+15');
      expect(result.trend).toBe('up');
    });

    it('calculates a regression correctly', () => {
      const result = calculateScoreDiff(90, 85);
      expect(result.delta).toBe(-5);
      expect(result.formattedDelta).toBe('-5');
      expect(result.trend).toBe('down');
    });

    it('calculates a flat score correctly', () => {
      const result = calculateScoreDiff(80, 80);
      expect(result.delta).toBe(0);
      expect(result.formattedDelta).toBe('0');
      expect(result.trend).toBe('flat');
    });

    it('gracefully handles missing before data', () => {
      const result = calculateScoreDiff(undefined, 85);
      expect(result.delta).toBeNull();
      expect(result.formattedDelta).toBe('—');
      expect(result.trend).toBe('unknown');
    });
  });

  describe('calculateTextDiff', () => {
    it('detects when text has changed', () => {
      const result = calculateTextDiff('Good job.', 'Great job!');
      expect(result.isChanged).toBe(true);
    });

    it('detects when text is identical', () => {
      const result = calculateTextDiff('Same feedback', 'Same feedback');
      expect(result.isChanged).toBe(false);
    });

    it('handles undefined or missing text', () => {
      const result = calculateTextDiff(undefined, 'New feedback');
      expect(result.isChanged).toBe(true);
    });
  });
});