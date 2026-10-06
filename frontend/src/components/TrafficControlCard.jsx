import React, { useState } from 'react';
import { 
  Sliders, 
  Send, 
  Play, 
  Check, 
  AlertCircle, 
  RotateCcw,
  Zap
} from 'lucide-react';

export function TrafficControlCard({
  deployment,
  trafficConfig,
  onShiftTraffic,
  onSimulateTraffic,
  isLoadingSimulation,
  lastSimulationResult
}) {
  const currentCanaryPct = trafficConfig ? trafficConfig.canary_percentage : 0;
  const [targetCanaryPct, setTargetCanaryPct] = useState(currentCanaryPct);
  const [requestCount, setRequestCount] = useState(25);
  const [isUpdatingTraffic, setIsUpdatingTraffic] = useState(false);

  const targetStablePct = 100 - targetCanaryPct;
  const isRolledBack = deployment?.status === 'ROLLED_BACK';

  const handleApplyTraffic = async () => {
    setIsUpdatingTraffic(true);
    try {
      await onShiftTraffic(targetStablePct, targetCanaryPct);
    } finally {
      setIsUpdatingTraffic(false);
    }
  };

  const handleSetPreset = (canaryVal) => {
    setTargetCanaryPct(canaryVal);
  };

  const handleRunSimulation = () => {
    onSimulateTraffic(requestCount);
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title-group">
          <Sliders size={18} color="var(--color-stable)" />
          <div>
            <div className="card-title">Traffic Shifting & Client Simulation Engine</div>
            <div className="card-subtitle">
              Adjust weighted routing distributions and dispatch synthetic client traffic batches
            </div>
          </div>
        </div>
      </div>

      <div className="card-body">
        {/* Warning if deployment is rolled back */}
        {isRolledBack && (
          <div className="alert-banner danger">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Deployment Status: ROLLED_BACK.</strong>
              <div>
                Traffic is locked at 100% Stable. To experiment with canary traffic again, reset deployment status or provision a new deployment.
              </div>
            </div>
          </div>
        )}

        {/* Section 1: Traffic Weight Adjustment */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Target Canary Weight:
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--color-canary-light)' }}>
              {targetStablePct}% Stable / {targetCanaryPct}% Canary
            </span>
          </div>

          <div className="slider-container">
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={targetCanaryPct}
              onChange={(e) => setTargetCanaryPct(Number(e.target.value))}
              disabled={isRolledBack}
              className="range-slider"
            />
            <div className="slider-val-box">
              {targetCanaryPct}%
            </div>
          </div>

          {/* Preset Buttons */}
          <div className="preset-group">
            <button
              className="btn btn-sm btn-ghost"
              onClick={() => handleSetPreset(0)}
              disabled={isRolledBack}
            >
              100/0 Baseline
            </button>
            <button
              className="btn btn-sm btn-ghost"
              onClick={() => handleSetPreset(10)}
              disabled={isRolledBack}
            >
              90/10 Pilot (10%)
            </button>
            <button
              className="btn btn-sm btn-ghost"
              onClick={() => handleSetPreset(25)}
              disabled={isRolledBack}
            >
              75/25 Phased (25%)
            </button>
            <button
              className="btn btn-sm btn-ghost"
              onClick={() => handleSetPreset(50)}
              disabled={isRolledBack}
            >
              50/50 Balanced (50%)
            </button>
            <button
              className="btn btn-sm btn-ghost"
              onClick={() => handleSetPreset(100)}
              disabled={isRolledBack}
            >
              0/100 Full Canary
            </button>
          </div>

          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              className="btn btn-primary"
              onClick={handleApplyTraffic}
              disabled={isRolledBack || isUpdatingTraffic || targetCanaryPct === currentCanaryPct}
            >
              <Check size={16} />
              <span>{isUpdatingTraffic ? 'Applying...' : 'Apply Traffic Shift'}</span>
            </button>
          </div>
        </div>

        {/* Section 2: Simulate Client Traffic Across Active Split */}
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <Zap size={16} color="var(--color-cyan)" />
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700 }}>Dispatch Client Workload</h4>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Simulate concurrent client requests distributed according to current weighted routing rules. 
            If the observed Canary error rate exceeds the rollback threshold ({deployment?.rollback_threshold}%), the circuit breaker will trip immediately.
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {[10, 25, 50, 100].map((count) => (
                <button
                  key={count}
                  className={`btn btn-sm ${requestCount === count ? 'btn-secondary' : 'btn-ghost'}`}
                  onClick={() => setRequestCount(count)}
                >
                  {count} Reqs
                </button>
              ))}
            </div>

            <button
              className="btn btn-success"
              onClick={handleRunSimulation}
              disabled={isLoadingSimulation || deployment?.status !== 'RUNNING'}
            >
              <Play size={15} />
              <span>{isLoadingSimulation ? 'Simulating...' : `Simulate ${requestCount} Requests`}</span>
            </button>
          </div>

          {/* Last Simulation Outcome Banner */}
          {lastSimulationResult && (
            <div 
              className={`alert-banner ${lastSimulationResult.triggered_rollback ? 'danger' : 'info'}`} 
              style={{ marginTop: '1.25rem' }}
            >
              <Zap size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong>
                    {lastSimulationResult.triggered_rollback
                      ? 'Circuit Breaker Tripped! Automated Rollback Executed'
                      : 'Batch Simulation Completed Successfully'}
                  </strong>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    {lastSimulationResult.total_requests} Requests
                  </span>
                </div>
                <div style={{ marginTop: '0.4rem', fontSize: '0.78rem' }}>
                  {lastSimulationResult.triggered_rollback ? (
                    <div>{lastSimulationResult.rollback_reason}</div>
                  ) : (
                    <div>
                      Stable: {lastSimulationResult.stable_summary.total_requests} reqs (Error: {lastSimulationResult.stable_summary.error_rate}%) | 
                      Canary: {lastSimulationResult.canary_summary.total_requests} reqs (Error: {lastSimulationResult.canary_summary.error_rate}%) | 
                      Overall Error: {lastSimulationResult.overall_summary.error_rate}%
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TrafficControlCard;
