import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';

interface GraphData {
  value: number | null;
  timestamp: string;
}

const GraphLast7D: React.FC = () => {
  const [data, setData] = useState<GraphData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:3000/api/moisture/sensor1/last7d');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result: GraphData[] = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Failed to fetch Last 7D data');
        console.error(err);
      }
    };
    fetchData();
  }, []);

  const chartData = {
    labels: data.map(d => d.timestamp),
    datasets: [
      {
        label: 'Moisture (%)',
        data: data.map(d => d.value),
        borderColor: 'rgba(255, 159, 64, 1)',
        backgroundColor: 'rgba(255, 159, 64, 0.2)',
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' as const },
      title: { display: true, text: 'Last 7 Days' },
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

export default GraphLast7D;