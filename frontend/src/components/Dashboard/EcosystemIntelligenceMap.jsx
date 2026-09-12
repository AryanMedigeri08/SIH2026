/**
 * EcosystemIntelligenceMap.jsx — MSME Density Heatmap (Step 1).
 *
 * Step 1: Village-level MSME registration density heatmap on geographic map.
 * Shows aggregate MSME counts per village/locality as heat intensity.
 *
 * Step 2+ features (enterprise nodes, edges, force-directed graph, temporal
 * scrubber, opportunity overlay) are COMMENTED OUT below — not deleted — and
 * will be incrementally re-enabled in future steps.
 *
 * Engineering Rules:
 *  - This component is a READ-MODEL consumer, not a second analytical engine.
 *  - Zero coordinate fabrication: unmapped entities are shown in a sidebar panel.
 *  - Bi-modal rendering via ViewModeContext (beneficiary vs banker).
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Map, Network, Eye, EyeOff, Filter, Layers,
  AlertTriangle, Info, ChevronRight, ChevronLeft,
  ZoomIn, ZoomOut, Maximize2, Play, Pause,
  Building2, Link2, MapPin, BarChart3, Clock,
  HelpCircle, X, Search, AlertCircle, Loader2,
  GitBranch, Users, Store, Factory, Truck,
  Crosshair, Circle, ArrowRight
} from 'lucide-react';
import { useViewMode, VIEW_MODES } from '../../context/ViewModeContext';

// ── Constants ────────────────────────────────────────────────────────────────

const MAP_PADDING = 40;

const STATE_CODES = {
  LOADING: 'LOADING',
  READY: 'READY',
  EMPTY: 'EMPTY',
  ERROR: 'ERROR',
  NO_DATA: 'NO_DATA',
};

/* STEP2: Enterprise node constants (preserved for future steps)
const NODE_BASE_RADIUS = 6;
const NODE_SELECTED_RADIUS = 10;
const EDGE_WIDTH_DEFAULT = 1;
const EDGE_WIDTH_SELECTED = 2.5;
const ANIMATION_DURATION = 300;

const PROJECTION_MODES = {
  GEOGRAPHIC: 'geographic',
  TOPOLOGICAL: 'topological',
};

const RELATIONSHIP_COLORS = {
  COMPETITOR: '#EF4444',
  SUPPLY_CHAIN: '#3B82F6',
};

const PRECISION_ICONS = {
  EXACT: '📍',
  LOCALITY: '🏘️',
  VILLAGE: '🏠',
  PINCODE: '📮',
  UNMAPPED: '❓',
};
*/

// ── Tile Servers (Google Maps + CartoDB + OpenStreetMap) ─────────────────────

const TILE_SERVERS = {
  GOOGLE_STREETS: {
    name: 'Google Maps',
    url: 'https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Maps Cartography',
    maxZoom: 20,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
  },
  GOOGLE_TERRAIN: {
    name: 'Google Terrain',
    url: 'https://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Maps',
    maxZoom: 20,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
  },
  GOOGLE_SATELLITE: {
    name: 'Google Satellite',
    url: 'https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attribution: '&copy; Google Maps Satellite',
    maxZoom: 20,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
  },
  VOYAGER: {
    name: 'Carto Light',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    maxZoom: 19,
    subdomains: 'abcd',
  },
  DARK: {
    name: 'Carto Dark',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    maxZoom: 19,
    subdomains: 'abcd',
  },
  OSM: {
    name: 'OSM Standard',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
    subdomains: ['a', 'b', 'c'],
  },
};

// ── Grad-CAM Thermal Color Scale (Jet / Turbo Colormap) ──────────────────────

const GRADCAM_GRADIENT = {
  0.00: 'rgba(0, 0, 128, 0)',        // 0% Transparent baseline
  0.15: 'rgba(0, 0, 255, 0.55)',     // Blue - low baseline activation
  0.35: '#00e5ff',                  // Cyan - mild activation
  0.55: '#00e676',                  // Emerald green - moderate density
  0.72: '#ffeb3b',                  // Vibrant Yellow - elevated cluster density
  0.88: '#ff9100',                  // Amber Orange - high density hotspot
  1.00: '#ff1744',                  // Crimson Red - peak cluster activation
};

const DENSITY_COLORS = [
  { threshold: 0.00, color: '#2563EB', label: 'Baseline (0.0 - 0.25)' },
  { threshold: 0.25, color: '#06B6D4', label: 'Mild (0.25 - 0.50)' },
  { threshold: 0.50, color: '#10B981', label: 'Moderate (0.50 - 0.70)' },
  { threshold: 0.70, color: '#F59E0B', label: 'High (0.70 - 0.85)' },
  { threshold: 0.85, color: '#EF4444', label: 'Peak Hotspot (0.85 - 1.0)' },
];

function getDensityColor(normalizedIntensity) {
  for (let i = DENSITY_COLORS.length - 1; i >= 0; i--) {
    if (normalizedIntensity >= DENSITY_COLORS[i].threshold) {
      return DENSITY_COLORS[i].color;
    }
  }
  return DENSITY_COLORS[0].color;
}

// ── Sub-components (Light Theme) ─────────────────────────────────────────────

function MetricCard({ label, value, icon: Icon }) {
  return (
    <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-2xs hover:border-slate-300 transition-colors">
      <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
        {Icon && <Icon size={13} className="text-indigo-600" />}
        <span className="font-medium">{label}</span>
      </div>
      <div className="text-base sm:text-lg font-bold font-mono text-slate-900 truncate">
        {typeof value === 'object' ? JSON.stringify(value) : value ?? '—'}
      </div>
    </div>
  );
}

// ── Leaflet Heatmap View (Grad-CAM Mode) ────────────────────────────────────

function LeafletHeatmapView({
  villageDensity,
  catchment,
  width,
  height,
  tileStyle = 'GOOGLE_STREETS',
  onTileStyleChange,
  selectedVillage,
  onVillageClick,
  targetLocationName,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const layersGroupRef = useRef(null);
  const heatLayerRef = useRef(null);
  const [leafletAvailable, setLeafletAvailable] = useState(
    typeof window !== 'undefined' && !!window.L
  );

  // Detect Leaflet loaded via CDN
  useEffect(() => {
    if (leafletAvailable) return;
    const interval = setInterval(() => {
      if (typeof window !== 'undefined' && window.L) {
        setLeafletAvailable(true);
        clearInterval(interval);
      }
    }, 100);
    return () => clearInterval(interval);
  }, [leafletAvailable]);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!leafletAvailable || !mapContainerRef.current || mapInstanceRef.current) return;
    const L = window.L;

    const centerLat = catchment?.center?.latitude || 28.6146;
    const centerLon = catchment?.center?.longitude || 77.2090;

    const map = L.map(mapContainerRef.current, {
      center: [centerLat, centerLon],
      zoom: 11,
      zoomControl: false,
      attributionControl: false,
    });

    // Custom attribution control
    L.control.attribution({ position: 'bottomright', prefix: false })
      .addAttribution('&copy; <a href="https://maps.google.com" target="_blank" rel="noreferrer">Google / OSM Cartography</a>')
      .addTo(map);

    // Initial tile layer (defaults to Google Maps)
    const tileConfig = TILE_SERVERS[tileStyle] || TILE_SERVERS.GOOGLE_STREETS;
    const tiles = L.tileLayer(tileConfig.url, {
      attribution: tileConfig.attribution,
      maxZoom: tileConfig.maxZoom,
      subdomains: tileConfig.subdomains,
    }).addTo(map);

    tileLayerRef.current = tiles;
    layersGroupRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [leafletAvailable]);

  // Handle tile style changes
  useEffect(() => {
    if (!mapInstanceRef.current || !leafletAvailable) return;
    const L = window.L;
    const tileConfig = TILE_SERVERS[tileStyle] || TILE_SERVERS.GOOGLE_STREETS;
    if (tileLayerRef.current) {
      mapInstanceRef.current.removeLayer(tileLayerRef.current);
    }
    const newTiles = L.tileLayer(tileConfig.url, {
      attribution: tileConfig.attribution,
      maxZoom: tileConfig.maxZoom,
      subdomains: tileConfig.subdomains,
    }).addTo(mapInstanceRef.current);
    newTiles.bringToBack();
    tileLayerRef.current = newTiles;
  }, [tileStyle, leafletAvailable]);

  // Invalidate size on dimensions change
  useEffect(() => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.invalidateSize();
    }
  }, [width, height]);

  // Render Grad-CAM Heatmap + User Location Pin + Catchment + Micro-targets
  useEffect(() => {
    if (!mapInstanceRef.current || !layersGroupRef.current || !leafletAvailable) return;
    const L = window.L;
    const lg = layersGroupRef.current;
    lg.clearLayers();

    // Remove existing heat layer
    if (heatLayerRef.current) {
      mapInstanceRef.current.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }

    const centerLat = catchment?.center?.latitude;
    const centerLon = catchment?.center?.longitude;

    // 1. Catchment Rings + User Location Pin
    if (centerLat != null && centerLon != null) {
      // Pan smoothly to updated catchment center
      mapInstanceRef.current.panTo([centerLat, centerLon], { animate: true, duration: 0.8 });

      const radiusMeters = (catchment?.radiusKm || 10) * 1000;

      // Outer catchment boundary circle
      L.circle([centerLat, centerLon], {
        radius: radiusMeters,
        color: '#2563EB',
        weight: 1.5,
        dashArray: '6, 6',
        fillColor: '#3B82F6',
        fillOpacity: 0.03,
      }).bindTooltip(`Catchment Radius: ${catchment?.radiusKm || 10} km`, { sticky: true }).addTo(lg);

      // Core immediate zone (50% radius)
      L.circle([centerLat, centerLon], {
        radius: radiusMeters * 0.5,
        color: '#3B82F6',
        weight: 1,
        dashArray: '4, 4',
        fillColor: '#60A5FA',
        fillOpacity: 0.05,
      }).bindTooltip(`Core Zone: ${((catchment?.radiusKm || 10) * 0.5).toFixed(1)} km`, { sticky: true }).addTo(lg);

      // User Location Custom Pin Icon (Prominent marker with animated radar ripple)
      const userLocationIcon = L.divIcon({
        className: 'user-location-marker-wrapper',
        html: `
          <div style="position: relative; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;">
            <span class="user-pulse-ring-1"></span>
            <span class="user-pulse-ring-2"></span>
            <div class="user-pin-head">
              <svg style="width: 14px; height: 14px; fill: #ffffff; transform: rotate(45deg);" viewBox="0 0 24 24">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
              </svg>
            </div>
            <div class="user-pin-shadow"></div>
          </div>
        `,
        iconSize: [44, 44],
        iconAnchor: [22, 36],
        popupAnchor: [0, -36],
      });

      L.marker([centerLat, centerLon], { icon: userLocationIcon, zIndexOffset: 1000 })
        .bindPopup(`
          <div style="font-family: system-ui, sans-serif; font-size: 12px; line-height: 1.4; color: #0F172A; min-width: 190px;">
            <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; color: #1D4ED8; margin-bottom: 4px; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px;">
              <span>📍</span>
              <span>${targetLocationName || catchment?.village || 'Your Target Location'}</span>
            </div>
            <div style="color: #475569; font-size: 11px;">
              <div>Catchment Center: <b>${centerLat.toFixed(4)}°N, ${centerLon.toFixed(4)}°E</b></div>
              <div style="margin-top: 2px;">Analysis Radius: <b>${catchment?.radiusKm || 10} km</b></div>
            </div>
            <div style="margin-top: 6px; padding: 4px 6px; background: #EFF6FF; border-radius: 6px; color: #1E40AF; font-size: 10px; font-weight: 500;">
              Active Catchment Origin
            </div>
          </div>
        `)
        .addTo(lg);
    }

    // 2. Grad-CAM Activation Heatmap Layer (Continuous thermal dispersion field)
    if (villageDensity?.length > 0 && L.heatLayer) {
      const maxCount = Math.max(...villageDensity.map(v => v.msmeCount), 1);

      // Build Grad-CAM intensity points: [lat, lng, normalized_intensity]
      const heatPoints = [];
      for (const village of villageDensity) {
        if (village.latitude != null && village.longitude != null) {
          // Continuous activation weight between 0.15 and 1.0
          const weight = Math.max(village.msmeCount / maxCount, 0.15);
          heatPoints.push([village.latitude, village.longitude, weight]);
        }
      }

      if (heatPoints.length > 0) {
        const heat = L.heatLayer(heatPoints, {
          radius: 54,       // Generous radius for smooth continuous thermal contours
          blur: 34,         // Gaussian blur for organic Grad-CAM activation field
          maxZoom: 15,
          max: 1.0,
          minOpacity: 0.40,
          gradient: GRADCAM_GRADIENT,
        }).addTo(mapInstanceRef.current);
        heatLayerRef.current = heat;
      }
    }

    // 3. Grad-CAM Precision Focal Targets (subtle micro-nodes, NO cartoonish circles)
    if (villageDensity?.length > 0) {
      const maxCount = Math.max(...villageDensity.map(v => v.msmeCount), 1);

      for (const village of villageDensity) {
        if (village.latitude == null || village.longitude == null) continue;

        const isSelected = selectedVillage?.villageName === village.villageName;
        const isMaxHotspot = village.msmeCount === maxCount && maxCount > 1;

        // Clean, subtle micro-target point (non-intrusive)
        const marker = L.circleMarker([village.latitude, village.longitude], {
          radius: isSelected ? 6 : (isMaxHotspot ? 5 : 3.5),
          fillColor: isSelected ? '#1D4ED8' : (isMaxHotspot ? '#DC2626' : '#FFFFFF'),
          color: isSelected ? '#FFFFFF' : (isMaxHotspot ? '#FFFFFF' : '#1E293B'),
          weight: isSelected ? 2.5 : (isMaxHotspot ? 2 : 1.2),
          fillOpacity: isSelected ? 1.0 : (isMaxHotspot ? 0.95 : 0.75),
        });

        marker.on('click', () => onVillageClick?.(village));

        // Hover tooltip with clean scientific Grad-CAM telemetry (not permanent sticker)
        const activationPct = Math.round((village.msmeCount / maxCount) * 100);
        marker.bindTooltip(`
          <div style="font-family: system-ui, sans-serif; font-size: 11px; color: #0F172A; padding: 2px 4px;">
            <div style="font-weight: 700; color: #1E293B;">${village.villageName}</div>
            <div style="color: #475569; display: flex; gap: 8px; justify-content: space-between; margin-top: 2px;">
              <span><b>${village.msmeCount}</b> MSMEs</span>
              <span style="color: ${activationPct > 70 ? '#DC2626' : activationPct > 40 ? '#D97706' : '#2563EB'}; font-weight: 600;">
                ${activationPct}% Activation
              </span>
            </div>
          </div>
        `, {
          direction: 'top',
          offset: [0, -6],
          className: 'gradcam-tooltip',
        });

        // Click Popup with complete cluster telemetry
        const sectorLines = Object.entries(village.sectorBreakdown || {})
          .sort(([, a], [, b]) => b - a)
          .slice(0, 5)
          .map(([sector, count]) =>
            `<div style="display: flex; justify-content: space-between; gap: 12px; margin-bottom: 2px;">
              <span style="color: #64748B;">${sector.replace(/_/g, ' ')}</span>
              <span style="font-weight: 600; color: #0F172A;">${count}</span>
            </div>`
          )
          .join('');

        const popupContent = `
          <div style="font-family: system-ui, sans-serif; font-size: 12px; line-height: 1.5; min-width: 210px; color: #0F172A;">
            <div style="font-weight: 700; font-size: 13px; color: #0F172A; margin-bottom: 4px; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
              <span>📍 ${village.villageName}</span>
              ${isMaxHotspot ? '<span style="background: #FEE2E2; color: #DC2626; font-size: 9px; padding: 1px 6px; border-radius: 9999px; font-weight: 700;">PEAK HOTSPOT</span>' : ''}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 6px 0; background: #F8FAFC; padding: 6px 8px; border-radius: 8px; border: 1px solid #F1F5F9;">
              <span style="color: #64748B; font-size: 11px;">MSME Registrations</span>
              <span style="font-size: 16px; font-weight: 800; color: #1D4ED8;">${village.msmeCount}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748B; margin-bottom: 4px;">
              <span>Grad-CAM Activation</span>
              <span style="font-weight: 700; color: ${activationPct > 70 ? '#DC2626' : activationPct > 40 ? '#D97706' : '#2563EB'};">${activationPct}%</span>
            </div>
            ${village.pincode ? `<div style="color: #64748B; font-size: 10px;">📮 Pincode: <b>${village.pincode}</b></div>` : ''}
            ${village.precision ? `<div style="color: #64748B; font-size: 10px; margin-bottom: 4px;">📐 Precision: <b>${village.precision}</b></div>` : ''}
            ${sectorLines ? `
              <div style="border-top: 1px solid #E2E8F0; padding-top: 6px; margin-top: 6px;">
                <div style="font-size: 10px; font-weight: 700; color: #4338CA; margin-bottom: 4px; letter-spacing: 0.025em;">PRIMARY SECTORS</div>
                ${sectorLines}
              </div>
            ` : ''}
            ${village.unmappedCount > 0 ? `
              <div style="margin-top: 6px; padding: 4px 6px; background: #FFFBEB; border: 1px solid #FEF3C7; border-radius: 6px; font-size: 10px; color: #B45309;">
                ⚠️ +${village.unmappedCount} enterprise(s) at locality with unresolved GPS
              </div>
            ` : ''}
          </div>
        `;

        marker.bindPopup(popupContent, { maxWidth: 280 });
        marker.addTo(lg);
      }
    }

    // Auto fit bounds
    const allPoints = [];
    if (centerLat != null && centerLon != null) {
      allPoints.push([centerLat, centerLon]);
    }
    for (const v of (villageDensity || [])) {
      if (v.latitude != null && v.longitude != null) {
        allPoints.push([v.latitude, v.longitude]);
      }
    }
    if (allPoints.length > 0 && !mapInstanceRef.current._hasFitBounds) {
      const L = window.L;
      const bounds = L.latLngBounds(allPoints);
      mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
      mapInstanceRef.current._hasFitBounds = true;
    }
  }, [villageDensity, catchment, selectedVillage, leafletAvailable]);

  if (!leafletAvailable) {
    return (
      <div className="flex items-center justify-center bg-slate-50 rounded-xl border border-slate-200" style={{ width, height }}>
        <div className="text-center space-y-2">
          <Loader2 size={24} className="text-indigo-600 animate-spin mx-auto" />
          <p className="text-slate-500 text-xs">Loading map tiles...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-50" style={{ width, height }}>
      {/* Light Popup, Tooltip & Keyframe Overrides */}
      <style>{`
        @keyframes userRadarPulse {
          0% { transform: scale(0.6); opacity: 0.9; }
          50% { opacity: 0.5; }
          100% { transform: scale(1.6); opacity: 0; }
        }
        .user-pulse-ring-1 {
          position: absolute;
          width: 44px;
          height: 44px;
          border-radius: 9999px;
          background: rgba(37, 99, 235, 0.3);
          animation: userRadarPulse 2s ease-out infinite;
        }
        .user-pulse-ring-2 {
          position: absolute;
          width: 30px;
          height: 30px;
          border-radius: 9999px;
          background: rgba(37, 99, 235, 0.4);
          animation: userRadarPulse 2s ease-out 0.6s infinite;
        }
        .user-pin-head {
          position: relative;
          z-index: 10;
          width: 30px;
          height: 30px;
          background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
          border: 2.5px solid #ffffff;
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 4px 12px rgba(37, 99, 235, 0.45);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .user-pin-shadow {
          position: absolute;
          bottom: 2px;
          width: 14px;
          height: 4px;
          background: rgba(0,0,0,0.25);
          border-radius: 50%;
          filter: blur(1px);
        }
        .leaflet-popup-content-wrapper {
          background: #FFFFFF !important;
          color: #0F172A !important;
          border: 1px solid #E2E8F0 !important;
          border-radius: 12px !important;
          box-shadow: 0 12px 24px -4px rgba(15, 23, 42, 0.12), 0 4px 6px -2px rgba(15, 23, 42, 0.04) !important;
        }
        .leaflet-popup-tip {
          background: #FFFFFF !important;
        }
        .leaflet-popup-close-button {
          color: #64748B !important;
        }
        .leaflet-container {
          background: #F8FAFC !important;
        }
        .gradcam-tooltip {
          background: #FFFFFF !important;
          border: 1px solid #CBD5E1 !important;
          border-radius: 8px !important;
          box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1) !important;
          padding: 3px 6px !important;
        }
        .gradcam-tooltip:before {
          border-top-color: #FFFFFF !important;
        }
      `}</style>

      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* Base Tile Switcher (Light Mode Glassmorphic) */}
      <div className="absolute top-3 left-3 z-[400] flex items-center bg-white/95 backdrop-blur-md rounded-lg p-1 border border-slate-200 shadow-md text-[11px] gap-1">
        {Object.entries(TILE_SERVERS).map(([key, cfg]) => (
          <button
            key={key}
            onClick={() => onTileStyleChange?.(key)}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
              tileStyle === key
                ? 'bg-indigo-600 text-white shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            {cfg.name}
          </button>
        ))}
      </div>

      {/* Attribution badge */}
      <div className="absolute bottom-2 left-3 z-[400] bg-white/90 backdrop-blur-sm border border-slate-200/80 rounded px-2 py-0.5 text-[9px] text-slate-500 pointer-events-none shadow-2xs">
        Google Maps / OSM • Grad-CAM Thermal Field
      </div>
    </div>
  );
}

// ── Grad-CAM Legend (Continuous Thermal Activation Spectrum) ────────────────

function GradCamLegend({ villageDensity }) {
  const totalMsmes = villageDensity?.reduce((s, v) => s + v.msmeCount, 0) || 0;
  const clusterCount = villageDensity?.length || 0;
  const maxCount = Math.max(...(villageDensity?.map(v => v.msmeCount) || [0]), 1);

  return (
    <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-md rounded-xl border border-slate-200 p-3.5 z-[400] shadow-lg max-w-[240px] text-slate-800">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold tracking-wider text-slate-500 uppercase">Grad-CAM Activation</span>
        <span className="text-[9px] font-medium px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded border border-indigo-100">Thermal</span>
      </div>

      {/* Jet / Turbo Continuous Spectrum Bar */}
      <div className="space-y-1 mb-2.5">
        <div
          className="h-2.5 w-full rounded-full shadow-inner border border-slate-200/80"
          style={{
            background: 'linear-gradient(to right, #0000ff 0%, #00e5ff 25%, #00e676 50%, #ffeb3b 75%, #ff1744 100%)',
          }}
        />
        <div className="flex justify-between text-[9px] font-medium text-slate-500">
          <span>0.0 (Cold)</span>
          <span>0.5 (Moderate)</span>
          <span>1.0 (Peak)</span>
        </div>
      </div>

      <div className="border-t border-slate-100 pt-2 space-y-1 text-[11px]">
        <div className="flex justify-between">
          <span className="text-slate-500">Total Catchment MSMEs</span>
          <span className="font-bold text-slate-900">{totalMsmes.toLocaleString('en-IN')}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Village Hubs</span>
          <span className="font-semibold text-slate-800">{clusterCount}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Peak Hub Volume</span>
          <span className="font-semibold text-rose-600">{maxCount} MSMEs</span>
        </div>
      </div>
    </div>
  );
}

// ── Village Detail Panel (Light Theme) ──────────────────────────────────────

function VillageDetailPanel({ village, onClose }) {
  if (!village) return null;

  const sectorEntries = Object.entries(village.sectorBreakdown || {})
    .sort(([, a], [, b]) => b - a);

  return (
    <div className="absolute right-0 top-0 bottom-0 w-80 bg-white/98 backdrop-blur-md border-l border-slate-200 text-slate-800 overflow-y-auto z-[500] shadow-xl animate-slide-in-right">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-slate-900 truncate">{village.villageName || 'Village'}</h3>
          <button onClick={onClose} aria-label="Close village details" className="text-slate-400 hover:text-slate-700 transition-colors p-1 rounded-lg hover:bg-slate-100">
            <X size={16} />
          </button>
        </div>

        <div className="space-y-3">
          {/* MSME Count Hero */}
          <div className="bg-indigo-50/80 rounded-xl p-4 border border-indigo-100 text-center shadow-2xs">
            <div className="text-3xl font-extrabold text-indigo-700">{village.msmeCount}</div>
            <div className="text-xs text-indigo-600 font-medium mt-1">Registered MSMEs</div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              Grad-CAM Activation: {Math.round((village.intensityNormalized || 0) * 100)}%
            </div>
          </div>

          {/* Metadata */}
          <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/80 text-xs space-y-2">
            {village.pincode && (
              <div className="flex justify-between">
                <span className="text-slate-500">Pincode</span>
                <span className="text-slate-900 font-mono font-medium">{village.pincode}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-500">Spatial Precision</span>
              <span className="text-slate-900 font-medium">{village.precision || 'UNKNOWN'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Coordinates</span>
              <span className="text-slate-900 font-mono text-[10px]">
                {village.latitude?.toFixed(4)}°N, {village.longitude?.toFixed(4)}°E
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Mapped / Unmapped</span>
              <span className="text-slate-900 font-medium">
                {village.mappedCount || 0} / {village.unmappedCount || 0}
              </span>
            </div>
          </div>

          {/* Sector Breakdown */}
          {sectorEntries.length > 0 && (
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/80 text-xs">
              <div className="text-slate-600 font-bold mb-2">Sector Breakdown</div>
              <div className="space-y-1.5">
                {sectorEntries.map(([sector, count]) => {
                  const pct = ((count / village.msmeCount) * 100).toFixed(0);
                  return (
                    <div key={sector} className="flex items-center gap-2">
                      <div className="flex-1 text-slate-700">{sector.replace(/_/g, ' ')}</div>
                      <div className="text-slate-900 font-semibold">{count}</div>
                      <div className="text-slate-400 w-10 text-right">{pct}%</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export function EcosystemIntelligenceMap({
  graphData,
  loadingState,
  error,
  className = '',
  onAutoDetectLocation = null,
  isDetectingLocation = false,
  targetLocationName = null,
}) {
  const { isBanker } = useViewMode();
  const containerRef = useRef(null);

  // State (Defaults to Light Mode / Google Maps)
  const [selectedVillage, setSelectedVillage] = useState(null);
  const [tileStyle, setTileStyle] = useState('GOOGLE_STREETS');
  const [showLegend, setShowLegend] = useState(true);
  const [showUnmapped, setShowUnmapped] = useState(false);

  /* STEP2: State for enterprise-level features (preserved for future steps)
  const [projection, setProjection] = useState('geographic');
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [showFilters, setShowFilters] = useState(false);
  const [showLayersMenu, setShowLayersMenu] = useState(false);
  const [temporalFilter, setTemporalFilter] = useState(null);
  const [activeLayers, setActiveLayers] = useState({
    catchmentRings: true,
    nodes: true,
    relationships: true,
    density: false,
    opportunities: true,
  });
  const [filters, setFilters] = useState({
    showEdges: true,
    edgeTypes: [],
    sectors: [],
  });
  */

  // Dimensions
  const [dims, setDims] = useState({ width: 800, height: 500 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(entries => {
      const { width } = entries[0].contentRect;
      setDims({ width: Math.max(400, width), height: Math.max(350, Math.min(width * 0.6, 600)) });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // Extract data
  const data = graphData || {};
  const villageDensity = data.villageDensity || [];
  const unmapped = data.unmappedEntities || [];
  const catchment = data.catchment || {};
  const metrics = data.metrics || {};
  const warnings = data.warnings || [];
  const intent = data.intent || {};

  // Derived stats
  const totalVillageMsmes = useMemo(
    () => villageDensity.reduce((s, v) => s + v.msmeCount, 0),
    [villageDensity]
  );
  const highestDensityVillage = useMemo(
    () => villageDensity.length > 0 ? villageDensity[0] : null,
    [villageDensity]
  );

  // ── Loading/Error States (Light Mode) ─────────────────────────────────────

  if (loadingState === STATE_CODES.LOADING) {
    return (
      <div className={`bg-white rounded-2xl border border-slate-200 shadow-card p-8 ${className}`}>
        <div className="flex flex-col items-center justify-center gap-3 py-12">
          <Loader2 size={32} className="text-indigo-600 animate-spin" />
          <p className="text-slate-800 text-sm font-semibold">Generating Grad-CAM MSME Density Surface...</p>
          <p className="text-slate-500 text-xs">Computing continuous spatial activation from village-level enterprise records</p>
        </div>
      </div>
    );
  }

  if (loadingState === STATE_CODES.ERROR || error) {
    return (
      <div className={`bg-white rounded-2xl border border-red-200 shadow-card p-8 ${className}`}>
        <div className="flex flex-col items-center justify-center gap-3 py-8">
          <AlertCircle size={28} className="text-red-500" />
          <p className="text-red-700 text-sm font-bold">Failed to load MSME density data</p>
          <p className="text-slate-600 text-xs max-w-md text-center">{error || 'An unexpected error occurred.'}</p>
        </div>
      </div>
    );
  }

  if (!villageDensity.length && !unmapped.length) {
    return (
      <div className={`bg-white rounded-2xl border border-slate-200 shadow-card p-8 ${className}`}>
        <div className="flex flex-col items-center justify-center gap-3 py-8">
          <Map size={28} className="text-slate-400" />
          <p className="text-slate-600 text-sm font-medium">No MSME registration data available for density visualization</p>
        </div>
      </div>
    );
  }

  // ── Main Render (Light Mode by Default) ───────────────────────────────────

  return (
    <div className={`bg-white rounded-2xl border border-slate-200 shadow-card overflow-hidden relative ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50/80">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-2xs">
            <Map size={16} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 font-outfit">
              {isBanker ? 'Grad-CAM MSME Registration Density Heatmap' : 'MSME Density Heatmap'}
            </h3>
            <p className="text-xs text-slate-500">
              {intent.displayName || 'Enterprise'} catchment • {villageDensity.length} village clusters • {totalVillageMsmes.toLocaleString('en-IN')} MSMEs
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onAutoDetectLocation && (
            <button
              onClick={onAutoDetectLocation}
              disabled={isDetectingLocation}
              aria-label="Auto-Detect My GPS Location"
              title="Auto-Detect My GPS Location and query surrounding MSMEs"
              className={`p-1.5 px-2.5 rounded-lg border text-xs font-bold transition-all flex items-center gap-1.5 shadow-2xs ${
                isDetectingLocation
                  ? 'bg-sky-100 border-sky-300 text-sky-800'
                  : 'border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-100 hover:text-sky-900'
              }`}
            >
              <Crosshair size={14} className={isDetectingLocation ? 'animate-spin text-sky-600' : 'text-sky-600'} />
              <span className="hidden sm:inline">{isDetectingLocation ? 'Locating...' : 'Auto-Detect'}</span>
            </button>
          )}

          <button
            onClick={() => setShowLegend(!showLegend)}
            aria-label="Toggle Grad-CAM Scale"
            title="Grad-CAM Activation Scale"
            className={`p-1.5 rounded-lg border text-xs font-medium transition-colors ${
              showLegend
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700 shadow-2xs'
                : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Eye size={14} />
          </button>

          {unmapped.length > 0 && (
            <button
              onClick={() => setShowUnmapped(!showUnmapped)}
              aria-label={`${unmapped.length} unmapped enterprises with unresolved coordinates`}
              title={`${unmapped.length} unmapped enterprises`}
              className={`p-1.5 rounded-lg border text-xs font-medium transition-colors ${
                showUnmapped
                  ? 'bg-amber-50 border-amber-200 text-amber-700 shadow-2xs'
                  : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <AlertTriangle size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Main visualization area */}
      <div className="relative" ref={containerRef}>
        <LeafletHeatmapView
          villageDensity={villageDensity}
          catchment={catchment}
          width={dims.width}
          height={dims.height}
          tileStyle={tileStyle}
          onTileStyleChange={setTileStyle}
          selectedVillage={selectedVillage}
          onVillageClick={setSelectedVillage}
          targetLocationName={targetLocationName || data?.catchment?.village || data?.summary?.targetVillage}
        />

        {/* Grad-CAM Legend overlay */}
        {showLegend && (
          <GradCamLegend villageDensity={villageDensity} />
        )}

        {/* Village detail panel */}
        <VillageDetailPanel
          village={selectedVillage}
          onClose={() => setSelectedVillage(null)}
        />
      </div>

      {/* Density Metrics Ribbon (Light Theme) */}
      <div className="px-4 py-3 border-t border-slate-200 bg-slate-50/50">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
          <MetricCard
            label="Village Clusters"
            value={villageDensity.length}
            icon={MapPin}
          />
          <MetricCard
            label="Total Catchment MSMEs"
            value={totalVillageMsmes.toLocaleString('en-IN')}
            icon={Building2}
          />
          <MetricCard
            label="Unmapped Localities"
            value={unmapped.length}
            icon={AlertTriangle}
          />
          <MetricCard
            label="Peak Activation Hub"
            value={highestDensityVillage ? `${highestDensityVillage.villageName} (${highestDensityVillage.msmeCount})` : '—'}
            icon={BarChart3}
          />
          {metrics.hhi && (
            <MetricCard
              label={isBanker ? 'HHI Saturation' : 'Competition'}
              value={isBanker ? metrics.hhi.value : metrics.hhi.interpretation}
              icon={Users}
            />
          )}
        </div>
      </div>

      {/* Warnings (Light Theme) */}
      {warnings.length > 0 && (
        <div className="px-4 py-3 border-t border-slate-200 bg-white">
          <div className="space-y-2">
            {(isBanker ? warnings : warnings.filter(w => w.severity === 'WARNING')).map((w, i) => (
              <div
                key={i}
                className={`flex items-start gap-2 p-2.5 rounded-lg border text-xs ${
                  w.severity === 'WARNING'
                    ? 'bg-amber-50 border-amber-200 text-amber-900'
                    : 'bg-blue-50 border-blue-200 text-blue-900'
                }`}
              >
                {w.severity === 'WARNING' ? <AlertTriangle size={14} className="mt-0.5 flex-shrink-0 text-amber-600" /> : <Info size={14} className="mt-0.5 flex-shrink-0 text-blue-600" />}
                <span>{w.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unmapped entities panel (Light Theme) */}
      {showUnmapped && unmapped.length > 0 && (
        <div className="px-4 py-3 border-t border-slate-200 bg-amber-50/40">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-amber-600" />
            <span className="text-xs font-bold text-amber-900">Unmapped Enterprises ({unmapped.length})</span>
          </div>
          <div className="max-h-40 overflow-y-auto space-y-1.5">
            {unmapped.map((u, i) => (
              <div key={i} className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 text-xs">
                <span className="text-slate-800 font-medium truncate flex-1">{u.enterpriseName || 'Unknown'}</span>
                <span className="text-slate-500 font-mono ml-2">{u.pincode || '—'}</span>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-amber-700/80 mt-2">
            These enterprises could not be placed on the map due to missing or unresolvable geographic coordinates.
          </p>
        </div>
      )}

      {/* Provenance footer (banker only) */}
      {isBanker && data.provenance && (
        <div className="px-4 py-2 border-t border-slate-200 bg-slate-50 text-[10px] text-slate-500 flex items-center justify-between">
          <span>Engine: {data.provenance.engine} • Schema: {data.schemaVersion}</span>
          <span>{data.provenance.generatedAt?.substring(0, 19)?.replace('T', ' ')} UTC</span>
        </div>
      )}
    </div>
  );
}

export default EcosystemIntelligenceMap;


/* ═══════════════════════════════════════════════════════════════════════════
 * STEP 2+ PRESERVED CODE — Enterprise Nodes, Edges, Force Layout
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * The following code blocks are the original enterprise-level visualization
 * features. They have been commented out (not deleted) for Step 1, which
 * only shows the village-level MSME density heatmap.
 *
 * Re-enable these incrementally in Step 2 (enterprise nodes), Step 3
 * (relationship edges), Step 4 (topological view), etc.
 *
 * ─── Helpers ─────────────────────────────────────────────────────────────
 *
 * function projectGeo(lat, lon, bounds, width, height) { ... }
 * function computeBounds(nodes) { ... }
 * function forceLayout(nodes, edges, width, height) { ... }
 *
 * ─── Sub-components ─────────────────────────────────────────────────────
 *
 * function StatusBadge({ status, className }) { ... }
 * function WarningPanel({ warnings }) { ... }
 * function NodeDetailPanel({ node, onClose, isBanker }) { ... }
 *
 * ─── LeafletMapView (enterprise-node mode) ──────────────────────────────
 *
 * function LeafletMapView({
 *   nodes, edges, unmapped, catchment, filters,
 *   selectedNode, hoveredNode, onNodeClick, onNodeHover,
 *   width, height, isBanker, temporalFilter, activeLayers,
 *   layers, tileStyle, onTileStyleChange,
 * }) { ... }
 *
 * ─── MapCanvas (force-directed Canvas renderer) ─────────────────────────
 *
 * function MapCanvas({
 *   nodes, edges, unmapped, catchment, projection, filters, zoom, pan,
 *   selectedNode, onNodeClick, onNodeHover, hoveredNode,
 *   width, height, isBanker, temporalFilter, activeLayers, layers,
 * }) { ... }
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */
