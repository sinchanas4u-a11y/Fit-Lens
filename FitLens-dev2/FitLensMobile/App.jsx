import React, { useEffect } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Toast from 'react-native-toast-message';
import AppNavigator from './src/navigation/AppNavigator';
import { testConnection } from './src/api/axiosInstance';

const App = () => {
  useEffect(() => {
    testConnection();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <AppNavigator />
        <Toast />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
};

export default App;
