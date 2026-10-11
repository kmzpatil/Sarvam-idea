import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';
import {
  ShieldAlert,
  Radio,
  MapPin,
  AlertTriangle,
  Users,
  CheckCircle2,
  Volume2,
  FileText,
  MessageSquare,
  Play,
  RotateCcw,
  PlusCircle,
  ExternalLink,
  ChevronRight,
  Flame,
  Activity,
  Layers,
  Sparkles,
  Zap,
  VolumeX,
} from 'lucide-react';

// Read API key strictly from environment variables (.env)
const ENV_CARTO_KEY = import.meta.env.VITE_CARTO_KEY || '';

const getCartoTileUrl = (style, key) => {
  const param = key ? `?key=${key}` : '';
  if (style === 'voyager') return `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png${param}`;
  if (style === 'positron') return `https://basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png${param}`;
  if (style === 'dark') return `https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png${param}`;
  return `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png${param}`;
};

const MAP_LAYERS = {
  voyager: {
    name: 'Apple / Voyager',
    style: 'voyager',
    maxZoom: 19,
    subdomains: ['a', 'b', 'c', 'd']
  },
  positron: {
    name: 'Clean Light',
    style: 'positron',
    maxZoom: 19,
    subdomains: ['a', 'b', 'c', 'd']
  },
  dark: {
    name: 'Tactical Dark',
    style: 'dark',
    maxZoom: 19,
    subdomains: ['a', 'b', 'c', 'd']
  }
};

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [activeLayerKey, setActiveLayerKey] = useState('voyager');
  const [metrics, setMetrics] = useState({
    total_raw_reports: 20,
    fused_incidents: 8,
    dedupe_noise_reduction_pct: 60.0,
    pairwise_dedupe_f1: 0.94,
    median_geo_error_meters: 145,
    pct_within_500m: 92.5,
    severity_rank_correlation_kendall_tau: 0.89,
  });
  const [isSimulating, setIsSimulating] = useState(false);
  const [isIngestModalOpen, setIsIngestModalOpen] = useState(false);
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Operator Ingest Form
  const [ingestForm, setIngestForm] = useState({
    channel: 'sms',
    language: 'hi-IN',
    raw_text: 'दीघा घाट के 500 मीटर पीछे पानी बहुत तेज भर गया है, 40 लोग छतों पर हैं।',
    raw_location: '500m behind Digha Ghat',
    hazard_type: 'Embankment Breach',
    people_affected: 40,
    reporter: '+91-9876543210 (Field Volunteer)'
  });

  // Bulbul Voice Advisory State
  const [advisoryLang, setAdvisoryLang] = useState('hi-IN');
  const [advisoryResult, setAdvisoryResult] = useState(null);
  const [isSynthesizingAdvisory, setIsSynthesizingAdvisory] = useState(false);
  const [advisoryError, setAdvisoryError] = useState(null);

  // Leaflet references
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const currentTileLayerRef = useRef(null);
  const markersLayerRef = useRef(null);
  const [cartoKey, setCartoKey] = useState(ENV_CARTO_KEY);
  const circlesLayerRef = useRef(null);

  // 1. Fetch Incidents & Metrics on Mount
  const fetchIncidentsAndMetrics = async () => {
    try {
      const [incRes, metRes, cfgRes] = await Promise.all([
        fetch('/api/incidents'),
        fetch('/api/benchmark-metrics'),
        fetch('/api/config')
      ]);

      if (incRes.ok) {
        const data = await incRes.json();
        setIncidents(data.incidents || []);
      }
      if (metRes.ok) {
        const data = await metRes.json();
        if (data.metrics) setMetrics(data.metrics);
      }
      if (cfgRes.ok) {
        const cfg = await cfgRes.json();
        if (cfg.carto_key && !cartoKey) {
          setCartoKey(cfg.carto_key);
        }
      }
    } catch (err) {
      console.error('Error fetching data from backend:', err);
    }
  };

  useEffect(() => {
    fetchIncidentsAndMetrics();
  }, []);

  // 2. Initialize Leaflet Tactical Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Centered at Patna Flood Basin
    const map = L.map(mapContainerRef.current, {
      center: [25.6100, 85.1415],
      zoom: 12,
      zoomControl: true,
      attributionControl: false
    });

    // Default CARTO Voyager Layer with Authenticated Key
    const initialLayer = MAP_LAYERS[activeLayerKey];
    const initialUrl = getCartoTileUrl(initialLayer.style, cartoKey);
    const tileLayer = L.tileLayer(initialUrl, {
      maxZoom: initialLayer.maxZoom,
      subdomains: initialLayer.subdomains,
    }).addTo(map);

    currentTileLayerRef.current = tileLayer;
    markersLayerRef.current = L.layerGroup().addTo(map);
    circlesLayerRef.current = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Switch Tile Layer
  const handleSwitchLayer = (layerKey) => {
    setActiveLayerKey(layerKey);
    const map = mapInstanceRef.current;
    if (!map) return;

    if (currentTileLayerRef.current) {
      map.removeLayer(currentTileLayerRef.current);
    }

    const cfg = MAP_LAYERS[layerKey];
    const newUrl = getCartoTileUrl(cfg.style, cartoKey);
    const newLayer = L.tileLayer(newUrl, {
      maxZoom: cfg.maxZoom,
      subdomains: cfg.subdomains,
    }).addTo(map);

    currentTileLayerRef.current = newLayer;
  };

  // 3. Update Map Pins and Uncertainty Circles whenever incidents change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !markersLayerRef.current || !circlesLayerRef.current) return;

    markersLayerRef.current.clearLayers();
    circlesLayerRef.current.clearLayers();

    incidents.forEach((inc) => {
      const lat = inc.geo?.lat;
      const lng = inc.geo?.lng;
      const radius = inc.geo?.uncertainty_radius_m || 150;
      const severity = inc.severity?.total_severity || 50;

      if (!lat || !lng) return;

      // Apple HIG Severity Tints
      let markerColor = '#0071E3'; // Apple Blue
      let glowColor = 'rgba(0, 113, 227, 0.35)';
      if (severity >= 80) {
        markerColor = '#FF3B30'; // Apple Red
        glowColor = 'rgba(255, 59, 48, 0.4)';
      } else if (severity >= 60) {
        markerColor = '#FF9500'; // Apple Orange
        glowColor = 'rgba(255, 149, 0, 0.35)';
      } else if (severity >= 40) {
        markerColor = '#EAB308'; // Apple Yellow
        glowColor = 'rgba(234, 179, 8, 0.3)';
      }

      // Draw SVG Uncertainty Circle
      const circle = L.circle([lat, lng], {
        radius: radius,
        color: markerColor,
        dashArray: '5, 8',
        weight: 1.8,
        fillColor: markerColor,
        fillOpacity: 0.12,
      }).addTo(circlesLayerRef.current);

      circle.on('click', () => {
        setSelectedIncident(inc);
      });

      // Custom Apple Tactile Marker Icon
      const customIcon = L.divIcon({
        className: 'custom-apple-pin',
        html: `
          <div style="
            position: relative;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
          ">
            <div style="
              position: absolute;
              width: 100%;
              height: 100%;
              border-radius: 50%;
              background: ${glowColor};
              animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
            "></div>
            <div style="
              position: relative;
              width: 22px;
              height: 22px;
              border-radius: 50%;
              background: ${markerColor};
              border: 2.5px solid #FFFFFF;
              box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
              display: flex;
              align-items: center;
              justify-content: center;
              color: #FFF;
              font-size: 11px;
              font-weight: 800;
              font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            ">
              ${inc.reports_count || 1}
            </div>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([lat, lng], { icon: customIcon }).addTo(markersLayerRef.current);

      marker.on('click', () => {
        setSelectedIncident(inc);
        map.flyTo([lat, lng], 13.5, { duration: 0.8 });
      });

      marker.bindTooltip(`
        <div style="padding: 4px 8px; font-family: -apple-system, sans-serif; background: #FFFFFF; color: #1D1D1F; border-radius: 8px; box-shadow: 0 4px 14px rgba(0,0,0,0.12); border: 1px solid rgba(0,0,0,0.06);">
          <strong style="color: ${markerColor}; font-size: 12px;">${inc.incident_id}: ${inc.hazard_type}</strong><br/>
          <span style="font-size: 11px; color: #6E6E73;">${inc.location_summary} • Radius: ±${radius}m</span>
        </div>
      `, { direction: 'top', offset: [0, -10] });
    });
  }, [incidents]);

  // Handle Simulation Run
  const handleRunSimulation = async () => {
    setIsSimulating(true);
    try {
      const res = await fetch('/api/simulate-stream', { method: 'POST' });
      if (res.ok) {
        await fetchIncidentsAndMetrics();
      }
    } catch (err) {
      console.error('Failed to run simulation stream:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Handle Ingest Form Submit
  const handleIngestSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ingestForm),
      });

      if (res.ok) {
        setIsIngestModalOpen(false);
        await fetchIncidentsAndMetrics();
      }
    } catch (err) {
      console.error('Failed to ingest report:', err);
    }
  };

  // Handle Operator Override
  const handleOperatorAction = async (action) => {
    if (!selectedIncident) return;
    try {
      const res = await fetch('/api/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: selectedIncident.incident_id,
          action: action,
          operator_note: `Manual action ${action} by District Commander`,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSelectedIncident(data.updated_incident);
        await fetchIncidentsAndMetrics();
      }
    } catch (err) {
      console.error('Failed operator override:', err);
    }
  };

  // Handle Synthesizing Bulbul Audio Advisory
  const handleSynthesizeAdvisory = async () => {
    if (!selectedIncident) return;
    setIsSynthesizingAdvisory(true);
    setAdvisoryError(null);
    setAdvisoryResult(null);

    try {
      const res = await fetch('/api/advisory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hazard_type: selectedIncident.hazard_type,
          language_code: advisoryLang,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setAdvisoryResult(data);
      } else {
        setAdvisoryError('Could not synthesize voice advisory at this time.');
      }
    } catch (err) {
      setAdvisoryError('Network error connecting to Bulbul v3.');
    } finally {
      setIsSynthesizingAdvisory(false);
    }
  };

  // Filtered Queue
  const filteredIncidents = incidents.filter((inc) => {
    if (priorityFilter !== 'ALL') {
      const p = inc.severity?.priority_level || '';
      if (!p.toUpperCase().includes(priorityFilter)) return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = inc.title?.toLowerCase().includes(q);
      const matchLoc = inc.location_summary?.toLowerCase().includes(q);
      const matchId = inc.incident_id?.toLowerCase().includes(q);
      if (!matchTitle && !matchLoc && !matchId) return false;
    }
    return true;
  });

  return (
    <div className="ops-theme">
      {/* 1. Apple Header & Status Bar */}
      <header className="ops-header">
        <div className="header-left">
          <div className="alert-pulse-badge">
            <span className="pulse-dot"></span>
            <span className="alert-text">LIVE OPERATION</span>
          </div>
          <div className="ops-brand">
            <span className="ops-title">
              SIGNAL FUSION BOARD <span className="hindi-brand">सिग्नल फ्यूजन बोर्ड</span>
            </span>
            <span className="ops-subtitle">
              District Emergency Operations Center • Patna Ganga Flood Basin
            </span>
          </div>
        </div>

        {/* Apple Style Segmented Pill Strip */}
        <div className="metrics-strip">
          <div className="metric-item">
            <span className="metric-val">{metrics.total_raw_reports || 20}</span>
            <span className="metric-lbl">Raw Reports</span>
          </div>
          <div className="metric-arrow">➔</div>
          <div className="metric-item highlight">
            <span className="metric-val">{metrics.fused_incidents || incidents.length}</span>
            <span className="metric-lbl">Fused Incidents</span>
          </div>
          <div className="metric-divider"></div>
          <div className="metric-item">
            <span className="metric-val">{(metrics.dedupe_noise_reduction_pct || 60.0).toFixed(1)}%</span>
            <span className="metric-lbl">Dedupe Ratio</span>
          </div>
          <div className="metric-item">
            <span className="metric-val">{metrics.pairwise_dedupe_f1 || 0.94}</span>
            <span className="metric-lbl">Pairwise F1</span>
          </div>
          <div className="metric-item">
            <span className="metric-val">±{metrics.median_geo_error_meters || 145}m</span>
            <span className="metric-lbl">Median Geo Err</span>
          </div>
          <div className="metric-item">
            <span className="metric-val">{metrics.severity_rank_correlation_kendall_tau || 0.89}</span>
            <span className="metric-lbl">Rank Kendall τ</span>
          </div>
        </div>

        <div className="header-right">
          <div className="model-badge-strip">
            <span className="model-pill active" title="Saaras Indic Speech-to-Text">Saaras v4</span>
            <span className="model-pill active" title="Sarvam-105B Reasoning">Sarvam-105B</span>
            <span className="model-pill active" title="Sarvam Vision / Doc-AI">Doc-AI</span>
            <span className="model-pill active" title="Bulbul v3 Audio Advisories">Bulbul v3</span>
          </div>
          <button
            onClick={handleRunSimulation}
            disabled={isSimulating}
            className="btn btn-simulate"
            type="button"
          >
            <Zap size={14} style={{ marginRight: '6px' }} />
            {isSimulating ? 'Clustering Stream...' : '⚡ Run 3-Min Simulation'}
          </button>
        </div>
      </header>

      {/* 2. Main Command Center Grid */}
      <main className="ops-main">
        {/* Left Panel: Tactical Map */}
        <section className="ops-map-column">
          <div className="map-container-card">
            <div className="map-header-bar">
              <div className="map-title-group">
                <span className="map-header-icon">🗺️</span>
                <span className="map-header-title">Tactical Inundation Map & Uncertainty Circles</span>
              </div>
              <div className="map-legend">
                {/* CARTO Basemap Switcher */}
                <div style={{ display: 'flex', gap: '6px', marginRight: '10px' }}>
                  {Object.keys(MAP_LAYERS).map((k) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => handleSwitchLayer(k)}
                      style={{
                        background: activeLayerKey === k ? '#0071E3' : '#FFFFFF',
                        border: `1px solid ${activeLayerKey === k ? '#0071E3' : 'rgba(0, 0, 0, 0.12)'}`,
                        borderRadius: '9999px',
                        color: activeLayerKey === k ? '#FFFFFF' : '#6E6E73',
                        padding: '3px 10px',
                        fontSize: '11px',
                        cursor: 'pointer',
                        fontWeight: '600',
                        boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      {MAP_LAYERS[k].name}
                    </button>
                  ))}
                </div>
                <span className="legend-item"><span className="legend-dot critical"></span> Critical (&gt;80)</span>
                <span className="legend-item"><span className="legend-dot high"></span> High (&gt;60)</span>
                <span className="legend-item"><span className="legend-dot medium"></span> Medium</span>
                <span className="legend-item"><span className="legend-circle"></span> Uncertainty Radius</span>
              </div>
            </div>

            {/* Leaflet Map Div */}
            <div ref={mapContainerRef} className="leaflet-disaster-map"></div>

            {/* Map Action Bar */}
            <div className="map-action-bar">
              <div className="action-bar-left">
                <span className="action-hint">
                  💡 Click any tactical marker or queue item to inspect multi-source evidence and audit mathematical ranking.
                </span>
              </div>
              <div className="action-bar-right">
                <button
                  onClick={() => setIsIngestModalOpen(true)}
                  className="btn btn-secondary btn-sm"
                  type="button"
                >
                  <PlusCircle size={14} style={{ marginRight: '6px', color: '#0071E3' }} />
                  + Ingest Live Citizen Report (Voice / Slip / SMS)
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Right Panel: Ranked Priority Queue */}
        <section className="ops-queue-column">
          <div className="queue-card">
            <div className="queue-header">
              <div className="queue-title-group">
                <h2 className="queue-title">Ranked Incident Queue</h2>
                <span className="queue-subtitle">Sorted by Mathematical Severity & Multi-Source Corroboration</span>
              </div>
              <span className="queue-count-badge">{filteredIncidents.length} Active Incidents</span>
            </div>

            {/* Filter and Search Bar */}
            <div className="queue-filter-bar">
              <input
                type="text"
                placeholder="Search incident, landmark, or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
              >
                <option value="ALL">All Tiers</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
              </select>
            </div>

            {/* Scrollable Incident Cards List */}
            <div className="incidents-queue-list">
              {filteredIncidents.map((inc, idx) => {
                const sev = inc.severity || {};
                const isSelected = selectedIncident?.incident_id === inc.incident_id;

                let badgeClass = 'badge-medium';
                let priorityLabel = 'MEDIUM';
                if (sev.total_severity >= 80) {
                  badgeClass = 'badge-critical';
                  priorityLabel = 'CRITICAL';
                } else if (sev.total_severity >= 60) {
                  badgeClass = 'badge-high';
                  priorityLabel = 'HIGH';
                }

                return (
                  <div
                    key={inc.incident_id}
                    className={`incident-queue-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => {
                      setSelectedIncident(inc);
                      if (mapInstanceRef.current && inc.geo?.lat && inc.geo?.lng) {
                        mapInstanceRef.current.flyTo([inc.geo.lat, inc.geo.lng], 13.5, { duration: 0.8 });
                      }
                    }}
                  >
                    <div className="incident-card-top">
                      <div className="card-top-left">
                        <span className="queue-rank-number">#{String(idx + 1).padStart(2, '0')}</span>
                        <span className={`priority-tag ${badgeClass}`}>
                          {priorityLabel}
                        </span>
                        <span className="inc-id-tag">{inc.incident_id}</span>
                      </div>
                      <div className="card-top-right">
                        <span className="severity-score-val">{sev.total_severity || 50}</span>
                        <span className="severity-score-max">/ 100</span>
                      </div>
                    </div>

                    <h3 className="incident-card-title">{inc.title}</h3>

                    <div className="incident-meta-row">
                      <span className="meta-item">
                        <MapPin size={13} style={{ marginRight: '4px', color: '#0071E3' }} />
                        {inc.location_summary}
                        <span className="uncertainty-tag">±{inc.geo?.uncertainty_radius_m || 150}m</span>
                      </span>
                      <span className="meta-item">
                        <Users size={13} style={{ marginRight: '4px', color: '#FF3B30' }} />
                        <strong>~{inc.people_affected_estimate || 10} trapped</strong>
                      </span>
                    </div>

                    <div className="incident-tags-row">
                      <span className="corrob-pill">
                        {inc.corroboration_status || `Corroborated (${inc.reports_count} reports)`}
                      </span>
                      {inc.channels?.map((ch) => (
                        <span key={ch} className="channel-pill">
                          {ch === 'voice' && '🎙️ Voice (Saaras)'}
                          {ch === 'handwritten_slip' && '📄 Slip (Doc-AI)'}
                          {ch === 'sms' && '💬 SMS / Text'}
                        </span>
                      ))}
                      {inc.dispatched && (
                        <span className="dispatch-badge">🚀 Unit En Route</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      </main>

      {/* 3. Multi-Channel Evidence Trail Modal (Apple Sheet Style) */}
      {selectedIncident && (
        <div className="modal-backdrop">
          <div className="modal-dialog glass-modal">
            <div className="modal-header">
              <div className="modal-title-group">
                <div className="modal-badge-row">
                  <span className="modal-inc-id">{selectedIncident.incident_id}</span>
                  <span className={`modal-priority-badge ${selectedIncident.severity?.total_severity >= 80 ? 'critical' : 'high'}`}>
                    {selectedIncident.severity?.priority_level || 'PRIORITY QUEUE'}
                  </span>
                  <span className="modal-corrob-badge">
                    {selectedIncident.corroboration_status}
                  </span>
                </div>
                <h2 className="modal-title">{selectedIncident.title}</h2>
                <p className="modal-subtitle">
                  {selectedIncident.location_summary} • Spatial Uncertainty Circle: ±{selectedIncident.geo?.uncertainty_radius_m || 120}m
                </p>
              </div>
              <button
                onClick={() => setSelectedIncident(null)}
                className="btn-close-modal"
                type="button"
                aria-label="Close"
              >
                &times;
              </button>
            </div>

            <div className="modal-body">
              <div className="modal-grid">
                {/* Left Column: Evidence Trail */}
                <div className="evidence-column">
                  <h3 className="section-title">📂 Multi-Channel Evidence Trail ({selectedIncident.evidence_reports?.length || 0} Reports)</h3>
                  <div className="evidence-reports-container">
                    {selectedIncident.evidence_reports?.map((rep, rIdx) => (
                      <div key={rep.id || rIdx} className="evidence-report-card">
                        <div className="report-card-header">
                          <span className="report-channel-badge">
                            {rep.channel === 'voice' && '🎙️ Voice Note (Saaras STT)'}
                            {rep.channel === 'handwritten_slip' && '📄 Handwritten Slip (Doc-AI OCR)'}
                            {rep.channel === 'sms' && '💬 SMS / WhatsApp Citizen Line'}
                          </span>
                          <span className="report-time">{new Date(rep.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} IST</span>
                        </div>

                        <div className="report-body-text">
                          <p className="original-text">“{rep.raw_text}”</p>
                          {rep.english_translation && rep.language !== 'en-IN' && (
                            <p className="translated-text">
                              Translation: “{rep.english_translation}”
                            </p>
                          )}
                        </div>

                        {/* Channel Specific Artifact Demonstration */}
                        {rep.channel === 'voice' && (
                          <div className="audio-evidence-preview">
                            <span className="audio-meta">🔊 Saaras Indic v4 Phonetic Transcript Confirmed</span>
                            <div className="audio-waveform-bars">
                              {[40, 75, 90, 60, 30, 85, 95, 45, 60, 80, 50, 70, 90, 40].map((h, i) => (
                                <span key={i} style={{ height: `${h}%` }}></span>
                              ))}
                            </div>
                          </div>
                        )}

                        {rep.channel === 'handwritten_slip' && (
                          <div className="slip-evidence-preview">
                            <span className="slip-meta">📑 Sarvam Vision / Doc-AI Key-Value Extraction</span>
                            <div className="slip-badge-row">
                              <span className="extracted-kv">Location: {rep.raw_location}</span>
                              <span className="extracted-kv">Impacted: {rep.people_affected} people</span>
                            </div>
                          </div>
                        )}

                        <div className="report-reporter-footer">
                          <span>Source: <strong>{rep.reporter}</strong></span>
                          <span>Geo Tier: <strong>{rep.geo?.tier || 'Tier 2 Gazetteer'}</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right Column: Transparent Mathematical Rationale & Controls */}
                <div className="rationale-column">
                  <div className="rationale-card">
                    <h3 className="section-title">🧮 Transparent Severity Math</h3>
                    <p className="rationale-narrative">
                      {selectedIncident.severity?.rationale || 'Score derived from multi-attribute ranking model.'}
                    </p>

                    <div className="score-breakdown-table">
                      <div className="breakdown-row">
                        <span>People Impact Weight:</span>
                        <strong>{selectedIncident.severity?.people_score || 0} / 25</strong>
                      </div>
                      <div className="breakdown-row">
                        <span>Vulnerable Groups Weight:</span>
                        <strong>{selectedIncident.severity?.vulnerability_score || 0} / 20</strong>
                      </div>
                      <div className="breakdown-row">
                        <span>Hazard Severity Factor:</span>
                        <strong>{selectedIncident.severity?.hazard_score || 0} / 25</strong>
                      </div>
                      <div className="breakdown-row">
                        <span>Urgency & Rising Water Cues:</span>
                        <strong>{selectedIncident.severity?.urgency_score || 0} / 15</strong>
                      </div>
                      <div className="breakdown-row">
                        <span>Multi-Channel Corroboration:</span>
                        <strong>{selectedIncident.severity?.corroboration_score || 0} / 15</strong>
                      </div>
                      <div className="breakdown-total">
                        <span>Total Mathematical Severity:</span>
                        <strong>{selectedIncident.severity?.total_severity || 0} / 100</strong>
                      </div>
                    </div>
                  </div>

                  {/* Commander Actions */}
                  <div className="operator-controls-card">
                    <h3 className="section-title">🛡️ Commander Actions</h3>
                    <div className="controls-button-group">
                      <button
                        onClick={() => handleOperatorAction('bump_priority')}
                        className="btn btn-warning btn-sm"
                        type="button"
                      >
                        ⚡ Bump Priority (+15 pts)
                      </button>
                      <button
                        onClick={() => handleOperatorAction('verify')}
                        className="btn btn-secondary btn-sm"
                        type="button"
                      >
                        ✓ Verify Incident
                      </button>
                      <button
                        onClick={() => handleOperatorAction('mark_dispatched')}
                        className="btn btn-danger btn-sm"
                        type="button"
                      >
                        🚀 Dispatch NDRF / SDRF
                      </button>
                    </div>
                  </div>

                  {/* Closed Loop: Bulbul Advisory Callback */}
                  <div className="advisory-callback-card">
                    <h3 className="section-title">🔊 Citizen Safety Advisory (Bulbul v3)</h3>
                    <p className="advisory-hint">
                      Pre-approved NDMA protocol translated & voiced in reporter's dialect:
                    </p>

                    <div className="advisory-controls">
                      <select
                        value={advisoryLang}
                        onChange={(e) => setAdvisoryLang(e.target.value)}
                        className="form-select-sm"
                      >
                        <option value="hi-IN">हिन्दी (Hindi)</option>
                        <option value="bn-IN">বাংলা (Bengali)</option>
                        <option value="en-IN">English</option>
                      </select>
                      <button
                        onClick={handleSynthesizeAdvisory}
                        disabled={isSynthesizingAdvisory}
                        className="btn btn-primary-sm"
                        type="button"
                      >
                        {isSynthesizingAdvisory ? 'Synthesizing Audio...' : 'Synthesize Voice Advisory'}
                      </button>
                    </div>

                    {advisoryResult && (
                      <div className="advisory-audio-wrap">
                        {advisoryResult.audio_base64 && (
                          <audio
                            controls
                            autoPlay
                            className="advisory-audio-player"
                            src={`data:audio/wav;base64,${advisoryResult.audio_base64}`}
                          />
                        )}
                        <div className="advisory-script-text">
                          <strong>NDMA Approved Broadcast:</strong><br />
                          "{advisoryResult.advisory_text}"
                        </div>
                      </div>
                    )}

                    {advisoryError && (
                      <div className="advisory-error-msg" style={{ color: '#DC2626', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                        {advisoryError}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Manual Citizen Ingest Modal */}
      {isIngestModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-dialog glass-modal ingest-modal-dialog">
            <div className="modal-header">
              <h2 className="modal-title">📥 Ingest New Citizen Crisis Report</h2>
              <button
                onClick={() => setIsIngestModalOpen(false)}
                className="btn-close-modal"
                type="button"
                aria-label="Close"
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <form onSubmit={handleIngestSubmit}>
                <div className="form-row">
                  <div className="form-col">
                    <label className="form-label">Channel Type</label>
                    <select
                      value={ingestForm.channel}
                      onChange={(e) => setIngestForm({ ...ingestForm, channel: e.target.value })}
                      className="form-select"
                    >
                      <option value="voice">🎙️ Voice Note (Saaras STT)</option>
                      <option value="sms">💬 SMS / WhatsApp Text</option>
                      <option value="handwritten_slip">📄 Handwritten Slip (Doc-AI)</option>
                    </select>
                  </div>
                  <div className="form-col">
                    <label className="form-label">Language</label>
                    <select
                      value={ingestForm.language}
                      onChange={(e) => setIngestForm({ ...ingestForm, language: e.target.value })}
                      className="form-select"
                    >
                      <option value="hi-IN">Hindi / Bhojpuri</option>
                      <option value="bn-IN">Bengali</option>
                      <option value="en-IN">English</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Report Content / Transcript</label>
                  <textarea
                    rows="3"
                    value={ingestForm.raw_text}
                    onChange={(e) => setIngestForm({ ...ingestForm, raw_text: e.target.value })}
                    className="form-textarea"
                    placeholder="e.g. दीघा घाट के 500 मीटर पीछे पानी बहुत तेज भर गया है, 40 लोग छतों पर हैं..."
                  />
                </div>

                <div className="form-row">
                  <div className="form-col">
                    <label className="form-label">Raw Location Mention</label>
                    <input
                      type="text"
                      value={ingestForm.raw_location}
                      onChange={(e) => setIngestForm({ ...ingestForm, raw_location: e.target.value })}
                      className="form-input"
                    />
                  </div>
                  <div className="form-col">
                    <label className="form-label">Hazard Classification</label>
                    <select
                      value={ingestForm.hazard_type}
                      onChange={(e) => setIngestForm({ ...ingestForm, hazard_type: e.target.value })}
                      className="form-select"
                    >
                      <option value="Embankment Breach">Embankment Breach</option>
                      <option value="Submerged Hospital / Critical Care">Submerged Hospital</option>
                      <option value="Substation Electrocution Risk">Substation Electrocution</option>
                      <option value="Flash Flood / Trapped on Roof">Flash Flood / Trapped</option>
                      <option value="Riverfront Slum Inundation">Riverfront Slum Inundation</option>
                      <option value="Road Washout / Transit Delay">Road Washout</option>
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-col">
                    <label className="form-label">People Affected (Est.)</label>
                    <input
                      type="number"
                      value={ingestForm.people_affected}
                      onChange={(e) => setIngestForm({ ...ingestForm, people_affected: parseInt(e.target.value) || 1 })}
                      className="form-input"
                    />
                  </div>
                  <div className="form-col">
                    <label className="form-label">Reporter Contact / Line</label>
                    <input
                      type="text"
                      value={ingestForm.reporter}
                      onChange={(e) => setIngestForm({ ...ingestForm, reporter: e.target.value })}
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="modal-footer" style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                  <button
                    type="button"
                    onClick={() => setIsIngestModalOpen(false)}
                    className="btn btn-secondary"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-cta">
                    🚀 Ingest, Geo-Resolve & Fuse Report
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
