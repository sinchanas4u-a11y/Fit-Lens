import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ActivityIndicator, Text } from 'react-native';
import { WebView } from 'react-native-webview';
import RNFS from 'react-native-fs';
import { Colors } from '../../constants/colors';

const MeshViewer = ({ meshData }) => {
  const [plotlyJs, setPlotlyJs] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPlotlyAsset();
  }, []);

  const loadPlotlyAsset = async () => {
    try {
      const js = await RNFS.readFileAssets('plotly.min.js', 'utf8');
      setPlotlyJs(js);
    } catch (e) {
      console.log('Error reading plotly.min.js asset:', e);
    } finally {
      setLoading(false);
    }
  };

  const buildHtml = () => {
    if (!meshData || !plotlyJs) {
      return '<html><body style="background:#0a0e27;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;"><h3>3D Mesh Data Unavailable</h3></body></html>';
    }

    return `
      <!DOCTYPE html><html>
      <head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
          *{margin:0;padding:0}
          body{background:#0a0e27;width:100vw;height:100vh;overflow:hidden}
          #p{width:100%;height:100%}
        </style>
        <script>${plotlyJs}</script>
      </head>
      <body>
        <div id="p"></div>
        <script>
          var x = ${JSON.stringify(meshData.x || [])};
          var y = ${JSON.stringify(meshData.y || [])};
          var z = ${JSON.stringify(meshData.z || [])};
          Plotly.newPlot('p', [{
            type: 'mesh3d',
            x: x, y: z, z: y.map(function(v){ return -v; }),
            i: ${JSON.stringify(meshData.i || [])},
            j: ${JSON.stringify(meshData.j || [])},
            k: ${JSON.stringify(meshData.k || [])},
            colorscale: [[0, '#004d40'], [0.5, '#00d4aa'], [1, '#80cbc4']],
            intensity: y,
            showscale: false,
            opacity: 1,
            lighting: { ambient: 0.6, diffuse: 0.9, specular: 0.4 },
            lightposition: { x: 1000, y: 1000, z: 2000 }
          }], {
            paper_bgcolor: '#0a0e27',
            margin: { l: 0, r: 0, t: 0, b: 0 },
            scene: {
              bgcolor: '#0a0e27',
              xaxis: { visible: false },
              yaxis: { visible: false },
              zaxis: { visible: false },
              camera: { eye: { x: 0, y: -2.5, z: 0.5 }, up: { x: 0, y: 0, z: 1 } },
              aspectmode: 'data'
            },
            dragmode: 'orbit'
          }, { responsive: true, displayModeBar: false, scrollZoom: true });
        </script>
      </body>
      </html>`;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.accent} />
        <Text style={styles.loadingText}>Initializing 3D Mesh Engine...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <WebView
        source={{ html: buildHtml() }}
        style={{ flex: 1 }}
        javaScriptEnabled
        domStorageEnabled
        scrollEnabled={false}
        originWhitelist={['*']}
        backgroundColor="#0a0e27"
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 350,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: Colors.primary,
  },
  loadingContainer: {
    height: 350,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.primary,
  },
  loadingText: {
    color: Colors.textSecondary,
    fontSize: 13,
    marginTop: 12,
  },
});

export default MeshViewer;
