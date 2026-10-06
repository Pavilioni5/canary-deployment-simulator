import React from 'react';
import { ShieldAlert, AlertTriangle, RotateCcw, Power } from 'lucide-react';

export function RollbackBanner({
  deployment,
  onManualRollback,
  isRollingBack
}) {
  if (!deployment) return null;

  const isRolledBack = deployment.status === 'ROLLED_BACK';

  if (isRolledBack) {
    return (
      <div className="alert-banner danger" style={{ animation: 'pulse-glow 3s infinite' }}>
        <ShieldAlert size={22} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: '0.92rem' }}>
              CIRCUIT BREAKER ACTIVATED: Automatic Rollback Executed
            </strong>
            <span className="badge badge-rolled-back">
              STATUS: ROLLED_BACK
            </span>
          </div>
          <p style={{ marginTop: '0.35rem', fontSize: '0.8rem' }}>
            Traffic has been automatically and instantaneously diverted to <strong>100% Stable (v1.0.0) / 0% Canary</strong>. 
            Canary telemetry exceeded the configured safety threshold of <strong>{deployment.rollback_threshold}%</strong>. 
            All in-flight and future requests are protected from canary anomalies.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
      <button
        className="btn btn-sm btn-danger"
        onClick={() => {
          if (window.confirm('Are you sure you want to trigger an immediate emergency rollback to 100% Stable?')) {
            onManualRollback('Operator executed emergency circuit breaker rollback');
          }
        }}
        disabled={isRollingBack || deployment.status !== 'RUNNING'}
        title="Instantly revert all traffic to 100% Stable"
      >
        <RotateCcw size={14} />
        <span>{isRollingBack ? 'Reverting Traffic...' : 'Manual Emergency Rollback'}</span>
      </button>
    </div>
  );
}

export default RollbackBanner;
