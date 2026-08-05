import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import TabNavigator from './TabNavigator';
import GuidelinesScreen from '../screens/main/GuidelinesScreen';
import UploadScreen from '../screens/main/UploadScreen';
import CameraScreen from '../screens/camera/CameraScreen';
import ProcessingScreen from '../screens/main/ProcessingScreen';
import ResultsScreen from '../screens/main/ResultsScreen';
import HistoryDetailScreen from '../screens/history/HistoryDetailScreen';
import ChangePasswordScreen from '../screens/settings/ChangePasswordScreen';
import DeleteAccountScreen from '../screens/settings/DeleteAccountScreen';
import ProfileSettings from '../screens/settings/ProfileSettings';

const Stack = createStackNavigator();

const MainNavigator = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="Tabs" component={TabNavigator} />
    <Stack.Screen name="Guidelines" component={GuidelinesScreen} />
    <Stack.Screen name="Upload" component={UploadScreen} />
    <Stack.Screen name="Camera" component={CameraScreen} />
    <Stack.Screen name="Processing" component={ProcessingScreen} />
    <Stack.Screen name="Results" component={ResultsScreen} />
    <Stack.Screen name="HistoryDetail" component={HistoryDetailScreen} />
    <Stack.Screen name="ChangePassword" component={ChangePasswordScreen} />
    <Stack.Screen name="DeleteAccount" component={DeleteAccountScreen} />
    <Stack.Screen name="ProfileSettings" component={ProfileSettings} />
  </Stack.Navigator>
);

export default MainNavigator;
