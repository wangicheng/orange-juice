import React, { useState } from 'react';
import apiClient from '../api';

interface ResultState {
  type: 'success' | 'error';
  message: string;
}

function CreateAccounts() {
    const [quantity, setQuantity] = useState<number>(10);
    const [loading, setLoading] = useState<boolean>(false);
    const [result, setResult] = useState<ResultState | null>(null);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);
        try {
            const response = await apiClient.post('/api/tasks/create-accounts', { quantity });
            setResult({ type: 'success', message: `Task started! Task ID: ${response.data.task_id}` });
        } catch (err: any) {
            setResult({ type: 'error', message: `Error: ${err.response?.data?.error || err.message}` });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Create Accounts Task</h2>
            <form onSubmit={handleSubmit}>
                <div className="mb-4">
                    <label htmlFor="quantity" className="block text-gray-700 font-bold mb-2">
                        Number of accounts to create:
                    </label>
                    <input
                        type="number"
                        id="quantity"
                        value={quantity}
                        onChange={(e) => setQuantity(parseInt(e.target.value, 10) || 0)}
                        min="1"
                        required
                        className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>
                <button type="submit" disabled={loading} className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:bg-blue-300">
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

export default CreateAccounts;