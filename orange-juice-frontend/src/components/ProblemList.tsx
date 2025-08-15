import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';

interface Problem {
  id: number;
  oj_display_id: string;
  title: string;
}

function ProblemList() {
    const [problems, setProblems] = useState<Problem[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchProblems = async () => {
            try {
                const response = await apiClient.get<Problem[]>('/api/problems/');
                setProblems(response.data);
            } catch (err) {
                setError('Failed to load problems.');
            } finally {
                setLoading(false);
            }
        };
        fetchProblems();
    }, []);

    if (loading) return <div className="text-center p-4">Loading problems...</div>;
    if (error) return <div className="text-center p-4 text-red-500">{error}</div>;

    return (
        <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Problems</h2>
            <div className="space-y-2">
                {problems.map(problem => (
                    <Link
                        key={problem.id}
                        to={`/problems/${problem.oj_display_id}/testcases`}
                        className="block p-4 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
                    >
                        <p className="font-semibold text-blue-600">{problem.oj_display_id}</p>
                        <p className="text-gray-700">{problem.title}</p>
                    </Link>
                ))}
            </div>
        </div>
    );
}

export default ProblemList;