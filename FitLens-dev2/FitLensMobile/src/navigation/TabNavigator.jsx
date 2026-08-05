import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import HomeScreen from '../screens/main/HomeScreen';
import HistoryScreen from '../screens/history/HistoryScreen';
import SettingsScreen from '../screens/settings/SettingsScreen';
import { Colors } from '../constants/colors';

const Tab = createBottomTabNavigator();

const TabNavigator = () => (
  <Tab.Navigator
    screenOptions={{
      headerShown: false,
      tabBarStyle: {
        backgroundColor: Colors.secondary,
        borderTopColor: Colors.border,
        paddingBottom: 8,
        height: 60,
      },
      tabBarActiveTintColor: Colors.accent,
      tabBarInactiveTintColor: Colors.textSecondary,
    }}>
    <Tab.Screen
      name="Home"
      component={HomeScreen}
      options={{
        tabBarIcon: ({ color }) => <Text style={{ fontSize: 22 }}>🏠</Text>,
      }}
    />
    <Tab.Screen
      name="History"
      component={HistoryScreen}
      options={{
        tabBarIcon: ({ color }) => <Text style={{ fontSize: 22 }}>📊</Text>,
      }}
    />
    <Tab.Screen
      name="Settings"
      component={SettingsScreen}
      options={{
        tabBarIcon: ({ color }) => <Text style={{ fontSize: 22 }}>⚙️</Text>,
      }}
    />
  </Tab.Navigator>
);

export default TabNavigator;
