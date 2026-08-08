import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

const AddressInput = ({ onSubmit, isLoading }) => {
  const [address, setAddress] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (address.trim()) {
      onSubmit(address);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="glass-panel">
      <div className="header" style={{ marginBottom: '16px' }}>
        <h1>Address Parser</h1>
        <p>Enter any messy Indian address</p>
      </div>
      
      <form onSubmit={handleSubmit} className="input-group">
        <label className="input-label" htmlFor="address-input">
          Raw Address String
        </label>
        <textarea
          id="address-input"
          className="textarea-field"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g., Flat 302, Sai Residency, near Post Office, Madhapur, Hyderabad 500081"
          disabled={isLoading}
        />
        <button 
          type="submit" 
          className="submit-btn"
          disabled={isLoading || !address.trim()}
        >
          {isLoading ? (
            <>
              <Loader2 className="loader" size={18} />
              Parsing...
            </>
          ) : (
            <>
              <Search size={18} />
              Geocode & Analyze
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default AddressInput;
