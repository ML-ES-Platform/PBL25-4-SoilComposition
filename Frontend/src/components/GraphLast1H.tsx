import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { ChartData } from 'chart.js';

interface GraphProps {
    deviceId: string;
}

const GraphLast1H: React.FC<GraphProps> = ({ deviceId }) => {
    const [chartData, setChartData] = useState<ChartData<'line'>>({
        labels: [],
        datasets: [{
            label: 'Moisture (%)',
            data: [],
            borderColor: 'rgba(75, 192, 192, 1)',
            fill: false,
        }],
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`http://localhost:3000/api/moisture/${deviceId}/last1h`);
                const data = await response.json();

                setChartData({
                    labels: data.map((item: any) => item.timestamp),
                    datasets: [{
                        label: 'Moisture (%)',
                        data: data.map((item: any) => item.value),
                        borderColor: 'rgba(75, 192, 192, 1)',
                        fill: false,
                    }]
                });
            } catch (error) {
                console.error("Error fetching last 1 hour data:", error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds
        return () => clearInterval(interval);

    }, [deviceId]);

    return (
        <div className="graph-box">
            <h3>Last 1 Hour</h3>
            <Line data={chartData} />
        </div>
    );
};

export default GraphLast1H;