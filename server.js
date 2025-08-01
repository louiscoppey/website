const express = require('express');
const path = require('path');
const fetch = require('node-fetch');
const app = express();
const port = 3000;

// Enable CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

// Add logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Spotify API endpoint
app.get('/api/spotify-playlist/:playlistId', async (req, res) => {
  try {
    const playlistId = req.params.playlistId;
    const clientId = '7529230155e74e30af35529874cb8fef';
    const clientSecret = 'e3a769eed628419ca4af050290f5311f';
    
    // Get access token
    const tokenResponse = await fetch('https://accounts.spotify.com/api/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + Buffer.from(clientId + ':' + clientSecret).toString('base64')
      },
      body: 'grant_type=client_credentials'
    });
    
    if (!tokenResponse.ok) {
      throw new Error('Authentication failed');
    }
    
    const tokenData = await tokenResponse.json();
    const accessToken = tokenData.access_token;
    
    // Fetch playlist data
    const response = await fetch(`https://api.spotify.com/v1/playlists/${playlistId}/tracks`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Playlist not accessible');
    }
    
    const data = await response.json();
    const tracks = data.items.map(item => ({
      artist: item.track.artists.map(artist => artist.name).join(', '),
      title: item.track.name,
      spotifyUrl: item.track.external_urls.spotify
    }));
    
    res.json(tracks);
  } catch (error) {
    console.error('Spotify API error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Servir les fichiers statiques
app.use(express.static(__dirname));

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
  console.log('Serving files from:', __dirname);
}); 