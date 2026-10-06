import React from 'react';
import { 
  Network, 
  ArrowRight, 
  Server, 
  ShieldAlert, 
  Cpu, 
  CheckCircle, 
  AlertTriangle,
  GitBranch
} from 'lucide-react';

export function TopologyCard({ deployment, trafficConfig, versions = [] }) {
  if (!deployment) return null;

  const stableVersion = versions.find(v => v.version_type === 'STABLE') || {
    version_tag: 'v1.0.0',
    simulated_latency_ms: 30,
    failure_rate: 0,
    is_active: true
  };

  const canaryVersion = versions.find(v => v.version_type === 'CANARY') || {
    version_tag: 'v2.0.0',
    simulated_latency_ms: 35,
    failure_rate: 0,
    error_type: 'HTTP_500',
    is_active: true
  };

  const stablePct = trafficConfig ? trafficConfig.stable_percentage : 100;
  const canaryPct = trafficConfig ? trafficConfig.canary_percentage : 0;
  const isRolledBack = deployment.status === 'ROLLED_BACK';

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title-group">
          <Network size={18} color="var(--color-cyan)" />
          <div>
            <div className="card-title">Cloud Deployment Topology & Routing Mesh</div>
            <div className="card-subtitle">
              Emulates AWS ALB weighted target groups routing between Stable (v1) and Canary (v2) fleets
            </div>
          </div>
        </div>
        <div>
          <span className={`badge badge-${deployment.status.toLowerCase().replace('_', '-')}`}>
            Status: {deployment.status}
          </span>
        </div>
      </div>

      <div className="card-body">
        <div className="topology-grid">
          {/* Ingress Gateway / ALB */}
          <div className="topology-node node-ingress">
            <div className="topology-node-title">
              <Network size={16} color="var(--color-cyan)" />
              <span>Application Load Balancer (ALB)</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Weighted Target Group Ingress
            </p>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
              <span className="badge badge-stable">{stablePct}% Stable</span>
              <span className="badge badge-canary">{canaryPct}% Canary</span>
            </div>
          </div>

          {/* Router Interconnect Arrow */}
          <div className="topology-arrow">
            <GitBranch size={24} />
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Weighted Split</span>
          </div>

          {/* Target Group Replicas */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Stable Version Node */}
            <div className="topology-node node-stable">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="topology-node-title">
                  <Server size={16} color="var(--color-stable)" />
                  <span>Stable Fleet ({stableVersion.version_tag})</span>
                </div>
                <span className="badge badge-stable">Traffic: {stablePct}%</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', fontSize: '0.72rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Latency: </span>
                  <strong style={{ fontFamily: 'var(--font-mono)' }}>{stableVersion.simulated_latency_ms}ms</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Fault Rate: </span>
                  <strong style={{ fontFamily: 'var(--font-mono)' }}>{(stableVersion.failure_rate * 100).toFixed(0)}%</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Target Group: </span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>tg-stable</span>
                </div>
              </div>
            </div>

            {/* Canary Version Node */}
            <div className="topology-node node-canary" style={{ borderColor: isRolledBack ? 'var(--color-danger)' : undefined }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="topology-node-title">
                  <Cpu size={16} color="var(--color-canary)" />
                  <span>Canary Fleet ({canaryVersion.version_tag})</span>
                </div>
                <span className="badge badge-canary">Traffic: {canaryPct}%</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', fontSize: '0.72rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Latency: </span>
                  <strong style={{ fontFamily: 'var(--font-mono)' }}>{canaryVersion.simulated_latency_ms}ms</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Injected Faults: </span>
                  <strong style={{ 
                    fontFamily: 'var(--font-mono)', 
                    color: canaryVersion.failure_rate > 0 ? 'var(--color-warning)' : 'var(--color-canary-light)' 
                  }}>
                    {(canaryVersion.failure_rate * 100).toFixed(0)}%
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Fault Profile: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-cyan-light)' }}>
                    {canaryVersion.error_type || 'HTTP_500'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Traffic Distribution Bar */}
        <div className="traffic-balance-wrapper">
          <div className="traffic-bar-labels">
            <span style={{ color: 'var(--color-stable-light)' }}>Stable Fleet ({stablePct}%)</span>
            <span style={{ color: 'var(--color-canary-light)' }}>Canary Fleet ({canaryPct}%)</span>
          </div>
          <div className="traffic-bar">
            <div className="traffic-segment-stable" style={{ width: `${stablePct}%` }}>
              {stablePct > 10 ? `${stablePct}% Stable` : ''}
            </div>
            <div className="traffic-segment-canary" style={{ width: `${canaryPct}%` }}>
              {canaryPct > 10 ? `${canaryPct}% Canary` : ''}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TopologyCard;
