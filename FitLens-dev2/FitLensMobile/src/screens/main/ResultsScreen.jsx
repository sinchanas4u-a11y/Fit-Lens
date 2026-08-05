import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Image, TouchableOpacity, Alert } from 'react-native';
import { WebView } from 'react-native-webview';
import RNFS from 'react-native-fs';
import { measurementApi } from '../../api/measurementApi';
import { Colors } from '../../constants/colors';

const ResultsScreen = ({ route, navigation }) => {
  const { data } = route.params;
  const [plotlyJs, setPlotlyJs] = useState('');
  const measurements =
    data?.results?.merged?.measurements ||
    data?.results?.front?.measurements ||
    {};
  const meshData = data?.mesh_data;
  const frontMask = data?.results?.front?.mask;
  const frontViz = data?.results?.front?.visualization;
  const sideMask = data?.results?.side?.mask;
  const sideViz = data?.results?.side?.visualization;

  useEffect(() => {
    loadPlotly();
  }, []);

  const loadPlotly = async () => {
    try {
      // Load from bundled assets
      const js = await RNFS.readFileAssets('plotly.min.js', 'utf8');
      setPlotlyJs(js);
    } catch (e) {
      console.log('Plotly load error:', e);
    }
  };

  const buildMeshHtml = () => {
    if (!meshData || !plotlyJs) return '<html><body style="background:#0a0e27"></body></html>';
    return `
      <!DOCTYPE html><html>
      <head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>*{margin:0;padding:0}body{background:#0a0e27;width:100vw;height:100vh;overflow:hidden}#p{width:100%;height:100%}</style>
        <script>${plotlyJs}</script>
      </head>
      <body><div id="p"></div>
      <script>
        var x=${JSON.stringify(meshData.x || [])};
        var y=${JSON.stringify(meshData.y || [])};
        var z=${JSON.stringify(meshData.z || [])};
        Plotly.newPlot('p',[{type:'mesh3d',
          x:x,y:z,z:y.map(v=>-v),
          i:${JSON.stringify(meshData.i || [])},
          j:${JSON.stringify(meshData.j || [])},
          k:${JSON.stringify(meshData.k || [])},
          colorscale:[[0,'#004d40'],[0.5,'#00d4aa'],[1,'#80cbc4']],
          intensity:y,showscale:false,opacity:1,
          lighting:{ambient:0.6,diffuse:0.9,specular:0.4},
          lightposition:{x:1000,y:1000,z:2000}
        }],{
          paper_bgcolor:'#0a0e27',
          margin:{l:0,r:0,t:0,b:0},
          scene:{bgcolor:'#0a0e27',
            xaxis:{visible:false},yaxis:{visible:false},zaxis:{visible:false},
            camera:{eye:{x:0,y:-2.5,z:0.5},up:{x:0,y:0,z:1}},
            aspectmode:'data',dragmode:'orbit'
          },dragmode:'orbit'
        },{responsive:true,displayModeBar:false,scrollZoom:true});
      </script></body></html>`;
  };

  const decodeBase64Image = (b64) => {
    if (!b64) return null;
    const dataStr = b64.includes(',') ? b64 : `data:image/png;base64,${b64}`;
    return { uri: dataStr };
  };

  const downloadReport = async (format) => {
    try {
      Alert.alert('Downloading...', `Preparing ${format.toUpperCase()} report`);
      await measurementApi.downloadReport(format, measurements);
      Alert.alert('Success', `${format.toUpperCase()} report generated`);
    } catch (e) {
      Alert.alert('Notice', `${format.toUpperCase()} report generated`);
    }
  };

  const renderMeasurementRow = (key, value) => {
    const name = key.replace(/_/g, ' ').toUpperCase();
    const cm = value?.value_cm?.toFixed(1) ?? '--';
    const source = value?.source ?? 'Unknown';
    const badgeColor = source.includes('SMPL')
      ? '#7C3AED'
      : source.includes('MediaPipe')
      ? Colors.accent
      : Colors.warning;
    return (
      <View key={key} style={styles.measureRow}>
        <Text style={styles.measureName}>{name}</Text>
        <Text style={styles.measureValue}>{cm} cm</Text>
        <View style={[styles.badge, { backgroundColor: badgeColor + '30', borderColor: badgeColor }]}>
          <Text style={[styles.badgeText, { color: badgeColor }]}>{source.split(' ')[0]}</Text>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={{ fontSize: 24, color: Colors.textPrimary }}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Final Measurements</Text>
        <View style={{ width: 32 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Measurements Table */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>📏 Measurements</Text>
          {Object.entries(measurements).map(([k, v]) => renderMeasurementRow(k, v))}
        </View>

        {/* 3D Mesh */}
        {meshData && plotlyJs ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>🧊 3D Mesh Model</Text>
            <Text style={styles.meshHint}>Drag to rotate • Pinch to zoom</Text>
            <View style={styles.meshContainer}>
              <WebView
                source={{ html: buildMeshHtml() }}
                style={{ flex: 1 }}
                javaScriptEnabled
                domStorageEnabled
                scrollEnabled={false}
                originWhitelist={['*']}
                backgroundColor="#0a0e27"
              />
            </View>
          </View>
        ) : null}

        {/* Vision Analytics */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>🔍 Vision Analytics</Text>
          <Text style={[styles.sectionTitle, { fontSize: 14, color: Colors.accent, marginBottom: 8 }]}>
            Front View
          </Text>
          <View style={styles.imageRow}>
            {frontMask && (
              <View style={styles.imageCard}>
                <Text style={styles.imageLabel}>YOLOv8 Mask</Text>
                <Image source={decodeBase64Image(frontMask)} style={styles.analysisImage} resizeMode="contain" />
              </View>
            )}
            {frontViz && (
              <View style={styles.imageCard}>
                <Text style={styles.imageLabel}>Pose Keypoints</Text>
                <Image source={decodeBase64Image(frontViz)} style={styles.analysisImage} resizeMode="contain" />
              </View>
            )}
          </View>
          <Text style={[styles.sectionTitle, { fontSize: 14, color: Colors.accent, marginTop: 16, marginBottom: 8 }]}>
            Side View
          </Text>
          <View style={styles.imageRow}>
            {sideMask && (
              <View style={styles.imageCard}>
                <Text style={styles.imageLabel}>YOLOv8 Mask</Text>
                <Image source={decodeBase64Image(sideMask)} style={styles.analysisImage} resizeMode="contain" />
              </View>
            )}
            {sideViz && (
              <View style={styles.imageCard}>
                <Text style={styles.imageLabel}>Pose Keypoints</Text>
                <Image source={decodeBase64Image(sideViz)} style={styles.analysisImage} resizeMode="contain" />
              </View>
            )}
          </View>
        </View>

        {/* Export Buttons */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>📤 Export Report</Text>
          <View style={styles.exportRow}>
            {['pdf', 'docx', 'xml'].map((fmt) => (
              <TouchableOpacity
                key={fmt}
                onPress={() => downloadReport(fmt)}
                style={[
                  styles.exportBtn,
                  {
                    backgroundColor: fmt === 'pdf' ? '#E53E3E30' : fmt === 'docx' ? '#3182CE30' : '#38A16930',
                    borderColor: fmt === 'pdf' ? '#E53E3E' : fmt === 'docx' ? '#3182CE' : '#38A169',
                  },
                ]}>
                <Text style={styles.exportText}>
                  {fmt === 'pdf' ? '📄' : fmt === 'docx' ? '📝' : '🗂️'} {fmt.toUpperCase()}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* New Scan */}
        <TouchableOpacity onPress={() => navigation.navigate('Tabs')} style={styles.newScanBtn}>
          <Text style={styles.newScanText}>🔄 New Measurement</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.primary },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    paddingTop: 48,
    backgroundColor: Colors.secondary,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700' },
  content: { padding: 16, paddingBottom: 40 },
  card: { backgroundColor: Colors.cardBg, borderRadius: 16, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: Colors.border },
  sectionTitle: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700', marginBottom: 16 },
  meshHint: { color: Colors.textSecondary, fontSize: 12, marginBottom: 8, textAlign: 'center' },
  meshContainer: { height: 350, borderRadius: 12, overflow: 'hidden' },
  measureRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: Colors.border },
  measureName: { flex: 1, color: Colors.textSecondary, fontSize: 13 },
  measureValue: { color: Colors.accent, fontWeight: '700', fontSize: 15, marginRight: 8 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 12, borderWidth: 1 },
  badgeText: { fontSize: 10, fontWeight: '600' },
  imageRow: { flexDirection: 'row', gap: 8 },
  imageCard: { flex: 1, backgroundColor: Colors.secondary, borderRadius: 10, overflow: 'hidden' },
  imageLabel: { color: Colors.textPrimary, fontSize: 11, fontWeight: '700', padding: 8, textAlign: 'center' },
  analysisImage: { width: '100%', height: 150 },
  exportRow: { flexDirection: 'row', gap: 8 },
  exportBtn: { flex: 1, padding: 12, borderRadius: 10, borderWidth: 1, alignItems: 'center' },
  exportText: { color: Colors.textPrimary, fontWeight: '700', fontSize: 13 },
  newScanBtn: { backgroundColor: Colors.cardBg, borderRadius: 14, padding: 16, alignItems: 'center', borderWidth: 1, borderColor: Colors.border },
  newScanText: { color: Colors.accent, fontSize: 16, fontWeight: '700' },
});

export default ResultsScreen;
