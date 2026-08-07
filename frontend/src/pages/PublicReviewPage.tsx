import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { BarChart3, Loader } from 'lucide-react';
import { apiClient } from '../services/api';
import { PublicReview } from '../types';

export const PublicReviewPage: React.FC = () => {
	const { token } = useParams<{ token: string }>();
	const [review, setReview] = useState<PublicReview | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');

	useEffect(() => {
		if (!token) return;
		const fetchReview = async () => {
			try {
				const data = await apiClient.getPublicReview(token);
				setReview(data);
			} catch (err) {
				setError(err instanceof Error ? err.message : 'Failed to load review');
			} finally {
				setLoading(false);
			}
		};
		fetchReview();
	}, [token]);

	return (
		<div className="min-h-screen bg-gray-50">
			<div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
				<div className="mb-8">
					<div className="flex items-center gap-2">
						<BarChart3 className="w-8 h-8 text-blue-600" />
						<h1 className="text-3xl font-bold text-gray-900">PathReview</h1>
					</div>
					<p className="text-gray-500 mt-1">Portfolio Review Summary</p>
				</div>

				{loading && (
					<div className="p-8 bg-white rounded-lg shadow text-center">
						<Loader className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
						<p className="text-gray-600">Loading review...</p>
					</div>
				)}

				{!loading && error && (
					<div className="p-8 bg-white rounded-lg shadow text-center">
						<p className="text-xl font-semibold text-gray-900 mb-2">
							{error === 'Share link has expired' ? 'This link has expired' : 'Review not found'}
						</p>
						<p className="text-gray-600">
							{error === 'Share link has expired'
								? 'The owner of this review will need to generate a new link.'
								: 'This review link is invalid or no longer exists.'}
						</p>
					</div>
				)}

				{!loading && review && (
					<>
						{review.overall_score !== undefined && (
							<div className="mb-8 bg-white rounded-lg shadow p-8">
								<h2 className="text-lg font-semibold text-gray-900 mb-4">Overall Score</h2>
								<div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
									<div className="h-full bg-blue-600 transition-all" style={{ width: `${review.overall_score * 100}%` }} />
								</div>
								<p className="mt-2 text-2xl font-bold text-blue-600">{Math.round(review.overall_score * 100)}/100</p>
							</div>
						)}

						<div className="space-y-6">
							<h2 className="text-2xl font-bold text-gray-900">Feedback</h2>
							{review.sections && review.sections.length > 0 ? (
								<div className="bg-white rounded-lg shadow divide-y divide-gray-200">
									{review.sections.map((section, index) => (
										<div key={index} className="p-6">
											<h3 className="text-lg font-semibold text-gray-900 mb-3">{section.section_name}</h3>
											<p className="text-gray-700 whitespace-pre-wrap mb-4">{section.content}</p>
											{section.suggestions && section.suggestions.length > 0 && (
												<>
													<h4 className="font-semibold text-gray-900 mb-2">Suggestions</h4>
													<ul className="space-y-2">
														{section.suggestions.map((suggestion, i) => (
															<li key={i} className="flex gap-3 text-gray-700">
																<span className="text-blue-600 font-semibold flex-shrink-0">•</span>
																<p>{suggestion}</p>
															</li>
														))}
													</ul>
												</>
											)}
										</div>
									))}
								</div>
							) : (
								<p className="text-gray-600">No feedback sections available</p>
							)}
						</div>
					</>
				)}
			</div>
		</div>
	);
};
