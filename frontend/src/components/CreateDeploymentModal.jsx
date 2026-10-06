import React, { useState } from 'react';
import { X, Plus, Server, Layers } from 'lucide-react';

export function CreateDeploymentModal({
  isOpen,
  onClose,
  onCreateDeployment
}) {
  const [formData, setFormData] = useState({
    name: 'Payment Gateway Microservice',
    description: 'Canary rollout of optimized checkout engine v2',
    rollback_threshold: 10.0,
    evaluation_window_seconds: 60,
    stable_tag: 'v1.0.0',
    canary_tag: 'v2.0.0',
    stable_latency_ms: 30.0,
    canary_latency_ms: 35.0,
    initial_canary_failure_rate: 0.0,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg('');
    try {
      await onCreateDeployment(formData);
      onClose();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to create deployment');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={18} color="var(--color-cyan)" />
            <strong style={{ fontSize: '1rem' }}>Provision Canary Deployment</strong>
          </div>
          <button className="btn btn-sm btn-ghost" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {errorMsg && (
              <div className="alert-banner danger" style={{ marginBottom: '1rem' }}>
                {errorMsg}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Deployment Name *</label>
              <input
                type="text"
                className="form-input"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Auth Microservice"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description</label>
              <input
                type="text"
                className="form-input"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="e.g. Testing new payment integration"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Rollback Threshold (%) *</label>
                <input
                  type="number"
                  step="0.5"
                  min="1"
                  max="100"
                  className="form-input font-mono"
                  required
                  value={formData.rollback_threshold}
                  onChange={(e) => setFormData({ ...formData, rollback_threshold: parseFloat(e.target.value) })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Evaluation Window (s) *</label>
                <input
                  type="number"
                  min="10"
                  max="3600"
                  className="form-input font-mono"
                  required
                  value={formData.evaluation_window_seconds}
                  onChange={(e) => setFormData({ ...formData, evaluation_window_seconds: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Stable Version Tag</label>
                <input
                  type="text"
                  className="form-input font-mono"
                  required
                  value={formData.stable_tag}
                  onChange={(e) => setFormData({ ...formData, stable_tag: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Canary Version Tag</label>
                <input
                  type="text"
                  className="form-input font-mono"
                  required
                  value={formData.canary_tag}
                  onChange={(e) => setFormData({ ...formData, canary_tag: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Stable Latency (ms)</label>
                <input
                  type="number"
                  step="1"
                  className="form-input font-mono"
                  value={formData.stable_latency_ms}
                  onChange={(e) => setFormData({ ...formData, stable_latency_ms: parseFloat(e.target.value) })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Canary Latency (ms)</label>
                <input
                  type="number"
                  step="1"
                  className="form-input font-mono"
                  value={formData.canary_latency_ms}
                  onChange={(e) => setFormData({ ...formData, canary_latency_ms: parseFloat(e.target.value) })}
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              <Plus size={16} />
              <span>{isSubmitting ? 'Creating...' : 'Provision Deployment'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateDeploymentModal;
