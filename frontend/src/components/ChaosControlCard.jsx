import React, { useState } from 'react';
import { 
  Flame, 
  Trash2, 
  AlertTriangle, 
  Cpu, 
  CheckCircle2, 
  Clock, 
  Database, 
  ServerCrash 
} from 'lucide-react';

export function ChaosControlCard({
  deployment,
  versions = [],
  onInjectFailure,
  onClearFailure
}) {
  const canaryVersion = versions.find(v => v.version_type === 'CANARY');
  const activeFailureRate = canaryVersion ? Math.round(canaryVersion.failure_rate * 100) : 0;
  const activeErrorType = canaryVersion?.error_type || 'HTTP_500';

  const [failureRate, setFailureRate] = useState(activeFailureRate || 35);
  const [errorType, setErrorType] = useState(activeErrorType);
  const [affectedVersion, setAffectedVersion] = useState('CANARY');
  const [latencyOverride, setLatencyOverride] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const errorProfiles = [
    { id: 'HTTP_500', name: 'HTTP 500 Fault', desc: 'Unhandled application logic crash', icon: ServerCrash },
    { id: 'LATENCY_TIMEOUT', name: 'Gateway Timeout (504)', desc: 'Thread exhaustion with latency >= 2500ms', icon: Clock },
    { id: 'DATABASE_ERROR', name: 'Database Disconnect', desc: 'Connection pool starvation exception', icon: Database },
    { id: 'MEMORY_SPIKE', name: 'Memory Pressure (503)', desc: 'Container OOM / service throttling', icon: Cpu },
  ];

  const handleInject = async () => {
    setIsSubmitting(true);
    try {
      const latencyNum = latencyOverride ? parseFloat(latencyOverride) : null;
      await onInjectFailure(failureRate / 100.0, errorType, affectedVersion, latencyNum);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClear = async () => {
    setIsSubmitting(true);
    try {
      await onClearFailure();
      setFailureRate(0);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title-group">
          <Flame size={18} color="var(--color-warning)" />
          <div>
            <div className="card-title">Controlled Failure Injection & Chaos Engineering (Phase 10)</div>
            <div className="card-subtitle">
              Inject synthetic fault rates and error signatures to validate automated circuit breaker triggers
            </div>
          </div>
        </div>
        <div>
          {activeFailureRate > 0 ? (
            <span className="badge badge-rolled-back" style={{ animation: 'pulse-glow 2s infinite' }}>
              Fault Active: {activeFailureRate}% ({activeErrorType})
            </span>
          ) : (
            <span className="badge badge-running">
              No Active Faults
            </span>
          )}
        </div>
      </div>

      <div className="card-body">
        {/* Active Chaos State Alert */}
        {activeFailureRate > 0 && (
          <div className="alert-banner warning">
            <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Chaos Fault Profile Injected: {activeFailureRate}% Failure on Canary</strong>
              <div style={{ fontSize: '0.78rem', marginTop: '0.2rem' }}>
                Simulated requests dispatched to the Canary release will produce synthetic {activeErrorType} errors. 
                If Canary error rate exceeds {deployment?.rollback_threshold}%, the circuit breaker will activate.
              </div>
            </div>
          </div>
        )}

        {/* Target Fleet Selection */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <label className="form-label">Target Deployment Fleet</label>
            <select
              className="select-input"
              style={{ width: '100%', minWidth: 'unset' }}
              value={affectedVersion}
              onChange={(e) => setAffectedVersion(e.target.value)}
            >
              <option value="CANARY">Canary Fleet (v2.0.0)</option>
              <option value="STABLE">Stable Fleet (v1.0.0)</option>
            </select>
          </div>

          <div>
            <label className="form-label">Latency Override (Optional ms)</label>
            <input
              type="number"
              className="form-input"
              placeholder="e.g. 150 (Leave blank for default)"
              value={latencyOverride}
              onChange={(e) => setLatencyOverride(e.target.value)}
            />
          </div>
        </div>

        {/* Failure Rate Slider */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Injected Failure Rate:
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: failureRate > (deployment?.rollback_threshold || 10) ? 'var(--color-danger)' : 'var(--color-warning)' }}>
              {failureRate}% Errors {failureRate > (deployment?.rollback_threshold || 10) ? '(Breaches Threshold)' : '(Sub-threshold)'}
            </span>
          </div>

          <div className="slider-container">
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={failureRate}
              onChange={(e) => setFailureRate(Number(e.target.value))}
              className="range-slider"
            />
            <div className="slider-val-box" style={{ color: 'var(--color-warning-light)' }}>
              {failureRate}%
            </div>
          </div>

          {/* Quick presets */}
          <div className="preset-group">
            <button className="btn btn-sm btn-ghost" onClick={() => setFailureRate(0)}>0% Healthy</button>
            <button className="btn btn-sm btn-ghost" onClick={() => setFailureRate(5)}>5% Minor Jitter</button>
            <button className="btn btn-sm btn-ghost" onClick={() => setFailureRate(15)}>15% Breach Trigger</button>
            <button className="btn btn-sm btn-ghost" onClick={() => setFailureRate(35)}>35% Severe Fault</button>
            <button className="btn btn-sm btn-ghost" onClick={() => setFailureRate(80)}>80% Critical Crash</button>
          </div>
        </div>

        {/* Fault Profile Selector */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label className="form-label" style={{ marginBottom: '0.65rem' }}>
            Select Fault Injection Profile:
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
            {errorProfiles.map((p) => {
              const IconComp = p.icon;
              const isSelected = errorType === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => setErrorType(p.id)}
                  style={{
                    backgroundColor: isSelected ? 'var(--bg-card-hover)' : 'var(--bg-surface)',
                    border: `1px solid ${isSelected ? 'var(--color-warning)' : 'var(--border-light)'}`,
                    borderRadius: 'var(--radius-md)',
                    padding: '0.85rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: isSelected ? '0 0 10px rgba(245, 158, 11, 0.2)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <IconComp size={16} color={isSelected ? 'var(--color-warning)' : 'var(--text-secondary)'} />
                    <strong style={{ fontSize: '0.82rem', color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                      {p.name}
                    </strong>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {p.desc}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <button
            className="btn btn-ghost"
            onClick={handleClear}
            disabled={isSubmitting || activeFailureRate === 0}
          >
            <Trash2 size={15} />
            <span>Clear Active Faults</span>
          </button>

          <button
            className="btn btn-warning"
            onClick={handleInject}
            disabled={isSubmitting}
          >
            <Flame size={15} />
            <span>{isSubmitting ? 'Injecting Fault...' : `Inject ${failureRate}% ${errorType}`}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChaosControlCard;
