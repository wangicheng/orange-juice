import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '../api';

interface Problem {
  id: number;
  oj_display_id: string;
  title: string;
}

interface TestCase {
  id: number;
  content: string;
  created_at: string;
}

function ProblemTestCases() {
    const { problemId } = useParams<{ problemId: string }>();
    const [problem, setProblem] = useState<Problem | null>(null);
    const [testCases, setTestCases] = useState<TestCase[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [copiedId, setCopiedId] = useState<number | null>(null);

    useEffect(() => {
        if (!problemId) return;

        const fetchData = async () => {
            try {
                const [problemRes, testCasesRes] = await Promise.all([
                    apiClient.get<Problem>(`/api/problems/${problemId}/`),
                    apiClient.get<TestCase[]>(`/api/problems/${problemId}/testcases/`)
                ]);
                setProblem(problemRes.data);
                setTestCases(testCasesRes.data);
            } catch (err) {
                setError('Failed to load data for this problem.');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [problemId]);

    const handleCopy = (text: string, id: number) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopiedId(id);
            setTimeout(() => {
                setCopiedId(null);
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    };

    if (loading) return <div className="text-center p-4">Loading test cases...</div>;
    if (error) return <div className="text-center p-4 text-red-500">{error}</div>;

    return (
        <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
            {problem && (
                 <div className="mb-6 border-b pb-4">
                    <h2 className="text-2xl font-bold text-gray-800">{problem.title}</h2>
                    <p className="text-gray-500">{problem.oj_display_id}</p>
                </div>
            )}
            <h3 className="text-xl font-semibold mb-4 text-gray-700">Test Cases ({testCases.length})</h3>
            <div className="space-y-4">
                {testCases.length > 0 ? (
                    testCases.map((tc, index) => (
                        <div key={tc.id} className="bg-gray-50 p-4 rounded-md shadow-sm">
                            <div className="flex justify-between items-center mb-2">
                                <h4 className="font-bold text-gray-600">Test Case #{index + 1}</h4>
                                <button
                                    onClick={() => handleCopy(tc.content, tc.id)}
                                    className="px-3 py-1 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                                >
                                    {copiedId === tc.id ? 'Copied!' : 'Copy'}
                                </button>
                            </div>
                            <pre className="bg-gray-900 text-white p-3 rounded-md text-sm whitespace-pre-wrap break-all">
                                <code>{tc.content}</code>
                            </pre>
                        </div>
                    ))
                ) : (
                    <p className="text-gray-500">No test cases found for this problem.</p>
                )}
            </div>
        </div>
    );
}

export default ProblemTestCases;