import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';

interface GraphData {
  value: number | null;
  timestamp: string;
}

interface GraphProps {
  deviceId: string;
}

const GraphNext12H: React.FC<GraphProps> = ({ deviceId }) => {
  const [data, setData] = useState<GraphData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!deviceId) return;

    const fetchData = async () => {
      try {
        const response = await fetch(`http://localhost:3000/api/moisture/${deviceId}/next12h`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result: GraphData[] = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Failed to fetch Next 12H data');
        console.error(err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);

  }, [deviceId]);

  const chartData = {
    labels: data.map(d => d.timestamp),
    datasets: [
      {
        label: 'Moisture (%)',
        data: data.map(d => d.value),
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' as const },
      title: { display: true, text: 'Next 12 Hours' },
    },
    scales: {
      y: { beginAtZero: false, title: { display: true, text: 'Moisture (%)' } },
    },
  };

  return (
    <div className="graph-box">
      {error ? <p className="error">{error}</p> : <Line data={chartData} options={chartOptions} />}
    </div>
  );
};

export default GraphNext12H;