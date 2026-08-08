import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, MapPin, Building, Hash } from 'lucide-react';

const EvidenceCard = ({ validation, parsedData, geocoding }) => {
  if (!validation) return null;

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'score-high';
    if (score >= 0.5) return 'score-medium';
    return 'score-low';
  };

  const getScoreIcon = (score) => {
    if (score >= 0.8) return <CheckCircle2 size={16} />;
    if (score >= 0.5) return <AlertTriangle size={16} />;
    return <XCircle size={16} />;
  };

  return (
    <div className="glass-panel evidence-card">
      <div className={`score-badge ${getScoreColor(validation.confidence_score)}`}>
        {getScoreIcon(validation.confidence_score)}
        <span style={{ marginLeft: '6px' }}>
          {Math.round(validation.confidence_score * 100)}% Confidence
        </span>
      </div>

      <div className="justification-text">
        {validation.evidence_justification}
      </div>

      <div className="details-grid">
        {parsedData?.parser_used && (
          <div className="detail-item">
            <span className="detail-label">Parser Engine</span>
            <span className="detail-value">
              <Hash size={14} className="text-muted" /> 
              {parsedData.parser_used}
            </span>
          </div>
        )}
        
        {geocoding?.matched_area && (
          <div className="detail-item">
            <span className="detail-label">Matched Area</span>
            <span className="detail-value">
              <MapPin size={14} className="text-muted" /> 
              {geocoding.matched_area}
            </span>
          </div>
        )}
        
        {geocoding?.matched_landmark && (
          <div className="detail-item">
            <span className="detail-label">Matched Landmark</span>
            <span className="detail-value">
              <Building size={14} className="text-muted" /> 
              {geocoding.matched_landmark}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvidenceCard;
