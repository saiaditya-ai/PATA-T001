import React, { useEffect } from 'react';
import { APIProvider, Map, AdvancedMarker, useMap } from '@vis.gl/react-google-maps';

// Component to handle dynamic panning
const MapUpdater = ({ position }) => {
  const map = useMap();
  useEffect(() => {
    if (map && position) {
      map.panTo(position);
      map.setZoom(15);
    }
  }, [map, position]);
  return null;
};

const MapView = ({ latitude, longitude, areaInfo }) => {
  // Default center (India)
  const defaultCenter = { lat: 20.5937, lng: 78.9629 };
  const position = (latitude && longitude) ? { lat: latitude, lng: longitude } : null;
  const mapCenter = position || defaultCenter;
  const zoom = position ? 15 : 5;

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

  if (!apiKey) {
    return (
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f0f0', borderRadius: '12px' }}>
        <p style={{ color: '#666', textAlign: 'center' }}>
          <strong>Google Maps API Key Missing</strong><br/>
          Please set VITE_GOOGLE_MAPS_API_KEY in frontend/.env
        </p>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', width: '100%', borderRadius: '12px', overflow: 'hidden' }}>
      <APIProvider apiKey={apiKey}>
        <Map
          defaultCenter={mapCenter}
          defaultZoom={zoom}
          mapId="DEMO_MAP_ID"
          disableDefaultUI={true}
        >
          <MapUpdater position={position} />
          
          {position && (
            <AdvancedMarker position={position} title="High-Confidence Pin">
              <div style={{
                background: 'rgba(34, 197, 94, 0.9)',
                color: 'white',
                padding: '6px 12px',
                borderRadius: '8px',
                fontWeight: 'bold',
                boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                border: '2px solid white'
              }}>
                📍 {areaInfo || 'Matched Location'}
              </div>
            </AdvancedMarker>
          )}
        </Map>
      </APIProvider>
    </div>
  );
};

export default MapView;
