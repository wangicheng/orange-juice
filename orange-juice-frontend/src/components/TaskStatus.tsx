import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../api';

// 與後端 crawler_core.py 中的 CrawlerState 一致
interface CrawlerState {
    state: 'NEEDS_PREDICT' | 'FINDING_NEXT_CHAR' | 'FINDING_PREFIX_LENGTH_LENGTH' | 'FINDING_PREFIX_LENGTH' | 'DONE';
    prefix: string;
    limit: number;
    prefix_length_length: number;
    prefix_length: number;
    position: number;
    lr_slope: number | null;
    lr_intercept: number | null;
}

interface Task {
    id: string;
    status: 'PENDING' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILURE' | 'PAUSED';
    progress: number;
    result: any;
    updated_at: string;
    task_type?: string;
    crawler_state?: CrawlerState;
}

function TaskStatus() {
    const { taskId } = useParams<{ taskId: string }>();
    const [task, setTask] = useState<Task | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [isResuming, setIsResuming] = useState<boolean>(false);
    const [isPausing, setIsPausing] = useState<boolean>(false);
    // 使用物件來分別儲存 state 的各個欄位
    const [editableCrawlerState, setEditableCrawlerState] = useState<Partial<CrawlerState>>({});
    const [resumeMessage, setResumeMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

    useEffect(() => {
        let isMounted = true;
        const fetchTaskStatus = async () => {
            try {
                const response = await apiClient.get<Task>(`/api/tasks/${taskId}/status/`);
                if (isMounted) {
                    setTask(response.data);
                    if (response.data.status === 'SUCCESS' || response.data.status === 'FAILURE') {
                        return true; // Stop polling
                    }
                }
            } catch (err: any) {
                if (isMounted) {
                    setError(err.response?.data?.error || 'Failed to fetch task status.');
                }
                return true; // Stop polling on error
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
            return false; // Continue polling
        };

        const poll = async () => {
            if (await fetchTaskStatus()) {
                clearInterval(intervalId);
            }
        };

        poll(); // Initial fetch
        const intervalId = setInterval(poll, 3000); // Poll every 3 seconds

        return () => {
            isMounted = false;
            clearInterval(intervalId); // Cleanup on component unmount
        };
    }, [taskId, isResuming]); // Rerun effect if we trigger a resume

    useEffect(() => {
        // 當 task 資料載入時，更新 editableCrawlerState 的預設值
        if (task && task.crawler_state) {
            setEditableCrawlerState(task.crawler_state);
        } else if (task) {
            setEditableCrawlerState({});
        }
    }, [task]);

    // 處理各個輸入框變更的通用函式
    const handleStateChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setEditableCrawlerState(prevState => ({
            ...prevState,
            [name]: value,
        }));
    };

    const handleResumeTask = async () => {
        if (!taskId) return;
        setIsResuming(true);
        setResumeMessage(null);
        try {
            // 建立一個要提交的 state 物件副本
            const stateToSubmit: { [key: string]: any } = { ...editableCrawlerState };

            // 將表單中的字串值轉換回數字或 null
            const numericFields: (keyof CrawlerState)[] = ['limit', 'prefix_length_length', 'prefix_length', 'position', 'lr_slope', 'lr_intercept'];
            
            for (const field of numericFields) {
                const value = stateToSubmit[field];
                if (value !== null && value !== undefined && String(value).trim() !== '') {
                    stateToSubmit[field] = Number(value);
                } else {
                    stateToSubmit[field] = null; // 確保空字串被轉換為 null
                }
            }

            await apiClient.post(`/api/tasks/${taskId}/resume/`, {
                crawler_state: stateToSubmit,
            });
            
            setResumeMessage({ type: 'success', text: 'Task resume request sent successfully! Refreshing status...' });
            // 重置狀態以觸發重新輪詢
            setLoading(true);
            setTask(null); 
        } catch (err: any) {
            setResumeMessage({ type: 'error', text: err.response?.data?.error || 'Failed to resume task.' });
            setIsResuming(false);
        }
    };

    const handlePauseTask = async () => {
        if (!taskId) return;
        setIsPausing(true);
        setResumeMessage(null);
        try {
            await apiClient.post(`/api/tasks/${taskId}/pause/`);
            setResumeMessage({ type: 'success', text: 'Task pause request sent successfully! Status will update shortly.' });
        } catch (err: any) {
            setResumeMessage({ type: 'error', text: err.response?.data?.error || 'Failed to pause task.' });
        } finally {
            setIsPausing(false);
        }
    };

    const getStatusColor = (status: Task['status']) => {
        switch (status) {
            case 'SUCCESS': return 'text-green-600';
            case 'FAILURE': return 'text-red-600';
            case 'IN_PROGRESS': return 'text-blue-600';
            case 'PENDING': return 'text-gray-600';
            case 'PAUSED': return 'text-yellow-600';
            default: return 'text-gray-800';
        }
    };

    if (loading && !task) {
        return <div className="text-center p-8">Loading task details...</div>;
    }

    if (error) {
        return <div className="max-w-4xl mx-auto bg-red-100 text-red-800 p-4 rounded-lg shadow-md mt-6">Error: {error}</div>;
    }

    if (!task) {
        return <div className="text-center p-8">Task not found.</div>;
    }

    return (
        <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md mt-6">
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-bold">Task Status</h1>
                {task && (task.status === 'IN_PROGRESS' || task.status === 'PENDING') && (
                    <button
                        onClick={handlePauseTask}
                        disabled={isPausing}
                        className="bg-yellow-500 text-white font-bold py-2 px-4 rounded hover:bg-yellow-600 disabled:bg-gray-400"
                    >
                        {isPausing ? 'Pausing...' : 'Pause Task'}
                    </button>
                )}
            </div>
            <div className="space-y-4">
                <div>
                    <span className="font-bold">Task ID:</span>
                    <span className="ml-2 font-mono bg-gray-100 p-1 rounded">{task.id}</span>
                </div>
                <div>
                    <span className="font-bold">Status:</span>
                    <span className={`ml-2 font-bold ${getStatusColor(task.status)}`}>{task.status}</span>
                </div>
                <div>
                    <span className="font-bold">Last Updated:</span>
                    <span className="ml-2">{new Date(task.updated_at).toLocaleString()}</span>
                </div>
                <div>
                    <span className="font-bold">Progress:</span>
                    <div className="w-full bg-gray-200 rounded-full h-4 mt-2">
                        <div
                            className={`h-4 rounded-full ${task.status === 'SUCCESS' ? 'bg-green-500' : 'bg-blue-600'}`}
                            style={{ width: `${task.progress}%` }}
                        ></div>
                    </div>
                    <span className="text-sm">{task.progress}%</span>
                </div>
                {task.result && (
                    <div>
                        <span className="font-bold">Result:</span>
                        <pre className="mt-2 p-4 bg-gray-100 rounded-md text-sm overflow-auto">
                            {JSON.stringify(task.result, null, 2)}
                        </pre>
                    </div>
                )}

                {/* Resume Section */}
                {task.task_type === 'CrawlTestCasesTask' && (task.status === 'FAILURE' || task.status === 'PAUSED') && (
                    <div className="mt-6 border-t pt-6">
                        <h2 className="text-xl font-bold mb-2">Resume Task</h2>
                        <p className="text-sm text-gray-600 mb-4">
                            {task.status === 'PAUSED'
                                ? 'The task is paused. You can resume it now or modify the state before resuming.'
                                : 'The task failed. You can modify the last saved state below and attempt to resume it.'
                            }
                        </p>
                        <div className="mb-4 p-4 border rounded-md bg-gray-50">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* State */}
                                <div>
                                    <label htmlFor="state" className="block font-bold mb-1 text-sm text-gray-700">State:</label>
                                    <select id="state" name="state" value={editableCrawlerState.state || ''} onChange={handleStateChange} className="w-full p-2 border rounded font-mono text-sm">
                                        <option value="NEEDS_PREDICT">NEEDS_PREDICT</option>
                                        <option value="FINDING_NEXT_CHAR">FINDING_NEXT_CHAR</option>
                                        <option value="FINDING_PREFIX_LENGTH_LENGTH">FINDING_PREFIX_LENGTH_LENGTH</option>
                                        <option value="FINDING_PREFIX_LENGTH">FINDING_PREFIX_LENGTH</option>
                                        <option value="DONE">DONE</option>
                                    </select>
                                </div>
                                {/* Limit */}
                                <div>
                                    <label htmlFor="limit" className="block font-bold mb-1 text-sm text-gray-700">Limit:</label>
                                    <input type="number" id="limit" name="limit" value={editableCrawlerState.limit ?? ''} onChange={handleStateChange} className="w-full p-2 border rounded font-mono text-sm" />
                                </div>
                                {/* Prefix */}
                                <div className="md:col-span-2">
                                    <label htmlFor="prefix" className="block font-bold mb-1 text-sm text-gray-700">Prefix:</label>
                                    <textarea id="prefix" name="prefix" className="w-full p-2 border rounded font-mono text-sm" rows={3} value={editableCrawlerState.prefix || ''} onChange={handleStateChange} />
                                </div>
                                {/* prefix_length_length */}
                                <div>
                                    <label htmlFor="prefix_length_length" className="block font-bold mb-1 text-sm text-gray-700">Prefix Length Length:</label>
                                    <input type="number" id="prefix_length_length" name="prefix_length_length" value={editableCrawlerState.prefix_length_length ?? ''} onChange={handleStateChange} className="w-full p-2 border rounded font-mono text-sm" />
                                </div>
                                {/* prefix_length */}
                                <div>
                                    <label htmlFor="prefix_length" className="block font-bold mb-1 text-sm text-gray-700">Prefix Length:</label>
                                    <input type="number" id="prefix_length" name="prefix_length" value={editableCrawlerState.prefix_length ?? ''} onChange={handleStateChange} className="w-full p-2 border rounded font-mono text-sm" />
                                </div>
                                {/* position */}
                                <div>
                                    <label htmlFor="position" className="block font-bold mb-1 text-sm text-gray-700">Position:</label>
                                    <input type="number" id="position" name="position" value={editableCrawlerState.position ?? ''} onChange={handleStateChange} className="w-full p-2 border rounded font-mono text-sm" />
                                </div>
                                <div></div> {/* Spacer */}
                                {/* lr_slope */}
                                <div>
                                    <label htmlFor="lr_slope" className="block font-bold mb-1 text-sm text-gray-700">LR Slope:</label>
                                    <input type="number" step="any" id="lr_slope" name="lr_slope" value={editableCrawlerState.lr_slope ?? ''} onChange={handleStateChange} className="w-full p-2 border rounded font-mono text-sm" placeholder="null" />
                                </div>
                                {/* lr_intercept */}
                                <div>
                                    <label htmlFor="lr_intercept" className="block font-bold mb-1 text-sm text-gray-700">LR Intercept:</label>
                                    <input type="number" step="any" id="lr_intercept" name="lr_intercept" value={editableCrawlerState.lr_intercept ?? ''} onChange={handleStateChange} className="w-full p-2 border rounded font-mono text-sm" placeholder="null" />
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={handleResumeTask}
                            disabled={isResuming}
                            className="bg-orange-500 text-white font-bold py-2 px-4 rounded hover:bg-orange-600 disabled:bg-gray-400"
                        >
                            {isResuming ? 'Resuming...' : 'Resume Task'}
                        </button>
                        {resumeMessage && (
                            <div className={`mt-4 p-3 rounded text-sm ${resumeMessage.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                {resumeMessage.text}
                            </div>
                        )}
                    </div>
                )}

                <div className="mt-6">
                    <Link to="/" className="text-blue-500 hover:underline">&larr; Back to Home</Link>
                </div>
            </div>
        </div>
    );
}

export default TaskStatus;