import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from './services/api';
import Navbar from './components/Navbar';
import TopologyCard from './components/TopologyCard';
import TrafficControlCard from './components/TrafficControlCard';
import ChaosControlCard from './components/ChaosControlCard';
import TelemetryPanel from './components/TelemetryPanel';
import AuditLogsPanel from './components/AuditLogsPanel';
import RollbackBanner from './components/RollbackBanner';
import CreateDeploymentModal from './components/CreateDeploymentModal';
import { 
  Network, 
  Sliders, 
  Flame, 
  Activity, 
  Terminal, 
  Play, 
  CheckCircle2, 
  AlertTriangle 
} from 'lucide-react';

export function App() {
  // Global & Connectivity State
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [authUser, setAuthUser] = useState(api.getAuthUser());
  const [notification, setNotification] = useState(null);

  // Deployments State
  const [deployments, setDeployments] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [deploymentDetail, setDeploymentDetail] = useState(null);

  // Telemetry & Logs State
  const [metrics, setMetrics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [history, setHistory] = useState([]);
  const [recentRequests, setRecentRequests] = useState([]);

  // UI Flow State
  const [activeTab, setActiveTab] = useState('topology');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isLoadingSimulation, setIsLoadingSimulation] = useState(false);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [lastSimulationResult, setLastSimulationResult] = useState(null);

  const isMounted = useRef(true);

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => {
      setNotification(null);
    }, 4500);
  };

  // Helper to ensure authentication
  const ensureAuth = useCallback(async () => {
    let user = api.getAuthUser();
    if (!user) {
      try {
        await api.loginDefaultAdmin();
        user = api.getAuthUser();
        setAuthUser(user);
      } catch (err) {
        console.error('Auto-login failed:', err);
      }
    }
    return user;
  }, []);

  // Check Backend Liveness
  const checkHealth = useCallback(async () => {
    try {
      await api.getHealth();
      setIsBackendOnline(true);
    } catch {
      setIsBackendOnline(false);
    }
  }, []);

  // Fetch Deployments List
  const loadDeployments = useCallback(async () => {
    try {
      await ensureAuth();
      const list = await api.getDeployments();
      setDeployments(list);

      // Auto-select first deployment or seed if none exist
      if (list.length > 0) {
        if (!selectedId || !list.some(d => d.id === selectedId)) {
          setSelectedId(list[0].id);
        }
      } else {
        // Seed initial academic demo deployment
        const seeded = await api.createDeployment({
          name: 'Payment Processing Microservice',
          description: 'Production canary release evaluating checkout engine v2',
          rollback_threshold: 10.0,
          evaluation_window_seconds: 60,
          stable_tag: 'v1.0.0',
          canary_tag: 'v2.0.0',
          stable_latency_ms: 30.0,
          canary_latency_ms: 35.0,
          initial_canary_failure_rate: 0.0,
        });
        await api.startDeployment(seeded.id);
        const updatedList = await api.getDeployments();
        setDeployments(updatedList);
        setSelectedId(seeded.id);
      }
    } catch (err) {
      console.error('Failed to load deployments:', err);
    }
  }, [ensureAuth, selectedId]);

  // Fetch Telemetry & Logs for Selected Deployment
  const loadDeploymentData = useCallback(async (depId) => {
    if (!depId) return;
    try {
      const [detail, met, lg, hist] = await Promise.all([
        api.getDeployment(depId),
        api.getMetrics(depId).catch(() => null),
        api.getLogs(depId, null, null, 40).catch(() => []),
        api.getHistory(depId).catch(() => []),
      ]);
      setDeploymentDetail(detail);
      setMetrics(met);
      setLogs(lg);
      setHistory(hist);
    } catch (err) {
      console.error('Failed to load deployment data:', err);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    isMounted.current = true;
    checkHealth();
    loadDeployments();
    return () => { isMounted.current = false; };
  }, [checkHealth, loadDeployments]);

  // Load telemetry when selected ID changes
  useEffect(() => {
    if (selectedId) {
      loadDeploymentData(selectedId);
    }
  }, [selectedId, loadDeploymentData]);

  // Polling Interval
  useEffect(() => {
    if (!autoRefresh || !selectedId) return;
    const interval = setInterval(() => {
      checkHealth();
      loadDeploymentData(selectedId);
    }, 3500);
    return () => clearInterval(interval);
  }, [autoRefresh, selectedId, checkHealth, loadDeploymentData]);

  // Action: Shift Traffic
  const handleShiftTraffic = async (stablePct, canaryPct) => {
    try {
      await api.shiftTraffic(selectedId, stablePct, canaryPct);
      showNotification(`Traffic weights updated to ${stablePct}% Stable / ${canaryPct}% Canary`, 'success');
      loadDeploymentData(selectedId);
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Failed to shift traffic', 'danger');
    }
  };

  // Action: Simulate Routed Client Traffic
  const handleSimulateTraffic = async (count) => {
    setIsLoadingSimulation(true);
    try {
      const res = await api.simulateRoutedTraffic(selectedId, count);
      setLastSimulationResult(res);
      setRecentRequests(res.results || []);

      if (res.triggered_rollback) {
        showNotification(`CIRCUIT BREAKER TRIGGERED: ${res.rollback_reason}`, 'danger');
        setActiveTab('telemetry');
      } else {
        showNotification(`Dispatched ${count} requests across weighted target groups`, 'info');
      }
      loadDeploymentData(selectedId);
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Simulation error', 'danger');
    } finally {
      setIsLoadingSimulation(false);
    }
  };

  // Action: Controlled Failure Injection (Phase 10)
  const handleInjectFailure = async (rate, errType, targetVersion, latencyMs) => {
    try {
      const res = await api.injectFailure(selectedId, rate, errType, targetVersion, latencyMs);
      showNotification(res.message, 'warning');
      loadDeploymentData(selectedId);
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Failure injection rejected', 'danger');
    }
  };

  // Action: Clear Failure Injection
  const handleClearFailure = async () => {
    try {
      const res = await api.clearFailure(selectedId);
      showNotification(res.message, 'info');
      loadDeploymentData(selectedId);
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Failed to clear failure', 'danger');
    }
  };

  // Action: Manual Emergency Rollback (Phase 9)
  const handleManualRollback = async (reason) => {
    setIsRollingBack(true);
    try {
      const res = await api.manualRollback(selectedId, reason);
      showNotification(`Manual Rollback Executed: Traffic reverted to 100% Stable (v1)`, 'danger');
      loadDeploymentData(selectedId);
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Rollback rejected', 'danger');
    } finally {
      setIsRollingBack(false);
    }
  };

  // Action: Start Deployment
  const handleStartDeployment = async () => {
    try {
      await api.startDeployment(selectedId);
      showNotification('Deployment lifecycle started. Status is now RUNNING.', 'success');
      loadDeployments();
      loadDeploymentData(selectedId);
    } catch (err) {
      showNotification(err.response?.data?.detail || 'Failed to start deployment', 'danger');
    }
  };

  // Action: Create Deployment
  const handleCreateDeployment = async (formData) => {
    const res = await api.createDeployment(formData);
    showNotification(`Deployment "${res.name}" provisioned. Starting rollout...`, 'success');
    await api.startDeployment(res.id);
    await loadDeployments();
    setSelectedId(res.id);
  };

  // Action: Quick Login
  const handleQuickLogin = async () => {
    try {
      await api.loginDefaultAdmin();
      const user = api.getAuthUser();
      setAuthUser(user);
      showNotification('Authenticated as System Administrator (admin@canary.local)', 'success');
      loadDeployments();
    } catch (err) {
      showNotification('Login failed', 'danger');
    }
  };

  const handleLogout = () => {
    api.logout();
    setAuthUser(null);
    showNotification('Logged out successfully', 'info');
  };

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <Navbar
        deployments={deployments}
        selectedDeploymentId={selectedId}
        onSelectDeployment={setSelectedId}
        onOpenCreateModal={() => setIsCreateModalOpen(true)}
        isBackendOnline={isBackendOnline}
        autoRefresh={autoRefresh}
        onToggleAutoRefresh={() => setAutoRefresh(!autoRefresh)}
        authUser={authUser}
        onQuickLogin={handleQuickLogin}
        onLogout={handleLogout}
      />

      <main className="main-content">
        {/* Floating Notification Toast */}
        {notification && (
          <div className={`alert-banner ${notification.type}`} style={{ animation: 'modal-enter 0.2s ease-out' }}>
            <div style={{ fontWeight: 600 }}>{notification.message}</div>
          </div>
        )}

        {/* Deployment Header & Controls Strip */}
        <div className="dashboard-header">
          <div className="deployment-select-wrapper">
            <span className="deployment-select-label">Active Deployment:</span>
            <select
              className="select-input"
              value={selectedId || ''}
              onChange={(e) => setSelectedId(Number(e.target.value))}
            >
              {deployments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} [{d.status}] - Threshold: {d.rollback_threshold}%
                </option>
              ))}
            </select>

            {deploymentDetail?.status === 'PENDING' && (
              <button className="btn btn-sm btn-success" onClick={handleStartDeployment}>
                <Play size={14} />
                <span>Start Deployment</span>
              </button>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {deploymentDetail && (
              <span className={`badge badge-${deploymentDetail.status.toLowerCase().replace('_', '-')}`}>
                {deploymentDetail.status}
              </span>
            )}
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Safety Threshold: {deploymentDetail?.rollback_threshold || 10.0}%
            </span>
          </div>
        </div>

        {/* Circuit Breaker Status Banner */}
        <RollbackBanner
          deployment={deploymentDetail}
          onManualRollback={handleManualRollback}
          isRollingBack={isRollingBack}
        />

        {/* Tabbed Navigation */}
        <div className="tabs-nav">
          <button
            className={`tab-btn ${activeTab === 'topology' ? 'active' : ''}`}
            onClick={() => setActiveTab('topology')}
          >
            <Network size={16} />
            <span>Architecture & Topology</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'traffic' ? 'active' : ''}`}
            onClick={() => setActiveTab('traffic')}
          >
            <Sliders size={16} />
            <span>Traffic Shifting & Simulator</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'chaos' ? 'active' : ''}`}
            onClick={() => setActiveTab('chaos')}
          >
            <Flame size={16} />
            <span>Chaos & Failure Injection</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'telemetry' ? 'active' : ''}`}
            onClick={() => setActiveTab('telemetry')}
          >
            <Activity size={16} />
            <span>Metrics & Packet Traces</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            <Terminal size={16} />
            <span>Audit Trail & Logs</span>
          </button>
        </div>

        {/* Active Tab Panel */}
        {activeTab === 'topology' && (
          <TopologyCard
            deployment={deploymentDetail}
            trafficConfig={deploymentDetail?.traffic_config}
            versions={deploymentDetail?.versions}
          />
        )}

        {activeTab === 'traffic' && (
          <TrafficControlCard
            deployment={deploymentDetail}
            trafficConfig={deploymentDetail?.traffic_config}
            onShiftTraffic={handleShiftTraffic}
            onSimulateTraffic={handleSimulateTraffic}
            isLoadingSimulation={isLoadingSimulation}
            lastSimulationResult={lastSimulationResult}
          />
        )}

        {activeTab === 'chaos' && (
          <ChaosControlCard
            deployment={deploymentDetail}
            versions={deploymentDetail?.versions}
            onInjectFailure={handleInjectFailure}
            onClearFailure={handleClearFailure}
          />
        )}

        {activeTab === 'telemetry' && (
          <TelemetryPanel
            deployment={deploymentDetail}
            metrics={metrics}
            recentRequests={recentRequests}
          />
        )}

        {activeTab === 'logs' && (
          <AuditLogsPanel
            history={history}
            logs={logs}
            onRefresh={() => loadDeploymentData(selectedId)}
          />
        )}
      </main>

      {/* Provision Deployment Modal */}
      <CreateDeploymentModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreateDeployment={handleCreateDeployment}
      />
    </div>
  );
}

export default App;
