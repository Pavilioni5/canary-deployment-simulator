import React from 'react';
import { 
  BarChart3, 
  Activity, 
  CheckCircle, 
  AlertOctagon, 
  Clock, 
  ShieldCheck, 
  ShieldAlert,
  Hash
} from 'lucide-react';

export function TelemetryPanel({
  deployment,
  metrics,
  recentRequests = []
}) {
  const canarySummary = metrics?.canary_metrics || {
    total_requests: 0,
    successful_requests: 0,
    failed_requests: 0,
    error_rate: 0.0,
    avg_latency_ms: 0.0
  };

  const stableSummary = metrics?.stable_metrics || {
    total_requests: 0,
    successful_requests: 0,
    failed_requests: 0,
    error_rate: 0.0,
    avg_latency_ms: 0.0
  };

  const overall = metrics?.overall_metrics || {
    total_requests: 0,
    successful_requests: 0,
    failed_requests: 0,
    error_rate: 0.0,
    avg_latency_ms: 0.0
  };

  const threshold = deployment?.rollback_threshold || 10.0;
  const isBreached = canarySummary.error_rate > threshold;
  const isRolledBack = deployment?.status === 'ROLLED_BACK';

  return (
    <div>
      {/* KPI Stats Grid */}
      <div className="stat-grid">
        {/* Total Client Traffic */}
        <div className="stat-card cyan">
          <div className="stat-header">
            <span className="stat-label">Total Traffic</span>
            <Activity size={18} className="stat-icon" />
          </div>
          <div className="stat-value">{overall.total_requests.toLocaleString()}</div>
          <div className="stat-meta">
            {overall.successful_requests} successful / {overall.failed_requests} failed
          </div>
        </div>

        {/* Canary Error Rate vs Threshold */}
        <div className={`stat-card ${isBreached || isRolledBack ? 'danger' : 'canary'}`}>
          <div className="stat-header">
            <span className="stat-label">Canary Error Rate</span>
            {isBreached ? <ShieldAlert size={18} color="var(--color-danger)" /> : <ShieldCheck size={18} color="var(--color-canary)" />}
          </div>
          <div className="stat-value" style={{ color: isBreached ? 'var(--color-danger-light)' : 'var(--color-canary-light)' }}>
            {canarySummary.error_rate.toFixed(1)}%
          </div>
          <div className="stat-meta">
            Threshold: {threshold.toFixed(1)}% ({canarySummary.failed_requests} / {canarySummary.total_requests} failed)
          </div>
        </div>

        {/* Stable Error Rate */}
        <div className="stat-card stable">
          <div className="stat-header">
            <span className="stat-label">Stable Error Rate</span>
            <CheckCircle size={18} className="stat-icon" />
          </div>
          <div className="stat-value" style={{ color: 'var(--color-stable-light)' }}>
            {stableSummary.error_rate.toFixed(1)}%
          </div>
          <div className="stat-meta">
            {stableSummary.successful_requests} successful / {stableSummary.failed_requests} failed
          </div>
        </div>

        {/* Mean Latency */}
        <div className="stat-card warning">
          <div className="stat-header">
            <span className="stat-label">Mean Latency</span>
            <Clock size={18} className="stat-icon" />
          </div>
          <div className="stat-value">
            {overall.avg_latency_ms.toFixed(1)}ms
          </div>
          <div className="stat-meta">
            Stable: {stableSummary.avg_latency_ms.toFixed(1)}ms | Canary: {canarySummary.avg_latency_ms.toFixed(1)}ms
          </div>
        </div>
      </div>

      {/* Threshold Monitor Progress Bar */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <BarChart3 size={18} color="var(--color-cyan)" />
            <div>
              <div className="card-title">Circuit Breaker Error Rate Threshold Monitor</div>
              <div className="card-subtitle">
                Automatic rollback is initiated when Canary error rate exceeds {threshold}%
              </div>
            </div>
          </div>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.8rem' }}>
            <span>Canary Error Rate: <strong>{canarySummary.error_rate.toFixed(2)}%</strong></span>
            <span>Safety Limit: <strong>{threshold}%</strong></span>
          </div>
          <div style={{ 
            height: '14px', 
            backgroundColor: 'var(--bg-surface)', 
            borderRadius: 'var(--radius-sm)', 
            overflow: 'hidden', 
            position: 'relative',
            border: '1px solid var(--border-light)'
          }}>
            {/* Safe threshold marker */}
            <div style={{
              position: 'absolute',
              left: `${Math.min(100, threshold)}%`,
              top: 0,
              bottom: 0,
              width: '2px',
              backgroundColor: 'var(--color-danger)',
              zIndex: 2,
            }} title={`Threshold: ${threshold}%`} />

            {/* Error rate fill */}
            <div style={{
              height: '100%',
              width: `${Math.min(100, (canarySummary.error_rate / Math.max(1, threshold * 2)) * 100)}%`,
              backgroundColor: isBreached ? 'var(--color-danger)' : (canarySummary.error_rate > 0 ? 'var(--color-warning)' : 'var(--color-canary)'),
              transition: 'width 0.4s ease',
            }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            <span>0%</span>
            <span>Threshold ({threshold}%)</span>
            <span>{threshold * 2}%+</span>
          </div>
        </div>
      </div>

      {/* Recent Request Stream Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <Activity size={18} color="var(--color-stable)" />
            <div>
              <div className="card-title">Live Request Stream & Telemetry Trace</div>
              <div className="card-subtitle">
                Inspect synthetic client requests passing through the Application Load Balancer
              </div>
            </div>
          </div>
          <span className="badge badge-stable">
            {recentRequests.length} Packets Captured
          </span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Request ID</th>
                  <th>Target Fleet</th>
                  <th>Version</th>
                  <th>HTTP Status</th>
                  <th>Latency</th>
                  <th>AWS Trace ID / Error Details</th>
                </tr>
              </thead>
              <tbody>
                {recentRequests.length > 0 ? (
                  recentRequests.slice(0, 15).map((req, idx) => (
                    <tr key={req.request_id || idx}>
                      <td className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {req.request_id}
                      </td>
                      <td>
                        <span className={`badge ${req.version_type === 'CANARY' ? 'badge-canary' : 'badge-stable'}`}>
                          {req.version_type}
                        </span>
                      </td>
                      <td className="font-mono">{req.version_tag}</td>
                      <td>
                        <span style={{ 
                          fontWeight: 700, 
                          fontFamily: 'var(--font-mono)',
                          color: req.status_code === 200 ? 'var(--color-canary-light)' : 'var(--color-danger-light)'
                        }}>
                          {req.status_code} {req.status === 'SUCCESS' ? 'OK' : 'FAIL'}
                        </span>
                      </td>
                      <td className="font-mono">{req.latency_ms}ms</td>
                      <td style={{ fontSize: '0.75rem', color: req.error_message ? 'var(--color-danger-light)' : 'var(--text-muted)' }}>
                        {req.error_message || req.headers?.['X-Amzn-Trace-Id'] || 'Healthy execution'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                      No simulated requests dispatched yet. Use the "Traffic Shifting" tab to send a traffic batch.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TelemetryPanel;
