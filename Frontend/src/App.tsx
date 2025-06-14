import { useState, useEffect } from 'react';
import './App.css';
import MoistureSensor from './components/MoistureSensor';
import GraphsField from './components/GraphsField';
import Header from "./components/Header";

function App() {
    const [sensors, setSensors] = useState<string[]>([]);
    const [selectedSensor, setSelectedSensor] = useState<string>('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetch('http://localhost:3000/api/sensors')
            .then(res => {
                if (!res.ok) {
                    throw new Error('Failed to fetch sensors');
                }
                return res.json();
            })
            .then(data => {
                if (data && data.length > 0) {
                    setSensors(data);
                    setSelectedSensor(data[0]);
                } else {
                    setError('No sensors found. Waiting for data...');
                }
            })
            .catch(error => {
                console.error("Failed to fetch sensors:", error);
                setError('Could not connect to the server or no sensors are available.');
            });
    }, []);

    return (
        <div className="dashboard-container">
            <Header />
            <div className="sensor-selector-container">
                <label htmlFor="sensor-selector">Select Sensor:</label>
                <select 
                    id="sensor-selector"
                    value={selectedSensor} 
                    onChange={e => setSelectedSensor(e.target.value)}
                    disabled={sensors.length === 0}
                >
                    {sensors.length > 0 ? (
                        sensors.map(sensorId => (
                            <option key={sensorId} value={sensorId}>
                                {sensorId}
                            </option>
                        ))
                    ) : (
                        <option>{error || 'Loading sensors...'}</option>
                    )}
                </select>
            </div>

            {selectedSensor ? (
                <div className="dashboard-grid">
                    <MoistureSensor deviceId={selectedSensor} />
                    <GraphsField deviceId={selectedSensor} />
                </div>
            ) : (
                <div className="loading-message">
                    <p>{error || 'Waiting for sensor selection...'}</p>
                </div>
            )}
        </div>
    );
}

export default App;