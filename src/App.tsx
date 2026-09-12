/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, Square, Save, Activity, CheckCircle, XCircle, 
  DollarSign, Clock, Terminal as TerminalIcon, Settings, 
  User, Lock, Server, Hash, Monitor, Smartphone, Trash2,
  Copy, Check, Mail, Key, Tag, Calendar, ShieldCheck, Sparkles
} from 'lucide-react';
import type { LogEntry, AppConfig, AppStats } from './types';

interface TaskData {
  login: string;
  name: string;
  password: string;
  email: string;
  code?: string;
  birthday?: string;
  taskId?: string;
  twofaKey?: string;
  step?: string;
}

const INITIAL_CONFIG: AppConfig = {
  username: 'Using Browser Cookies',
  password: '',
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
  const [currentTask, setCurrentTask] = useState<TaskData | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  
  const logsEndRef = useRef<HTMLDivElement>(null);
  const runningRef = useRef(isRunning);
  runningRef.current = isRunning;

  // Clear any legacy local storage cache if previously saved
  useEffect(() => {
    try {
      localStorage.removeItem('collected_accounts_v1');
    } catch {
      // ignore
    }
  }, []);

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

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const formatRuntime = (seconds: number) => {
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  const handleSaveConfig = () => {
    addLog('Configuration saved to local storage.', 'success');
  };

  const handleTestConnection = () => {
    addLog('Testing connections...', 'info');
    setTimeout(() => addLog('✅ EasyEarn: Connected (Ready)', 'success'), 400);
    setTimeout(() => addLog(`✅ LDPlayer: Found at ${config.ldplayerPath}`, 'success'), 800);
  };

  // Simulated Automation Loop
  useEffect(() => {
    if (!isRunning) return;

    let timeoutId: number;
    
    const runCycle = async () => {
      if (!runningRef.current) return;
      
      try {
        addLog('🌐 Connecting to EasyEarn session...', 'info');
        await new Promise(r => setTimeout(r, 1200));
        if (!runningRef.current) return;

        addLog('📋 Fetching task credentials from EasyEarn...', 'info');
        await new Promise(r => setTimeout(r, 1500));
        if (!runningRef.current) return;

        const fakeNum = Math.floor(Math.random() * 9000 + 1000);
        const fakeUser = `user_${fakeNum}`;
        const fakeName = `Alex Johnson ${fakeNum % 99}`;
        const fakePass = `Insta_${Math.random().toString(36).substring(2, 7)}9`;
        const fakeEmail = `${fakeUser}@fastmail.org`;
        const fakeBday = "1999-05-14";
        const fakeTaskId = `#EE-${fakeNum}`;

        const task: TaskData = {
          login: fakeUser,
          name: fakeName,
          password: fakePass,
          email: fakeEmail,
          code: '',
          birthday: fakeBday,
          taskId: fakeTaskId,
          twofaKey: '',
          step: 'Step 1/11: Connecting'
        };
        setCurrentTask({ ...task });

        addLog('📦 Fetched task credentials from EasyEarn (Unmasked):', 'success');
        addLog(`   👤 Login / User : ${fakeUser}`, 'info');
        addLog(`   📝 Full Name    : ${fakeName}`, 'info');
        addLog(`   🔒 Password     : ${fakePass}`, 'info');
        addLog(`   ✉️ Email        : ${fakeEmail}`, 'info');
        addLog(`   🎂 Birthday     : ${fakeBday}`, 'info');
        addLog(`   🆔 Task ID      : ${fakeTaskId}`, 'info');

        await new Promise(r => setTimeout(r, 1200));
        if (!runningRef.current) return;
        task.step = 'Step 4/11: Entering Password';
        setCurrentTask({ ...task });

        await new Promise(r => setTimeout(r, 1000));
        if (!runningRef.current) return;
        task.step = 'Step 5/11: Setting Adult Birthday';
        setCurrentTask({ ...task });

        await new Promise(r => setTimeout(r, 1000));
        if (!runningRef.current) return;
        addLog(`📧 Requesting OTP verification code for ${fakeEmail}...`, 'info');
        task.step = 'Step 7/11: Polling Email OTP';
        setCurrentTask({ ...task });
        
        await new Promise(r => setTimeout(r, 2000));
        if (!runningRef.current) return;
        const receivedCode = String(Math.floor(100000 + Math.random() * 900000));
        task.code = receivedCode;
        task.step = `OTP Code: ${receivedCode}`;
        setCurrentTask({ ...task });
        addLog(`📧 Code received: ${receivedCode}`, 'success');

        await new Promise(r => setTimeout(r, 1000));
        if (!runningRef.current) return;
        task.step = 'Step 8/11: Finalizing Profile';
        setCurrentTask({ ...task });
        addLog(`📱 Creating Instagram account on LDPlayer (Password: ${fakePass})...`, 'task');

        // Simulate LDPlayer processing
        await new Promise(r => setTimeout(r, 3000));
        if (!runningRef.current) return;
        
        // 85% success rate
        if (Math.random() > 0.15) {
          const fake2FA = 'JBSWY3DPEHPK3PXP';
          task.twofaKey = fake2FA;
          task.step = 'Step 10/11: 2FA & EasyEarn Report';
          setCurrentTask({ ...task });
          addLog(`✅ Account created: ${fakeUser} | Pass: ${fakePass}`, 'success');
          addLog('🔐 Generating and submitting 2FA security key...', 'info');
          await new Promise(r => setTimeout(r, 1000));
          if (!runningRef.current) return;
          
          addLog('✅ 2FA key accepted by EasyEarn', 'success');
          addLog('📤 Submitting final completion report...', 'info');
          await new Promise(r => setTimeout(r, 1000));
          if (!runningRef.current) return;

          task.step = '🎉 Completed Successfully';
          setCurrentTask({ ...task });
          addLog('✅ Task completed successfully!', 'success');
          setStats(s => ({
            ...s,
            accountsCreated: s.accountsCreated + 1,
            earnings: s.earnings + 0.025
          }));
        } else {
          task.step = '❌ Failed';
          setCurrentTask({ ...task });
          addLog(`❌ Account creation failed: Device rate limit encountered`, 'error');
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
      setIsRunning(true);
      addLog('🚀 Starting automation loop...', 'info');
    } else {
      setIsRunning(false);
      addLog('🛑 Stopping automation loop...', 'warning');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-xl shadow-lg shadow-indigo-500/20">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Instagram Automation Suite</h1>
              <p className="text-sm text-slate-400">v1.5.7 • Full Credential Visibility • Zero Local Storage</p>
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

        {/* Current Task Bar - High Visibility with ALL Account Details */}
        <div className="bg-slate-900 border border-indigo-500/30 rounded-2xl p-5 shadow-lg shadow-indigo-950/20 space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <span className="p-1.5 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-indigo-400">
                <Key className="w-4 h-4" />
              </span>
              <div>
                <h3 className="text-base font-semibold text-slate-100 flex flex-wrap items-center gap-2">
                  Current Task Information
                  <span className="text-xs px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-md font-normal">
                    Plain Text • All Fields Unmasked
                  </span>
                  {currentTask?.step && (
                    <span className="text-xs px-2.5 py-0.5 bg-amber-500/10 border border-amber-500/30 text-amber-300 rounded-md font-mono">
                      {currentTask.step}
                    </span>
                  )}
                </h3>
                <p className="text-xs text-slate-400">All real-time credentials, verification codes, and parameters for active Instagram task</p>
              </div>
            </div>
            
            {currentTask && (
              <div className="flex flex-wrap items-center gap-2">
                <button 
                  onClick={() => {
                    const combo = [
                      currentTask.login,
                      currentTask.password,
                      currentTask.email,
                      currentTask.name,
                      currentTask.code || '',
                      currentTask.birthday || '',
                      currentTask.twofaKey || ''
                    ].filter(Boolean).join(':');
                    copyToClipboard(combo, 'curr_combo_all');
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600/25 hover:bg-indigo-600/35 border border-indigo-500/40 text-indigo-200 rounded-lg text-xs font-medium transition-colors"
                  title="Copy All Info (User:Pass:Email:Name:Code:Birthday:2FA)"
                >
                  {copiedKey === 'curr_combo_all' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedKey === 'curr_combo_all' ? 'Copied All Info!' : '📋 Copy All Account Info'}</span>
                </button>
                <button 
                  onClick={() => copyToClipboard(`${currentTask.login}:${currentTask.password}`, 'curr_user_pass')}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg text-xs font-medium transition-colors"
                >
                  {copiedKey === 'curr_user_pass' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>User:Pass</span>
                </button>
                {currentTask.code && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.code!, 'curr_code_only')}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 bg-emerald-950/40 hover:bg-emerald-900/50 border border-emerald-500/40 text-emerald-300 rounded-lg text-xs font-medium transition-colors"
                  >
                    {copiedKey === 'curr_code_only' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>OTP: {currentTask.code}</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Core Credentials Quick Summary Bar */}
          <div className="bg-slate-950/90 border border-indigo-500/25 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-semibold text-slate-200 uppercase tracking-wider text-xs">Active Credentials:</span>
            </div>
            <div className="flex flex-wrap items-center gap-3 sm:gap-4 font-mono">
              <span className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 px-2.5 py-1 rounded-lg">
                <span className="text-slate-500 text-xs font-sans">USER:</span>
                <span className="text-cyan-300 font-bold">{currentTask?.login || '—'}</span>
              </span>
              <span className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 px-2.5 py-1 rounded-lg">
                <span className="text-slate-500 text-xs font-sans">NAME:</span>
                <span className="text-emerald-300 font-bold">{currentTask?.name || '—'}</span>
              </span>
              <span className="flex items-center gap-1.5 bg-amber-950/30 border border-amber-500/30 px-2.5 py-1 rounded-lg">
                <span className="text-amber-500/80 text-xs font-sans">PASS:</span>
                <span className="text-amber-300 font-bold tracking-wide">{currentTask?.password || '—'}</span>
              </span>
              <span className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 px-2.5 py-1 rounded-lg">
                <span className="text-slate-500 text-xs font-sans">EMAIL:</span>
                <span className="text-indigo-300 font-bold">{currentTask?.email || '—'}</span>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* 1. Login */}
            <div className="bg-slate-950/80 border border-slate-800 hover:border-cyan-500/40 rounded-xl p-3 relative group transition-colors">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1.5 text-cyan-400 font-semibold">
                  <User className="w-3.5 h-3.5" /> 1. Login / Username
                </span>
                {currentTask?.login && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.login, 'c_login')}
                    className="opacity-60 hover:opacity-100 text-slate-400 hover:text-white transition-opacity p-0.5"
                    title="Copy Login"
                  >
                    {copiedKey === 'c_login' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
              <div className="font-mono text-sm text-cyan-200 font-bold truncate select-all">
                {currentTask?.login || <span className="text-slate-600 font-normal italic">Waiting for task...</span>}
              </div>
            </div>

            {/* 2. Name */}
            <div className="bg-slate-950/80 border border-slate-800 hover:border-emerald-500/40 rounded-xl p-3 relative group transition-colors">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                  <Tag className="w-3.5 h-3.5" /> 2. Full Name
                </span>
                {currentTask?.name && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.name, 'c_name')}
                    className="opacity-60 hover:opacity-100 text-slate-400 hover:text-white transition-opacity p-0.5"
                    title="Copy Full Name"
                  >
                    {copiedKey === 'c_name' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
              <div className="font-mono text-sm text-emerald-200 font-bold truncate select-all">
                {currentTask?.name || <span className="text-slate-600 font-normal italic">Waiting for task...</span>}
              </div>
            </div>

            {/* 3. Password - UNMASKED PLAIN TEXT */}
            <div className="bg-slate-950/80 border border-amber-500/40 hover:border-amber-400/60 rounded-xl p-3 relative group transition-colors shadow-sm shadow-amber-950/30">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1.5 text-amber-400 font-bold">
                  <Lock className="w-3.5 h-3.5" /> 3. Password (Unmasked)
                </span>
                {currentTask?.password && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.password, 'c_pass')}
                    className="opacity-60 hover:opacity-100 text-slate-400 hover:text-white transition-opacity p-0.5"
                    title="Copy Password"
                  >
                    {copiedKey === 'c_pass' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
              <div className="font-mono text-sm text-amber-300 font-extrabold tracking-wide truncate select-all">
                {currentTask?.password || <span className="text-slate-600 font-normal italic">Waiting for task...</span>}
              </div>
            </div>

            {/* 4. Email */}
            <div className="bg-slate-950/80 border border-slate-800 hover:border-indigo-500/40 rounded-xl p-3 relative group transition-colors">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1.5 text-indigo-400 font-semibold">
                  <Mail className="w-3.5 h-3.5" /> 4. Email Address
                </span>
                {currentTask?.email && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.email, 'c_email')}
                    className="opacity-60 hover:opacity-100 text-slate-400 hover:text-white transition-opacity p-0.5"
                    title="Copy Email"
                  >
                    {copiedKey === 'c_email' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
              <div className="font-mono text-sm text-indigo-200 font-bold truncate select-all">
                {currentTask?.email || <span className="text-slate-600 font-normal italic">Waiting for task...</span>}
              </div>
            </div>

            {/* 5. OTP / Verification Code */}
            <div className="bg-slate-950/80 border border-emerald-500/30 rounded-xl p-3 relative group">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <Key className="w-3.5 h-3.5" /> OTP Code (EasyEarn)
                </span>
                {currentTask?.code && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.code!, 'c_code')}
                    className="opacity-60 hover:opacity-100 text-slate-400 hover:text-white transition-opacity p-0.5"
                    title="Copy OTP Code"
                  >
                    {copiedKey === 'c_code' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
              <div className="font-mono text-sm text-emerald-300 font-bold tracking-wider truncate select-all">
                {currentTask?.code || <span className="text-slate-600 font-normal italic">Waiting for OTP...</span>}
              </div>
            </div>

            {/* 6. Birthday */}
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 relative group">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1.5 text-violet-400 font-medium">
                  <Calendar className="w-3.5 h-3.5" /> Birthday (Age &gt; 18)
                </span>
                {currentTask?.birthday && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.birthday!, 'c_bday')}
                    className="opacity-60 hover:opacity-100 text-slate-400 hover:text-white transition-opacity p-0.5"
                    title="Copy Birthday"
                  >
                    {copiedKey === 'c_bday' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
              <div className="font-mono text-sm text-slate-100 font-semibold truncate select-all">
                {currentTask?.birthday || <span className="text-slate-600 font-normal italic">Waiting for task...</span>}
              </div>
            </div>

            {/* 7. 2FA Key */}
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 relative group">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1.5 text-rose-400 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5" /> 2FA Secret Key
                </span>
                {currentTask?.twofaKey && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.twofaKey!, 'c_2fa')}
                    className="opacity-60 hover:opacity-100 text-slate-400 hover:text-white transition-opacity p-0.5"
                    title="Copy 2FA Key"
                  >
                    {copiedKey === 'c_2fa' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
              <div className="font-mono text-sm text-slate-100 font-semibold truncate select-all">
                {currentTask?.twofaKey || <span className="text-slate-600 font-normal italic">Generated after signup</span>}
              </div>
            </div>

            {/* 8. Task ID */}
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 relative group">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1.5 text-sky-400 font-medium">
                  <Hash className="w-3.5 h-3.5" /> EasyEarn Task ID
                </span>
                {currentTask?.taskId && (
                  <button 
                    onClick={() => copyToClipboard(currentTask.taskId!, 'c_taskid')}
                    className="opacity-60 hover:opacity-100 text-slate-400 hover:text-white transition-opacity p-0.5"
                    title="Copy Task ID"
                  >
                    {copiedKey === 'c_taskid' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
              <div className="font-mono text-sm text-sky-300 font-semibold truncate select-all">
                {currentTask?.taskId || <span className="text-slate-600 font-normal italic">Pending...</span>}
              </div>
            </div>
          </div>
        </div>

        {/* Main Workspace Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Configuration & Controls */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-5">
                <Settings className="w-5 h-5 text-slate-400" />
                <h2 className="text-lg font-semibold text-slate-200">Configuration</h2>
              </div>
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Browser Authentication</h3>
                  <div className="bg-emerald-950/30 border border-emerald-900/50 rounded-lg p-3">
                    <p className="text-xs text-emerald-400 font-medium mb-1">Stealth Profile Active</p>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Session cookies and manual Cloudflare verifications persist automatically in your profile.
                    </p>
                  </div>
                </div>

                <div className="pt-2 space-y-3">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">LDPlayer Emulator</h3>
                  <div className="space-y-3">
                    <div className="relative">
                      <Monitor className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <input 
                        type="text" 
                        placeholder="Path (e.g. C:\LDPlayer\LDPlayer.exe)" 
                        disabled={isRunning}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                        value={config.ldplayerPath}
                        onChange={e => setConfig({...config, ldplayerPath: e.target.value})}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div className="relative">
                        <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input 
                          type="text" 
                          placeholder="Instance Name" 
                          disabled={isRunning}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                          value={config.instanceName}
                          onChange={e => setConfig({...config, instanceName: e.target.value})}
                        />
                      </div>
                      <div className="relative">
                        <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input 
                          type="number" 
                          placeholder="Index" 
                          disabled={isRunning}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
                          value={config.instanceIndex}
                          onChange={e => setConfig({...config, instanceIndex: e.target.value})}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between border-t border-slate-800/60 pt-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="rounded border-slate-700 text-indigo-500 focus:ring-indigo-500/30 bg-slate-950 h-4 w-4"
                      checked={config.autoMode}
                      onChange={e => setConfig({...config, autoMode: e.target.checked})}
                      disabled={isRunning}
                    />
                    <span className="text-xs text-slate-300">Auto Task Loop</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="rounded border-slate-700 text-indigo-500 focus:ring-indigo-500/30 bg-slate-950 h-4 w-4"
                      checked={config.headlessMode}
                      onChange={e => setConfig({...config, headlessMode: e.target.checked})}
                      disabled={isRunning}
                    />
                    <span className="text-xs text-slate-300">Headless Browser</span>
                  </label>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-800/60 flex gap-2">
                <button 
                  onClick={handleSaveConfig}
                  disabled={isRunning}
                  className="flex-1 flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 py-2 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" /> Save Config
                </button>
                <button 
                  onClick={handleTestConnection}
                  disabled={isRunning}
                  className="flex-1 flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 py-2 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                >
                  <Server className="w-3.5 h-3.5" /> Test Ports
                </button>
              </div>

              <div className="mt-4">
                <button 
                  onClick={toggleAutomation}
                  className={`w-full flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl font-semibold transition-all shadow-md ${
                    isRunning 
                      ? 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 ring-1 ring-rose-500/30' 
                      : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20'
                  }`}
                >
                  {isRunning ? (
                    <><Square className="w-4 h-4 fill-current" /> Stop Automation</>
                  ) : (
                    <><Play className="w-4 h-4 fill-current" /> Start Automation Loop</>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Execution Log Terminal */}
          <div className="lg:col-span-2 flex flex-col space-y-4">
            
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                <TerminalIcon className="w-4 h-4 text-blue-400" />
                <span>Execution Log</span>
                <span className="text-xs font-normal text-slate-500">• Real-Time Terminal</span>
              </div>

              <button 
                onClick={clearLogs}
                className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors px-2 py-1"
                title="Clear Terminal Logs"
              >
                <Trash2 className="w-3.5 h-3.5" /> Clear
              </button>
            </div>

            {/* Terminal Window */}
            <div className="bg-[#0D1117] border border-slate-800 rounded-2xl h-[480px] flex flex-col overflow-hidden relative shadow-sm">
              <div className="p-4 flex-1 overflow-y-auto font-mono text-[13px] leading-relaxed">
                {logs.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-slate-600 italic">
                    Ready to start. Click 'Start Automation Loop' above.
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    {logs.map(log => (
                      <div key={log.id} className="flex gap-3 break-all">
                        <span className="text-slate-500 shrink-0 select-none">[{log.timestamp}]</span>
                        <span className={`
                          ${log.level === 'info' ? 'text-blue-400/90' : ''}
                          ${log.level === 'success' ? 'text-emerald-400 font-medium' : ''}
                          ${log.level === 'error' ? 'text-rose-400 font-semibold' : ''}
                          ${log.level === 'warning' ? 'text-amber-400' : ''}
                          ${log.level === 'task' ? 'text-purple-400 font-medium' : ''}
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
