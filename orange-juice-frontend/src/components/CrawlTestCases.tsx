import React, { useState, useEffect } from 'react';
import apiClient from '../api';

// Data interfaces
interface Problem {
  id: number;
  oj_display_id: string;
  title: string;
}

interface CrawlerSource {
  id: number;
  name: string;
}

interface FormData {
  oj_problem_id: string;
  crawler_source_id: string;
  header_code: string;
  footer_code: string;
}

interface ResultState {
  type: 'success' | 'error';
  message: string;
}

function CrawlTestCases() {
    const [problems, setProblems] = useState<Problem[]>([]);
    const [crawlerSources, setCrawlerSources] = useState<CrawlerSource[]>([]);
    const [formData, setFormData] = useState<FormData>({
        oj_problem_id: '',
        crawler_source_id: '',
        header_code: '',
        footer_code: ''
    });
    const [loading, setLoading] = useState<boolean>(false);
    const [result, setResult] = useState<ResultState | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [problemsRes, sourcesRes] = await Promise.all([
                    apiClient.get<Problem[]>('/api/problems/'),
                    apiClient.get<CrawlerSource[]>('/api/crawler-sources/')
                ]);
                setProblems(problemsRes.data);
                setCrawlerSources(sourcesRes.data);
            } catch (error) {
                setResult({ type: 'error', message: 'Failed to load initial data.' });
            }
        };
        fetchData();
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLTextAreaElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);
        try {
            const response = await apiClient.post('/api/tasks/crawl-testcases', {
                ...formData,
                crawler_source_id: parseInt(formData.crawler_source_id)
            });
            setResult({ type: 'success', message: `Task started! Task ID: ${response.data.task_id}` });
        } catch (err: any) {
            setResult({ type: 'error', message: `Error: ${err.response?.data?.error || err.message}` });
        } finally {
            setLoading(false);
        }
    };

    const commonInputStyle = "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-green-500";

    return (
        <div className="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Crawl Test Cases Task</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label htmlFor="oj_problem_id" className="block text-gray-700 font-bold mb-2">OJ Problem ID:</label>
                    <select id="oj_problem_id" name="oj_problem_id" value={formData.oj_problem_id} onChange={handleChange} required className={commonInputStyle}>
                        <option value="" disabled>Select a problem</option>
                        {problems.map(p => <option key={p.id} value={p.oj_display_id}>{p.oj_display_id}: {p.title}</option>)}
                    </select>
                </div>
                <div>
                    <label htmlFor="crawler_source_id" className="block text-gray-700 font-bold mb-2">Crawler Source:</label>
                    <select id="crawler_source_id" name="crawler_source_id" value={formData.crawler_source_id} onChange={handleChange} required className={commonInputStyle}>
                        <option value="" disabled>Select a crawler source</option>
                        {crawlerSources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </select>
                </div>
                <div>
                    <label htmlFor="header_code" className="block text-gray-700 font-bold mb-2">Header Code:</label>
                    <textarea id="header_code" name="header_code" value={formData.header_code} onChange={handleChange} rows={4} className={`${commonInputStyle} font-mono text-sm`} />
                </div>
                <div>
                    <label htmlFor="footer_code" className="block text-gray-700 font-bold mb-2">Footer Code:</label>
                    <textarea id="footer_code" name="footer_code" value={formData.footer_code} onChange={handleChange} rows={4} className={`${commonInputStyle} font-mono text-sm`} />
                </div>
                <button type="submit" disabled={loading} className="w-full bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:bg-green-300">
                    {loading ? 'Starting...' : 'Start Task'}
                </button>
            </form>
            {result && (
                <div className={`mt-6 p-4 rounded-md text-sm ${result.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {result.message}
                </div>
            )}
        </div>
    );
}

export default CrawlTestCases;