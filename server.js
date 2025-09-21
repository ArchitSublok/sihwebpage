// backend/server.js

const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 5001; // Using a fixed port since we have no .env file

// Middleware
app.use(cors());
app.use(express.json()); // Essential for parsing form data

// --- API Endpoints ---

// Handles signup form submission
app.post('/api/signup', (req, res) => {
  console.log('Received signup data:', req.body);
  res.json({ success: true, message: 'Signup data received by server!' });
});

// Handles login form submission
app.post('/api/login', (req, res) => {
  console.log('Received login data:', req.body);
  res.json({ success: true, message: 'Login data received by server!' });
});

// Handles contact form submission
app.post('/api/contact', (req, res) => {
  console.log('Received contact message:', req.body);
  res.json({ success: true, message: 'Contact message received by server!' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Simplified server running on http://localhost:${PORT}`);
});
