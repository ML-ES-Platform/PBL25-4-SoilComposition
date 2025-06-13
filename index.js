const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');

const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());

const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'iot_data',
    password: 'postgres',
    port: 5432,
});

app.post('/moisture', async (req, res) => {
    const { device_id, moisture_value } = req.body;
    try {
        await pool.query(
            'INSERT INTO moisture_data (device_id, moisture_value) VALUES ($1, $2)',
            [device_id, moisture_value]
        );
        res.status(201).send('Moisture data inserted');
    } catch (err) {
        console.error(err);
        res.status(500).send('Error inserting data');
    }
});

app.get('/moisture', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM moisture_data ORDER BY timestamp DESC');
        res.status(200).json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).send('Error fetching data');
    }
});

app.listen(port, () => {
    console.log(`Server listening on http://localhost:${port}`);
});
