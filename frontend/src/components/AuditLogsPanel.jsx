import React, { useState } from 'react';
import { 
  FileText, 
  History, 
  Filter, 
  Terminal, 
  ShieldAlert, 
  CheckCircle2, 
  Clock 
} from 'lucide-react';

export function AuditLogsPanel({
  history = [],
  logs = [],
  onRefresh
}) {
  const [activeSubTab, setActiveSubTab] = useState('history');
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [levelFilter, setLevelFilter] = useState('ALL');

  const filteredLogs = logs.filter((log) => {
    if (sourceFilter !== 'ALL' && log.source !== sourceFilter) return false;
    if (levelFilter !== 'ALL' && log.level !== levelFilter) return false;
    return true;
  });

  const getEventBadge = (type) => {
    switch (type) {
      case 'AUTO_ROLLBACK':
        return <span className="badge badge-rolled-back">AUTO_ROLLBACK</span>;
      case 'MANUAL_ROLLBACK':
        return <span className="badge badge-rolled-back">MANUAL_ROLLBACK</span>;
      case 'FAILURE_INJECTED':
        return <span className="badge" style={{ backgroundColor: 'var(--color-warning-bg)', color: 'var(--color-warning-light)', border: '1px solid var(--color-warning)' }}>FAILURE_INJECTED</span>;
      case 'TRAFFIC_SHIFT':
        return <span className="badge badge-stable">TRAFFIC_SHIFT</span>;
      default:
        return <span className="badge badge-running">{type}</span>;
    }
  };

  const getLogLevelBadge = (level) => {
    switch (level) {
      case 'CRITICAL':
        return <span className="badge badge-rolled-back">CRITICAL</span>;
      case 'ERROR':
        return <span className="badge badge-danger">ERROR</span>;
      case 'WARNING':
        return <span className="badge badge-pending">WARNING</span>;
      default:
        return <span className="badge badge-running">INFO</span>;
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title-group">
          <Terminal size={18} color="var(--color-cyan)" />
          <div>
            <div className="card-title">Audit Trail & Observability Logs</div>
            <div className="card-subtitle">
              Persistent event provenance and diagnostic logs for academic verification
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className={`btn btn-sm ${activeSubTab === 'history' ? 'btn-secondary' : 'btn-ghost'}`}
            onClick={() => setActiveSubTab('history')}
          >
            <History size={14} />
            <span>Audit Trail ({history.length})</span>
          </button>
          <button
            className={`btn btn-sm ${activeSubTab === 'logs' ? 'btn-secondary' : 'btn-ghost'}`}
            onClick={() => setActiveSubTab('logs')}
          >
            <FileText size={14} />
            <span>Application Logs ({logs.length})</span>
          </button>
        </div>
      </div>

      <div className="card-body" style={{ padding: 0 }}>
        {activeSubTab === 'history' ? (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '180px' }}>Timestamp</th>
                  <th style={{ width: '160px' }}>Event Type</th>
                  <th>Audit Message</th>
                  <th>Diagnostic Details</th>
                </tr>
              </thead>
              <tbody>
                {history.length > 0 ? (
                  history.map((event) => (
                    <tr key={event.id}>
                      <td className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                        {new Date(event.timestamp).toLocaleString()}
                      </td>
                      <td>{getEventBadge(event.event_type)}</td>
                      <td style={{ fontWeight: 500 }}>{event.message}</td>
                      <td className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', maxWidth: '300px', wordBreak: 'break-all' }}>
                        {event.details || '-'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                      No lifecycle audit events recorded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div>
            {/* Filter Bar */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '1rem', 
              padding: '0.75rem 1.25rem', 
              borderBottom: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-surface)' 
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem' }}>
                <Filter size={14} color="var(--text-muted)" />
                <span style={{ color: 'var(--text-secondary)' }}>Source:</span>
                <select 
                  className="select-input" 
                  style={{ minWidth: '120px', padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                >
                  <option value="ALL">All Sources</option>
                  <option value="ROUTER">ROUTER</option>
                  <option value="CIRCUIT_BREAKER">CIRCUIT_BREAKER</option>
                  <option value="CHAOS_ENGINE">CHAOS_ENGINE</option>
                  <option value="SIMULATOR">SIMULATOR</option>
                </select>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Level:</span>
                <select 
                  className="select-input" 
                  style={{ minWidth: '110px', padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                  value={levelFilter}
                  onChange={(e) => setLevelFilter(e.target.value)}
                >
                  <option value="ALL">All Levels</option>
                  <option value="INFO">INFO</option>
                  <option value="WARNING">WARNING</option>
                  <option value="ERROR">ERROR</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>

              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                Showing {filteredLogs.length} of {logs.length} entries
              </span>
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: '180px' }}>Timestamp</th>
                    <th style={{ width: '110px' }}>Level</th>
                    <th style={{ width: '140px' }}>Source</th>
                    <th>Log Message</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.length > 0 ? (
                    filteredLogs.map((log) => (
                      <tr key={log.id}>
                        <td className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td>{getLogLevelBadge(log.level)}</td>
                        <td className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--color-cyan-light)' }}>
                          {log.source}
                        </td>
                        <td style={{ fontSize: '0.78rem' }}>{log.message}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                        No diagnostic log entries match the selected filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AuditLogsPanel;
