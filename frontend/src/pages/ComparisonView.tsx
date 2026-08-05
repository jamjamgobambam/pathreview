// frontend/src/pages/ComparisonView.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/api';
import { Review } from '../types';
import { calculateScoreDiff, calculateTextDiff } from '../utils/diffFormatter';
import { formatDate } from '../utils/dateFormatters';

export const ComparisonView: React.FC = () => {
  const navigate = useNavigate();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [beforeId, setBeforeId] = useState<string>('');
  const [afterId, setAfterId] = useState<string>('');

  useEffect(() => {
    const fetchAllReviews = async () => {
      try {
        // Fetching a larger page size to populate the dropdowns
        const response = await apiClient.listReviews(1, 100);
        const fetchedReviews = response.items ?? [];
        
        // Sort chronologically (oldest first) so Before/After makes intuitive sense
        const sortedReviews = fetchedReviews.sort((a, b) => 
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
        
        setReviews(sortedReviews);
        
        // Auto-select the oldest and newest if there are at least two
        if (sortedReviews.length >= 2) {
          setBeforeId(sortedReviews[0].id);
          setAfterId(sortedReviews[sortedReviews.length - 1].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load review history');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllReviews();
  }, []);

  const beforeReview = reviews.find(r => r.id === beforeId);
  const afterReview = reviews.find(r => r.id === afterId);

  // Use our utility to calculate diffs
  const scoreDiff = calculateScoreDiff(beforeReview?.overall_score, afterReview?.overall_score);
  // Assuming the text field is called 'feedback'. Update this if it's 'notes', 'comments', etc.
  const textDiff = calculateTextDiff(beforeReview?.feedback, afterReview?.feedback);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Loading comparison data...</p>
      </div>
    );
  }

  if (reviews.length < 2) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto bg-white rounded-lg shadow p-12 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Not Enough Data</h2>
          <p className="text-gray-600 mb-6">
            You need at least two completed reviews to use the comparison tool. 
            Keep learning and submit another portfolio soon!
          </p>
          <button
            onClick={() => navigate('/reviews')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to History
          </button>
        </div>
      </div>
    );
  }

  const isSameReview = beforeId === afterId;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Compare Reviews</h1>
          <p className="text-gray-600 mt-2">See how your portfolio has improved over time</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Selection Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8 flex flex-col md:flex-row gap-6 items-end">
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-2">Before (Older Review)</label>
            <select
              value={beforeId}
              onChange={(e) => setBeforeId(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              {reviews.map(r => (
                <option key={r.id} value={r.id}>
                  {formatDate(r.created_at)} - {r.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-2">After (Newer Review)</label>
            <select
              value={afterId}
              onChange={(e) => setAfterId(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              {reviews.map(r => (
                <option key={r.id} value={r.id}>
                  {formatDate(r.created_at)} - {r.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {isSameReview ? (
          <div className="p-8 bg-yellow-50 border border-yellow-200 rounded-lg text-center">
            <p className="text-yellow-800 font-medium">Please select two different reviews to compare.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Score Comparison */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Overall Score</h3>
                {scoreDiff.trend !== 'unknown' && (
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    scoreDiff.trend === 'up' ? 'bg-green-100 text-green-800' : 
                    scoreDiff.trend === 'down' ? 'bg-red-100 text-red-800' : 
                    'bg-gray-100 text-gray-800'
                  }`}>
                    Delta: {scoreDiff.formattedDelta}
                  </span>
                )}
              </div>
              
              {/* Responsive Grid: Stacks on mobile, side-by-side on md screens */}
              <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-200">
                <div className="p-6 text-center">
                  <p className="text-sm text-gray-500 mb-2">Before ({formatDate(beforeReview?.created_at || '')})</p>
                  <p className="text-4xl font-bold text-gray-900">{scoreDiff.before ?? '—'}</p>
                </div>
                <div className="p-6 text-center">
                  <p className="text-sm text-gray-500 mb-2">After ({formatDate(afterReview?.created_at || '')})</p>
                  <p className="text-4xl font-bold text-gray-900">{scoreDiff.after ?? '—'}</p>
                </div>
              </div>
            </div>

            {/* Feedback Comparison */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 flex justify-between">
                  Feedback Notes
                  {textDiff.isChanged && <span className="text-sm font-normal text-blue-600 bg-blue-50 px-2 py-1 rounded">Content updated</span>}
                </h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-200">
                <div className="p-6">
                  <p className="text-sm font-medium text-gray-500 mb-4">Previous Feedback</p>
                  <p className="text-gray-700 whitespace-pre-wrap">{textDiff.before || 'No feedback provided.'}</p>
                </div>
                <div className="p-6">
                  <p className="text-sm font-medium text-gray-500 mb-4">New Feedback</p>
                  <p className="text-gray-700 whitespace-pre-wrap">{textDiff.after || 'No feedback provided.'}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};