export interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  level: 'info' | 'success' | 'error' | 'warning' | 'task';
}

export interface AppConfig {
  username: string;
  password: string;
  ldplayerPath: string;
  instanceName: string;
  instanceIndex: string;
  autoMode: boolean;
  headlessMode: boolean;
}

export interface AppStats {
  accountsCreated: number;
  failedAccounts: number;
  earnings: number;
  runtimeSeconds: number;
}
