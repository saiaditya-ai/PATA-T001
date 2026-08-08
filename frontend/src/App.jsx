import React, { useState } from 'react';
import AddressInput from './components/AddressInput';
import EvidenceCard from './components/EvidenceCard';
import MapView from './components/MapView';
import { geocodeAddress } from './api/client';
import { MapPin } from 'lucide-react';
import './index.css';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAddressSubmit = async (address) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const data = await geocodeAddress(address);
      setResult(data);
    } catch (err) {
      setError("Failed to geocode address. Please ensure the backend is running.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <div style={{ background: 'var(--primary)', padding: '8px', borderRadius: '12px', display: 'flex' }}>
            <MapPin color="white" size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, background: 'linear-gradient(to right, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Pata AI
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Address Intelligence
            </p>
          </div>
        </div>

        <AddressInput onSubmit={handleAddressSubmit} isLoading={isLoading} />
        
        {error && (
          <div className="glass-panel" style={{ borderLeft: '4px solid var(--danger)' }}>
            <p style={{ color: 'var(--danger)', fontSize: '0.9rem', margin: 0 }}>{error}</p>
          </div>
        )}

        {result && (
          <EvidenceCard 
            validation={result.validation} 
            parsedData={result.parsed_address}
            geocoding={result.geocoding}
          />
        )}
      </div>
      
      <div className="map-container">
        <MapView 
          latitude={result?.geocoding?.latitude}
          longitude={result?.geocoding?.longitude}
          areaInfo={result?.geocoding?.matched_landmark || result?.geocoding?.matched_area}
        />
      </div>
    </div>
  );
}

export default App;
