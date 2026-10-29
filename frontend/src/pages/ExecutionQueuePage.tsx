import React, { useEffect, useState } from 'react';
import {
  Cpu,
  RefreshCw,
  XCircle,
  Play,
  Terminal,
  Clock,
  AlertCircle,
  CheckCircle2,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import type { QueueTask } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

export const ExecutionQueuePage: React.FC = () => {
  const [currentTask, setCurrentTask] = useState<QueueTask | null>(null);
  const [queuedTasks, setQueuedTasks] = useState<QueueTask[]>([]);
  const [history, setHistory] = useState<QueueTask[]>([]);
  const [concurrency, setConcurrency] = useState({ active_workers: 0, max_workers: 1 });
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<QueueTask | null>(null);

  const fetchQueue = async () => {
    try {
      const data = await api.getQueue();
      setCurrentTask(data.current_task);
      setQueuedTasks(data.queued_tasks);
      setHistory(data.history);
      setConcurrency(data.concurrency);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleCancel = async (taskId: string) => {
    try {
      await api.cancelTask(taskId);
      fetchQueue();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Execution Queue</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor background autonomous tasks, queue status, and real-time execution logs.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-slate-200 bg-white text-xs font-mono text-slate-700">
            <Cpu size={13} className="text-blue-600" />
            <span>Capacity:</span>
            <span className="font-semibold text-slate-900">
              {concurrency.active_workers} / {concurrency.max_workers} Worker Active
            </span>
          </div>
          <button
            onClick={fetchQueue}
            className="p-1.5 rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      {/* Currently Running Task Box */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-blue-500 animate-ping" />
            <h2 className="text-sm font-semibold text-slate-900">Active Task Running</h2>
          </div>
          {currentTask && (
            <button
              onClick={() => handleCancel(currentTask.id)}
              className="text-xs font-semibold text-rose-600 hover:text-rose-700 flex items-center gap-1"
            >
              <XCircle size={13} /> Cancel Run
            </button>
          )}
        </div>

        {currentTask ? (
          <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900">{currentTask.name}</h3>
                  <StatusBadge status={currentTask.stage} />
                </div>
                <div className="flex items-center gap-4 text-xs font-mono text-slate-500 mt-1">
                  <span>ID: {currentTask.id}</span>
                  <span>Target: {currentTask.competition_slug}</span>
                  <span>Allocation: {currentTask.resource_allocation}</span>
                </div>
              </div>
            </div>

            {/* Live Logs Stream Window */}
            <div className="space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <Terminal size={12} /> Execution Logs
              </span>
              <div className="p-3 bg-slate-950 text-slate-200 rounded-lg font-mono text-xs max-h-48 overflow-y-auto space-y-1 select-text">
                {currentTask.logs.length === 0 ? (
                  <span className="text-slate-500 italic">Initializing runner...</span>
                ) : (
                  currentTask.logs.map((log, i) => (
                    <div key={i} className="text-slate-300">
                      {log}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-slate-400">
            Worker is currently idle. No tasks running.
          </div>
        )}
      </div>

      {/* Queued Tasks Table */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">Pending in Queue ({queuedTasks.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-2.5 px-3">Position</th>
                <th className="py-2.5 px-3">Task Name</th>
                <th className="py-2.5 px-3">Competition</th>
                <th className="py-2.5 px-3">Stage</th>
                <th className="py-2.5 px-3">Enqueued At</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {queuedTasks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-400">
                    Queue is empty.
                  </td>
                </tr>
              ) : (
                queuedTasks.map((t, idx) => (
                  <tr key={t.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-700">#{idx + 1}</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">{t.name}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">{t.competition_slug}</td>
                    <td className="py-2.5 px-3"><StatusBadge status={t.stage} size="sm" /></td>
                    <td className="py-2.5 px-3 text-slate-500">{t.created_at.split('T')[1]?.substring(0, 8)}</td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleCancel(t.id)}
                        className="text-xs font-semibold text-rose-600 hover:text-rose-800"
                      >
                        Cancel
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Task History Table */}
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">Recent Completed Tasks ({history.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-2.5 px-3">Task Name</th>
                <th className="py-2.5 px-3">Competition</th>
                <th className="py-2.5 px-3">Duration</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Finished At</th>
                <th className="py-2.5 px-3 text-right">Logs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-400">
                    No task history recorded yet.
                  </td>
                </tr>
              ) : (
                history.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-medium text-slate-900">{t.name}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">{t.competition_slug}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-700">{t.elapsed_time || '—'}</td>
                    <td className="py-2.5 px-3"><StatusBadge status={t.status} size="sm" /></td>
                    <td className="py-2.5 px-3 text-slate-500">{t.end_time?.split('T')[1]?.substring(0, 8) || '—'}</td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => setSelectedTask(t)}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                      >
                        View Logs
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Task Logs Modal */}
      {selectedTask && (
        <Modal
          isOpen={Boolean(selectedTask)}
          onClose={() => setSelectedTask(null)}
          title={selectedTask.name}
          subtitle={`Task ID: ${selectedTask.id} | Duration: ${selectedTask.elapsed_time || '—'}`}
          maxWidth="2xl"
        >
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700 font-mono">
                Target: {selectedTask.competition_slug}
              </span>
              <StatusBadge status={selectedTask.status} size="sm" />
            </div>
            {selectedTask.error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-800">
                <strong>Error:</strong> {selectedTask.error}
              </div>
            )}
            <pre className="p-3 bg-slate-950 text-slate-200 rounded-lg font-mono text-xs max-h-64 overflow-y-auto whitespace-pre-wrap">
              {selectedTask.logs.join('\n') || 'No log messages recorded.'}
            </pre>
          </div>
        </Modal>
      )}
    </div>
  );
};
