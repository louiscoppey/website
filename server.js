const express = require('express');
const path = require('path');
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

// Spotify API endpoint (for desktop only)
app.get('/api/spotify-playlist/:playlistId', async (req, res) => {
  try {
    // For now, return static data to avoid fetch issues
    const tracks = [
      { artist: 'Franz Schubert, Maurizio Pollini', title: 'Piano Sonata No. 18 in G Major, D. 894: I. Molto moderato e cantabile', spotifyUrl: 'https://open.spotify.com/track/0hfnkmV7KryBL6prIBG2pv' },
      { artist: 'Esbjörn Svensson Trio', title: 'In My Garage', spotifyUrl: 'https://open.spotify.com/track/5XikEwYFSwGIfNd5XYgj8L' },
      { artist: 'Esbjörn Svensson Trio', title: 'Waltz for the Lonely Ones', spotifyUrl: 'https://open.spotify.com/track/4JEADljWBThk6rIUjdnG9S' }
    ];
    
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