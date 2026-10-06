import React from 'react';
import { 
  Cloud, 
  Activity, 
  Plus, 
  RotateCw, 
  ShieldCheck, 
  UserCheck, 
  LogOut, 
  Server 
} from 'lucide-react';

export function Navbar({
  deployments = [],
  selectedDeploymentId,
  onSelectDeployment,
  onOpenCreateModal,
  isBackendOnline,
  autoRefresh,
  onToggleAutoRefresh,
  authUser,
  onQuickLogin,
  onLogout,
}) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Brand Identity */}
        <div className="brand-section">
          <div className="brand-icon">
            <Cloud size={20} />
          </div>
          <div className="brand-info">
            <div className="brand-title">
              Canary Deployment Simulator
              <span className="brand-badge">P71</span>
            </div>
            <div className="brand-subtitle">
              Cloud-Based Traffic Routing & Automated Rollback
            </div>
          </div>
        </div>

        {/* Navigation Actions */}
        <div className="nav-actions">
          {/* Backend Status Probe */}
          <div className="status-pill" title={isBackendOnline ? 'FastAPI Backend Online' : 'Backend Unreachable'}>
            <span className={`status-dot ${isBackendOnline ? 'online pulse' : 'offline'}`} />
            <span>{isBackendOnline ? 'API Connected' : 'API Offline'}</span>
          </div>

          {/* Auto Refresh Toggle */}
          <button
            className={`btn btn-sm ${autoRefresh ? 'btn-secondary' : 'btn-ghost'}`}
            onClick={onToggleAutoRefresh}
            title="Auto-refresh metrics every 3 seconds"
          >
            <RotateCw size={14} className={autoRefresh ? 'spin-icon' : ''} />
            <span>{autoRefresh ? 'Live Polling' : 'Auto-Refresh Off'}</span>
          </button>

          {/* New Deployment Button */}
          <button className="btn btn-sm btn-primary" onClick={onOpenCreateModal}>
            <Plus size={14} />
            <span>New Deployment</span>
          </button>

          {/* Authentication State */}
          {authUser ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div className="status-pill" style={{ borderColor: 'var(--color-stable)' }}>
                <UserCheck size={14} color="var(--color-stable-light)" />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                  {authUser.email} ({authUser.role})
                </span>
              </div>
              <button 
                className="btn btn-sm btn-ghost" 
                onClick={onLogout}
                title="Log out"
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <button className="btn btn-sm btn-warning" onClick={onQuickLogin}>
              <ShieldCheck size={14} />
              <span>Admin Quick-Login</span>
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
