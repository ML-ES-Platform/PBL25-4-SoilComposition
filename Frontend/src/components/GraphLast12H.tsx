import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface GraphData {
  value: number | null;
  timestamp: string;
}

const GraphLast12H: React.FC = () => {
  const [data, setData] = useState<GraphData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/moisture/sensor1/last12h');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result: GraphData[] = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Failed to fetch Last 12H data');
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
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' as const },
      title: { display: true, text: 'Last 12 Hours' },
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

export default GraphLast12H;