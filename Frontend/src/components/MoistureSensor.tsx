import React, { useState, useEffect } from 'react';

interface MoistureData {
  last_hour: number | null;
  current: number | null;
  next_hour: number | null;
}

interface SensorProps {
  deviceId: string;
}

const MoistureSensor: React.FC<SensorProps> = ({ deviceId }) => {
  const [data, setData] = useState<MoistureData>({ last_hour: null, current: null, next_hour: null });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!deviceId) return; // Don't fetch if no device is selected

    const fetchData = async () => {
      try {
        const response = await fetch(`http://localhost:3000/api/moisture/${deviceId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result: MoistureData = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Failed to fetch moisture data');
        console.error(err);
      }
    };

    fetchData();
    // Set up a polling interval to refresh the data every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);

  }, [deviceId]); // Re-run the effect if the deviceId changes

  return (
    <div className="moisture-sensor">
      <h2>Moisture Readings</h2>
      <div className="moisture-fields">
        <div className="field">
          <p className="field-label">Last Hour:</p>
          <p className="field-value small">
            {data.last_hour !== null ? `${data.last_hour}%` : 'N/A'}
          </p>
        </div>
        <div className="field">
          <p className="field-label">Current:</p>
          <p className="field-value large">
            {data.current !== null ? `${data.current}%` : 'N/A'}
          </p>
        </div>
        <div className="field">
          <p className="field-label">Next Hour:</p>
          <p className="field-value small">
            {data.next_hour !== null ? `${data.next_hour}%` : 'N/A'}
          </p>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
};

export default MoistureSensor;