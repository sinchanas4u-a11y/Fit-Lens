import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, Image, TouchableOpacity,
  StyleSheet, Dimensions, Alert, ActivityIndicator, PermissionsAndroid, Platform
} from 'react-native';
import { WebView } from 'react-native-webview';
import RNFS from 'react-native-fs';
import { Config } from '../../constants/config';
import { useAuthStore } from '../../store/authStore';
import { Colors } from '../../constants/colors';

const { width } = Dimensions.get('window');

const ResultsScreen = ({ route, navigation }) => {
  const { data } = route.params;
  const [plotlyJs, setPlotlyJs] = useState('');
  const [meshReady, setMeshReady] = useState(false);
  const [downloading, setDownloading] = useState(false);

  // Extract all data same as web:
  const frontMeasurements = data?.results?.front?.measurements || {};
  const mergedMeasurements = data?.results?.merged?.measurements || frontMeasurements;
  const meshData = data?.mesh_data;
  const calibration = data?.calibration;
  const frontMask = data?.results?.front?.mask;
  const frontViz = data?.results?.front?.visualization;
  const sideMask = data?.results?.side?.mask;
  const sideViz = data?.results?.side?.visualization;

  useEffect(() => {
    loadPlotly();
  }, []);

  const loadPlotly = async () => {
    try {
      const js = await RNFS.readFileAssets('plotly.min.js', 'utf8');
      setPlotlyJs(js);
      setMeshReady(true);
    } catch (e) {
      console.log('Plotly error:', e);
    }
  };

  const buildMeshHtml = () => {
    if (!meshData || !plotlyJs) return '';
    const x = JSON.stringify(meshData.x || []);
    const y = JSON.stringify(meshData.y || []);
    const z = JSON.stringify(meshData.z || []);
    const i = JSON.stringify(meshData.i || []);
    const j = JSON.stringify(meshData.j || []);
    const k = JSON.stringify(meshData.k || []);
    return `<!DOCTYPE html><html>
    <head>
      <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
      <style>*{margin:0;padding:0}html,body{width:100%;height:100%;
        background:#0a0e27;overflow:hidden}#p{width:100vw;height:100vh}</style>
      <script>${plotlyJs}</script>
    </head>
    <body><div id="p"></div><script>
      try {
        var xd=${x},yd=${y},zd=${z};
        Plotly.newPlot('p',[{
          type:'mesh3d',
          x:xd,y:zd,z:yd.map(function(v){return -v;}),
          i:${i},j:${j},k:${k},
          colorscale:[[0,'#004d40'],[0.5,'#00d4aa'],[1,'#80cbc4']],
          intensity:yd,showscale:false,opacity:1,
          flatshading:false,
          lighting:{ambient:0.6,diffuse:0.9,specular:0.4,roughness:0.4,fresnel:0.3},
          lightposition:{x:1000,y:1000,z:2000},
          hoverinfo:'none'
        }],{
          paper_bgcolor:'#0a0e27',
          margin:{l:0,r:0,t:0,b:0},
          scene:{
            bgcolor:'#0a0e27',
            xaxis:{visible:false,showgrid:false,zeroline:false},
            yaxis:{visible:false,showgrid:false,zeroline:false},
            zaxis:{visible:false,showgrid:false,zeroline:false},
            camera:{eye:{x:0,y:-2.5,z:0.5},up:{x:0,y:0,z:1},center:{x:0,y:0,z:0}},
            aspectmode:'data',dragmode:'orbit'
          },
          dragmode:'orbit'
        },{responsive:true,displayModeBar:false,scrollZoom:true});
      } catch(e){
        document.body.innerHTML='<p style="color:#fc8181;padding:20px;">'+e.message+'</p>';
      }
    </script></body></html>`;
  };

  const decodeImage = (b64) => {
    if (!b64) return null;
    const clean = b64.includes(',') ? b64 : `data:image/png;base64,${b64}`;
    return { uri: clean };
  };

  const getSourceColor = (source) => {
    if (!source) return Colors.textSecondary;
    if (source.includes('MediaPipe')) return Colors.accent;
    if (source.includes('SMPL')) return '#7C3AED';
    if (source.includes('Edge') || source.includes('Canny')) return '#ED8936';
    if (source.includes('Estimated')) return '#ED8936';
    if (source.includes('User')) return '#48BB78';
    return Colors.textSecondary;
  };

  const downloadReport = async (format) => {
    if (downloading) return;
    setDownloading(true);
    try {
      // 1. Request Android Storage Permission if on Android < 33
      if (Platform.OS === 'android' && Platform.Version < 33) {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          {
            title: 'Storage Permission',
            message: 'FitLens needs access to your storage to save report files.',
            buttonNeutral: 'Ask Later',
            buttonNegative: 'Cancel',
            buttonPositive: 'OK',
          }
        );
        if (granted !== PermissionsAndroid.RESULTS.GRANTED) {
          Alert.alert('Permission Denied', 'Storage permission is required to save reports.');
          setDownloading(false);
          return;
        }
      }

      // 2. Ensure /storage/emulated/0/Download/FitLens directory exists (reusing it if present)
      const downloadDir = Platform.OS === 'android' ? RNFS.DownloadDirectoryPath : RNFS.DocumentDirectoryPath;
      const fitlensDir = `${downloadDir}/FitLens`;

      const dirExists = await RNFS.exists(fitlensDir);
      if (!dirExists) {
        await RNFS.mkdir(fitlensDir);
      }

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `FitLens_Report_${timestamp}.${format}`;
      const filePath = `${fitlensDir}/${filename}`;

      // 3. Obtain auth token
      const token = useAuthStore.getState().token;
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const measurementsForDownload = {};
      Object.entries(mergedMeasurements).forEach(([key, val]) => {
        measurementsForDownload[key] = {
          value_cm: val?.value_cm ?? null,
          value_px: val?.value_px ?? null,
          source: val?.source ?? 'Unknown',
          label: key.replace(/_/g, ' ')
            .split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
        };
      });

      const exportPayload = {
        user_id: data?.user_id || 'Guest_User',
        calibration: data?.calibration || {},
        results: data?.results || {},
        measurements: measurementsForDownload,
      };

      console.log(`[Export Start] Requesting ${format.toUpperCase()} report from: ${Config.BASE_URL}/api/download/${format}`);

      // 4. Download binary file natively using RNFS.downloadFile directly to disk
      const downloadTask = RNFS.downloadFile({
        fromUrl: `${Config.BASE_URL}/api/download/${format}`,
        toFile: filePath,
        method: 'POST',
        headers: headers,
        body: JSON.stringify(exportPayload),
      });

      const res = await downloadTask.promise;

      if (res.statusCode !== 200) {
        let errDetail = `Server responded with status code ${res.statusCode}`;
        try {
          const errText = await RNFS.readFile(filePath, 'utf8');
          const parsed = JSON.parse(errText);
          if (parsed.error) errDetail = parsed.error;
        } catch (_) {}
        // Remove error file
        await RNFS.unlink(filePath).catch(() => {});
        throw new Error(errDetail);
      }

      const fileStat = await RNFS.stat(filePath);
      console.log(`[Export Success] Saved ${format.toUpperCase()} (${fileStat.size} bytes) to: ${filePath}`);

      // 5. Show success dialog ONLY AFTER file write Promise resolves
      Alert.alert(
        '✅ Download Complete',
        `Report saved to Downloads folder as ${filename}`,
        [{ text: 'OK' }]
      );
    } catch (err) {
      console.error(`[Export Error] ${format.toUpperCase()} export failed:`, err);
      Alert.alert(
        'Download Failed',
        err.message || `Failed to download ${format.toUpperCase()} report`,
        [{ text: 'OK' }]
      );
    } finally {
      setDownloading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backBtn}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Final Measurements</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>

        {/* Calibration Info — same as web */}
        {calibration && (
          <View style={[styles.card, styles.calibrationCard]}>
            <Text style={styles.sectionTitle}>📐 Height-Based Calibration</Text>
            <View style={styles.calibrationRow}>
              <Text style={styles.calibLabel}>Your Height:</Text>
              <Text style={styles.calibValue}>{calibration.user_height_cm} cm</Text>
            </View>
            <View style={styles.calibrationRow}>
              <Text style={styles.calibLabel}>Height in Image:</Text>
              <Text style={styles.calibValue}>
                {calibration.height_in_image_px?.toFixed(2)} pixels
              </Text>
            </View>
            <View style={styles.calibrationRow}>
              <Text style={styles.calibLabel}>Scale Factor:</Text>
              <Text style={styles.calibValue}>
                {calibration.scale_factor?.toFixed(4)} cm/px
              </Text>
            </View>
            <View style={styles.formulaBox}>
              <Text style={styles.formulaText}>{calibration.formula}</Text>
            </View>
            <Text style={styles.calibNote}>{calibration.description}</Text>
          </View>
        )}

        {/* Measurements Table — same as web */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>
            📏 Body Measurements ({Object.keys(mergedMeasurements).length} measurements)
          </Text>
          {Object.entries(mergedMeasurements).map(([key, val]) => {
            const name = key.replace(/_/g, ' ')
              .split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            const cm = val?.value_cm != null ? val.value_cm.toFixed(1) : '--';
            const px = val?.value_px != null ? `(${val.value_px.toFixed(2)} px)` : '(—)';
            const source = val?.source || 'Unknown';
            const sourceColor = getSourceColor(source);
            return (
              <View key={key} style={styles.measureRow}>
                <Text style={styles.measureName}>{name}</Text>
                <Text style={styles.measureCm}>{cm} cm</Text>
                <Text style={styles.measurePx}>{px}</Text>
                <View style={[styles.sourceBadge,
                  { backgroundColor: sourceColor + '20', borderColor: sourceColor }]}>
                  <Text style={[styles.sourceText, { color: sourceColor }]}>
                    {source.length > 15 ? source.substring(0, 12) + '...' : source}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>

        {/* 3D Mesh Model */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>🧊 3D Mesh Model</Text>
          <Text style={styles.meshHint}>Drag to rotate • Pinch to zoom</Text>
          {meshData && meshReady ? (
            <View style={styles.meshContainer}>
              <WebView
                source={{ html: buildMeshHtml() }}
                style={{ flex: 1, backgroundColor: '#0a0e27' }}
                javaScriptEnabled
                domStorageEnabled
                scrollEnabled={false}
                originWhitelist={['*']}
                onError={(e) => console.log('WebView error:', e)}
              />
            </View>
          ) : (
            <View style={styles.meshPlaceholder}>
              <ActivityIndicator color={Colors.accent} size="large" />
              <Text style={{ color: Colors.textSecondary, marginTop: 12 }}>
                {meshData ? 'Loading 3D model...' : '3D mesh not available'}
              </Text>
            </View>
          )}
        </View>

        {/* Vision Analytics — Front View */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>🔍 Vision Analytics & Segmentation</Text>

          <Text style={styles.viewLabel}>Front View</Text>
          <View style={styles.imageRow}>
            <View style={styles.imageCard}>
              <Text style={styles.imageLabel}>YOLOv8 Mask</Text>
              {frontMask ? (
                <Image source={decodeImage(frontMask)}
                  style={styles.analysisImage} resizeMode="contain" />
              ) : (
                <View style={styles.noImage}>
                  <Text style={styles.noImageText}>Not available</Text>
                </View>
              )}
            </View>
            <View style={styles.imageCard}>
              <Text style={styles.imageLabel}>Pose Keypoints</Text>
              {frontViz ? (
                <Image source={decodeImage(frontViz)}
                  style={styles.analysisImage} resizeMode="contain" />
              ) : (
                <View style={styles.noImage}>
                  <Text style={styles.noImageText}>Not available</Text>
                </View>
              )}
            </View>
          </View>

          {/* Side View */}
          <Text style={[styles.viewLabel, { marginTop: 16 }]}>Side View</Text>
          <View style={styles.imageRow}>
            <View style={styles.imageCard}>
              <Text style={styles.imageLabel}>YOLOv8 Mask</Text>
              {sideMask ? (
                <Image source={decodeImage(sideMask)}
                  style={styles.analysisImage} resizeMode="contain" />
              ) : (
                <View style={styles.noImage}>
                  <Text style={styles.noImageText}>Not available</Text>
                </View>
              )}
            </View>
            <View style={styles.imageCard}>
              <Text style={styles.imageLabel}>Pose Keypoints</Text>
              {sideViz ? (
                <Image source={decodeImage(sideViz)}
                  style={styles.analysisImage} resizeMode="contain" />
              ) : (
                <View style={styles.noImage}>
                  <Text style={styles.noImageText}>Not available</Text>
                </View>
              )}
            </View>
          </View>
        </View>

        {/* Export Report */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>
            📤 Export Report {downloading && '(Downloading...)'}
          </Text>
          <View style={styles.exportRow}>
            {[
              { fmt: 'pdf', label: '📄 PDF', color: '#E53E3E' },
              { fmt: 'docx', label: '📝 DOCX', color: '#3182CE' },
              { fmt: 'xml', label: '🗂️ XML', color: '#38A169' },
            ].map(({ fmt, label, color }) => (
              <TouchableOpacity key={fmt}
                disabled={downloading}
                onPress={() => downloadReport(fmt)}
                style={[styles.exportBtn, {
                  backgroundColor: color + '20',
                  borderColor: color,
                  opacity: downloading ? 0.5 : 1,
                }]}>
                <Text style={[styles.exportLabel, { color }]}>{label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* New Measurement */}
        <TouchableOpacity
          onPress={() => navigation.navigate('Tabs')}
          style={styles.newScanBtn}>
          <Text style={styles.newScanText}>🔄 Process New Images</Text>
        </TouchableOpacity>

      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.primary },
  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', padding: 20, paddingTop: 48,
    backgroundColor: Colors.secondary,
    borderBottomWidth: 1, borderBottomColor: Colors.border
  },
  backBtn: { color: Colors.textPrimary, fontSize: 24, fontWeight: '700' },
  headerTitle: { color: Colors.textPrimary, fontSize: 18, fontWeight: '700' },
  content: { padding: 16, paddingBottom: 40 },
  card: {
    backgroundColor: Colors.cardBg, borderRadius: 16,
    padding: 16, marginBottom: 16,
    borderWidth: 1, borderColor: Colors.border
  },
  calibrationCard: {
    borderColor: Colors.accent + '50',
    backgroundColor: Colors.accent + '10'
  },
  sectionTitle: {
    color: Colors.textPrimary, fontSize: 17,
    fontWeight: '700', marginBottom: 16
  },
  calibrationRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    marginBottom: 8
  },
  calibLabel: { color: Colors.textSecondary, fontSize: 14 },
  calibValue: { color: Colors.textPrimary, fontWeight: '600', fontSize: 14 },
  formulaBox: {
    backgroundColor: Colors.primary, borderRadius: 8,
    padding: 12, marginVertical: 8
  },
  formulaText: { color: Colors.accent, fontFamily: 'monospace', fontSize: 13 },
  calibNote: { color: Colors.textSecondary, fontSize: 12,
    fontStyle: 'italic', marginTop: 4 },
  measureRow: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1, borderBottomColor: Colors.border
  },
  measureName: { flex: 1.5, color: Colors.textPrimary, fontSize: 12,
    fontWeight: '600' },
  measureCm: { flex: 1, color: Colors.accent, fontWeight: '700', fontSize: 13 },
  measurePx: { flex: 1, color: Colors.textSecondary, fontSize: 10 },
  sourceBadge: {
    paddingHorizontal: 6, paddingVertical: 3,
    borderRadius: 10, borderWidth: 1
  },
  sourceText: { fontSize: 9, fontWeight: '600' },
  meshHint: {
    color: Colors.textSecondary, fontSize: 12,
    textAlign: 'center', marginBottom: 8
  },
  meshContainer: { height: 380, borderRadius: 12, overflow: 'hidden' },
  meshPlaceholder: {
    height: 200, justifyContent: 'center',
    alignItems: 'center', borderRadius: 12,
    backgroundColor: Colors.primary
  },
  viewLabel: { color: Colors.accent, fontWeight: '700',
    fontSize: 14, marginBottom: 8 },
  imageRow: { flexDirection: 'row', gap: 8 },
  imageCard: {
    flex: 1, backgroundColor: Colors.secondary,
    borderRadius: 10, overflow: 'hidden',
    borderWidth: 1, borderColor: Colors.border
  },
  imageLabel: {
    color: Colors.textPrimary, fontSize: 11,
    fontWeight: '700', padding: 8, textAlign: 'center'
  },
  analysisImage: { width: '100%', height: 160 },
  noImage: { height: 100, justifyContent: 'center', alignItems: 'center' },
  noImageText: { color: Colors.textSecondary, fontSize: 11 },
  exportRow: { flexDirection: 'row', gap: 8 },
  exportBtn: {
    flex: 1, padding: 12, borderRadius: 10,
    borderWidth: 1, alignItems: 'center'
  },
  exportLabel: { fontWeight: '700', fontSize: 13 },
  newScanBtn: {
    backgroundColor: Colors.cardBg, borderRadius: 14,
    padding: 16, alignItems: 'center',
    borderWidth: 1, borderColor: Colors.border, marginBottom: 24
  },
  newScanText: { color: Colors.accent, fontSize: 16, fontWeight: '700' },
});

export default ResultsScreen;
