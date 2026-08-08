import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

const customIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Component to handle dynamic panning
const MapUpdater = ({ position, zoom }) => {
  const map = useMap();
  useEffect(() => {
    if (map && position) {
      map.setView(position, zoom, { animate: true });
    }
  }, [map, position, zoom]);
  return null;
};

const MapView = ({ latitude, longitude, areaInfo }) => {
  // Default center (India)
  const defaultCenter = [20.5937, 78.9629];
  const position = (latitude && longitude) ? [latitude, longitude] : null;
  const mapCenter = position || defaultCenter;
  const zoom = position ? 15 : 5;

  return (
    <div style={{ height: '100%', width: '100%', borderRadius: '12px', overflow: 'hidden' }}>
      <MapContainer 
        center={mapCenter} 
        zoom={zoom} 
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapUpdater position={position || defaultCenter} zoom={zoom} />
        
        {position && (
          <Marker position={position} icon={customIcon}>
            <Popup>
              <strong>{areaInfo || 'Matched Location'}</strong>
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
};

export default MapView;
