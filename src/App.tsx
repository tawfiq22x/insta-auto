/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, Square, Save, Activity, CheckCircle, XCircle, 
  DollarSign, Clock, Terminal as TerminalIcon, Settings, 
  User, Lock, Server, Hash, Monitor, Smartphone, Trash2
} from 'lucide-react';
import type { LogEntry, AppConfig, AppStats } from './types';

const INITIAL_CONFIG: AppConfig = {
  username: 'Using Browser Cookies',
  password: '***',
  ldplayerPath: 'C:\\LDPlayer\\LDPlayer.exe',
  instanceName: 'LDPlayer',
  instanceIndex: '0',
  autoMode: true,
  headlessMode: false,
};

const INITIAL_STATS: AppStats = {
  accountsCreated: 0,
  failedAccounts: 0,
  earnings: 0,
  runtimeSeconds: 0,
};

export default function App() {
  const [config, setConfig] = useState<AppConfig>(INITIAL_CONFIG);
  const [stats, setStats] = useState<AppStats>(INITIAL_STATS);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentTask, setCurrentTask] = useState<string>('No active task');
  
  const logsEndRef = useRef<HTMLDivElement>(null);
  const runningRef = useRef(isRunning);
  runningRef.current = isRunning;

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Runtime timer
  useEffect(() => {
    let interval: number;
    if (isRunning) {
      interval = window.setInterval(() => {
        setStats(s => ({ ...s, runtimeSeconds: s.runtimeSeconds + 1 }));
      }, 1000);
    }
    return () => window.clearInterval(interval);
  }, [isRunning]);

  const addLog = (message: string, level: LogEntry['level'] = 'info') => {
    const newLog: LogEntry = {
      id: Math.random().toString(36).substring(7),
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      message,
      level
    };
    setLogs(prev => [...prev, newLog]);
  };

  const clearLogs = () => setLogs([]);

  const formatRuntime = (seconds: number) => {
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  const handleSaveConfig = () => {
    addLog('Configuration saved to local storage.', 'success');
    // In a real app, you would save to localStorage or backend here
  };

  const handleTestConnection = () => {
    addLog('Testing connections...', 'info');
    setTimeout(() => addLog('✅ EasyEarn: Connected (Simulated)', 'success'), 500);
    setTimeout(() => addLog(`✅ LDPlayer: Found at ${config.ldplayerPath} (Simulated)`, 'success'), 1000);
  };

  // Simulated Automation Loop
  useEffect(() => {
    if (!isRunning) return;

    let timeoutId: number;
    
    const runCycle = async () => {
      if (!runningRef.current) return;
      
      try {
        addLog('🌐 Logging into EasyEarn...', 'info');
        await new Promise(r => setTimeout(r, 1500));
        if (!runningRef.current) return;

        addLog('📋 Checking for tasks...', 'info');
        await new Promise(r => setTimeout(r, 2000));
        if (!runningRef.current) return;

        const fakeUser = `user_${Math.floor(Math.random() * 10000)}`;
        setCurrentTask(`Task: ${fakeUser} | Email: ${fakeUser}@example.com`);
        addLog(`📋 Task found: ${fakeUser}`, 'task');
        
        await new Promise(r => setTimeout(r, 1500));
        if (!runningRef.current) return;
        addLog('📧 Getting email verification code...', 'info');
        
        await new Promise(r => setTimeout(r, 2500));
        if (!runningRef.current) return;
        addLog(`📧 Code received: ${Math.floor(100000 + Math.random() * 900000)}`, 'success');

        await new Promise(r => setTimeout(r, 1000));
        if (!runningRef.current) return;
        addLog('📱 Creating Instagram account (LDPlayer)...', 'task');

        // Simulate LDPlayer taking time
        await new Promise(r => setTimeout(r, 4000));
        if (!runningRef.current) return;
        
        // Randomly succeed or fail (80% success rate)
        if (Math.random() > 0.2) {
          addLog(`✅ Account created: ${fakeUser}`, 'success');
          addLog('🔐 Submitting 2FA key to EasyEarn...', 'info');
          await new Promise(r => setTimeout(r, 1000));
          if (!runningRef.current) return;
          
          addLog('✅ 2FA key submitted', 'success');
          addLog('📤 Submitting final report...', 'info');
          await new Promise(r => setTimeout(r, 1000));
          if (!runningRef.current) return;

          addLog('✅ Task completed!', 'success');
          setStats(s => ({
            ...s,
            accountsCreated: s.accountsCreated + 1,
            earnings: s.earnings + 0.025
          }));
        } else {
          addLog(`❌ Account creation failed: Registration blocked by IP`, 'error');
          setStats(s => ({
            ...s,
            failedAccounts: s.failedAccounts + 1
          }));
        }

        if (!runningRef.current) return;
        addLog('🔄 Cycle complete, waiting for next task...', 'info');
        timeoutId = window.setTimeout(runCycle, 3000);

      } catch (err) {
        addLog(`❌ Automation error: ${err}`, 'error');
        setIsRunning(false);
      }
    };

    runCycle();

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [isRunning]);

  const toggleAutomation = () => {
    if (!isRunning) {
      addLog('🚀 Automation sequence initialized.', 'success');
      setIsRunning(true);
    } else {
      addLog('⏹️ Automation stopped by user.', 'warning');
      setIsRunning(false);
      setCurrentTask('No active task');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans p-6 selection:bg-indigo-500/30">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="flex items-center justify-between pb-4 border-b border-slate-800/60">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-indigo-500/10 rounded-xl ring-1 ring-indigo-500/20">
              <Activity className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Instagram Automation Suite</h1>
              <p className="text-sm text-slate-500">v5.0 Web Interface</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">Status:</span>
            {isRunning ? (
              <span className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-sm font-medium">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                Running
              </span>
            ) : (
              <span className="px-3 py-1 bg-slate-800 text-slate-400 border border-slate-700 rounded-full text-sm font-medium">
                Idle
              </span>
            )}
          </div>
        </header>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard icon={<CheckCircle className="w-5 h-5 text-emerald-400" />} label="Accounts Created" value={stats.accountsCreated} />
          <StatCard icon={<XCircle className="w-5 h-5 text-rose-400" />} label="Failed Attempts" value={stats.failedAccounts} />
          <StatCard icon={<DollarSign className="w-5 h-5 text-amber-400" />} label="Total Earnings" value={`$${stats.earnings.toFixed(3)}`} />
          <StatCard icon={<Clock className="w-5 h-5 text-blue-400" />} label="Session Runtime" value={formatRuntime(stats.runtimeSeconds)} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Config */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-6">
                <Settings className="w-5 h-5 text-slate-400" />
                <h2 className="text-lg font-semibold text-slate-200">Configuration</h2>
              </div>
              
              <div className="space-y-4">
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Cloudflare & Chrome</h3>
                  <div className="bg-emerald-950/30 border border-emerald-900/50 rounded-lg p-3">
                    <p className="text-sm text-emerald-400 font-medium mb-1">Stealth Browser Profile Enabled</p>
                    <p className="text-xs text-slate-400">
                      The bot will launch a dedicated browser window to bypass detection. 
                      <strong className="text-slate-300 block mt-1">If you see a Cloudflare checkbox, you must click it manually!</strong>
                      Your login will be saved forever automatically.
                    </p>
                  </div>
                </div>

                <div className="pt-4 space-y-3">
                  <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">LDPlayer Settings</h3>
                  <div className="space-y-3">
                    <div className="relative">
                      <Monitor className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <input 
                        type="text" 
                        placeholder="Path (e.g. C:\LDPlayer\LDPlayer.exe)" 
                        disabled={isRunning}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                        value={config.ldplayerPath}
                        onChange={e => setConfig({...config, ldplayerPath: e.target.value})}
                      />
                    </div>
                    <div className="flex gap-3">
                      <div className="relative flex-1">
                        <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input 
                          type="text" 
                          placeholder="Instance Name" 
                          disabled={isRunning}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                          value={config.instanceName}
                          onChange={e => setConfig({...config, instanceName: e.target.value})}
                        />
                      </div>
                      <div className="relative w-24">
                        <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input 
                          type="number" 
                          placeholder="Index" 
                          disabled={isRunning}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                          value={config.instanceIndex}
                          onChange={e => setConfig({...config, instanceIndex: e.target.value})}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="rounded border-slate-700 text-indigo-500 focus:ring-indigo-500/30 bg-slate-950 h-4 w-4"
                      checked={config.autoMode}
                      onChange={e => setConfig({...config, autoMode: e.target.checked})}
                      disabled={isRunning}
                    />
                    <span className="text-sm">Auto Mode</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="rounded border-slate-700 text-indigo-500 focus:ring-indigo-500/30 bg-slate-950 h-4 w-4"
                      checked={config.headlessMode}
                      onChange={e => setConfig({...config, headlessMode: e.target.checked})}
                      disabled={isRunning}
                    />
                    <span className="text-sm">Headless Mode</span>
                  </label>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-slate-800/60 flex gap-3">
                <button 
                  onClick={handleSaveConfig}
                  disabled={isRunning}
                  className="flex-1 flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" /> Save
                </button>
                <button 
                  onClick={handleTestConnection}
                  disabled={isRunning}
                  className="flex-1 flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                >
                  <Server className="w-4 h-4" /> Test
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Controls & Terminal */}
          <div className="lg:col-span-2 space-y-6 flex flex-col">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col sm:flex-row gap-4 items-center justify-between">
              <div className="space-y-1 w-full">
                <h3 className="text-sm font-medium text-slate-400">Current Task</h3>
                <div className="text-base text-slate-200 bg-slate-950 border border-slate-800/60 py-2 px-3 rounded-lg truncate w-full">
                  {currentTask}
                </div>
              </div>
              <div className="flex gap-3 shrink-0">
                <button 
                  onClick={toggleAutomation}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all shadow-sm ${
                    isRunning 
                      ? 'bg-rose-500/10 text-rose-500 hover:bg-rose-500/20 ring-1 ring-rose-500/30' 
                      : 'bg-indigo-500 text-white hover:bg-indigo-600 shadow-indigo-500/20'
                  }`}
                >
                  {isRunning ? (
                    <><Square className="w-5 h-5 fill-current" /> Stop Process</>
                  ) : (
                    <><Play className="w-5 h-5 fill-current" /> Start Automation</>
                  )}
                </button>
              </div>
            </div>

            <div className="bg-[#0D1117] border border-slate-800 rounded-2xl flex-1 flex flex-col overflow-hidden relative shadow-sm">
              <div className="bg-slate-900/50 border-b border-slate-800/60 p-3 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2 text-slate-400">
                  <TerminalIcon className="w-4 h-4" />
                  <span className="text-sm font-medium tracking-wide">Execution Log</span>
                </div>
                <button 
                  onClick={clearLogs}
                  className="text-slate-500 hover:text-slate-300 transition-colors p-1"
                  title="Clear Logs"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="p-4 flex-1 overflow-y-auto font-mono text-[13px] leading-relaxed">
                {logs.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-slate-600 italic">
                    Ready to start...
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    {logs.map(log => (
                      <div key={log.id} className="flex gap-3 break-all">
                        <span className="text-slate-500 shrink-0">[{log.timestamp}]</span>
                        <span className={`
                          ${log.level === 'info' ? 'text-blue-400/90' : ''}
                          ${log.level === 'success' ? 'text-emerald-400' : ''}
                          ${log.level === 'error' ? 'text-rose-400' : ''}
                          ${log.level === 'warning' ? 'text-amber-400' : ''}
                          ${log.level === 'task' ? 'text-purple-400' : ''}
                        `}>
                          {log.message}
                        </span>
                      </div>
                    ))}
                    <div ref={logsEndRef} />
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode, label: string, value: string | number }) {
  return (
    <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-sm flex items-center gap-4">
      <div className="p-3 bg-slate-950 border border-slate-800/60 rounded-xl shrink-0">
        {icon}
      </div>
      <div>
        <div className="text-sm text-slate-400 font-medium">{label}</div>
        <div className="text-xl font-bold text-slate-100">{value}</div>
      </div>
    </div>
  );
}

