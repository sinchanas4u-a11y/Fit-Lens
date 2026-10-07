import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import { profileApi } from '../api/profileApi';
import { useMeasurementStore } from './measurementStore';

const ACTIVE_PROFILE_KEY = '@fitlens_active_profile';

export const useProfileStore = create((set, get) => ({
  profiles: [],
  activeProfile: null,
  isLoading: false,
  error: null,
  activeCount: 0,
  pendingCount: 0,
  totalSlots: 0,
  maxSlots: 4,

  fetchProfiles: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await profileApi.listProfiles();
      if (res.data?.success) {
        const fetchedProfiles = res.data.profiles || [];
        const currentActive = get().activeProfile;

        // If current active profile is in the fetched list, update it with fresh data
        let nextActive = null;
        if (currentActive) {
          nextActive = fetchedProfiles.find((p) => p.id === currentActive.id);
        }

        // If no active profile yet, try restoring from AsyncStorage or pick the first profile
        if (!nextActive && fetchedProfiles.length > 0) {
          try {
            const saved = await AsyncStorage.getItem(ACTIVE_PROFILE_KEY);
            if (saved) {
              const parsed = JSON.parse(saved);
              nextActive = fetchedProfiles.find((p) => p.id === parsed.id);
            }
          } catch (e) {
            console.log('Error reading saved profile:', e);
          }
          if (!nextActive) {
            nextActive = fetchedProfiles[0];
          }
          if (nextActive) {
            await AsyncStorage.setItem(ACTIVE_PROFILE_KEY, JSON.stringify(nextActive));
          }
        }

        set({
          profiles: fetchedProfiles,
          activeProfile: nextActive,
          activeCount: res.data.active_profiles_count ?? fetchedProfiles.length,
          pendingCount: res.data.pending_invites_count ?? 0,
          totalSlots: res.data.total_reserved_slots ?? fetchedProfiles.length,
          maxSlots: res.data.max_allowed_slots ?? 4,
          isLoading: false,
        });
        return fetchedProfiles;
      }
    } catch (err) {
      console.log('Fetch profiles error:', err.response?.data || err.message);
      set({
        error: err.response?.data?.error || err.message || 'Failed to load profiles',
        isLoading: false,
      });
    }
    return [];
  },

  setActiveProfile: async (profile) => {
    // Safety check: Prevent switching while an active scan is in progress
    const isProcessing = useMeasurementStore.getState().isProcessing;
    if (isProcessing) {
      Alert.alert(
        'Scan In Progress',
        'Cannot switch profile while a body measurement scan is actively processing. Please wait or cancel.',
        [{ text: 'OK' }]
      );
      return false;
    }

    try {
      // Clear stale measurement state from previous profile
      useMeasurementStore.getState().clearResults();
      useMeasurementStore.getState().setHistory([]);
      useMeasurementStore.getState().setLatest(null);

      // Persist to AsyncStorage
      await AsyncStorage.setItem(ACTIVE_PROFILE_KEY, JSON.stringify(profile));
      set({ activeProfile: profile });
      return true;
    } catch (err) {
      console.log('Set active profile error:', err);
      return false;
    }
  },

  clearActiveProfile: async () => {
    try {
      await AsyncStorage.removeItem(ACTIVE_PROFILE_KEY);
    } catch (e) {}
    useMeasurementStore.getState().clearResults();
    useMeasurementStore.getState().setHistory([]);
    useMeasurementStore.getState().setLatest(null);
    set({ activeProfile: null, profiles: [] });
  },

  createProfile: async (profileData) => {
    set({ isLoading: true, error: null });
    try {
      const res = await profileApi.createProfile(profileData);
      if (res.data?.success) {
        await get().fetchProfiles();
        set({ isLoading: false });
        return { success: true, profile: res.data.profile };
      }
      throw new Error(res.data?.error || 'Failed to create profile');
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || 'Failed to create profile';
      set({ error: errorMsg, isLoading: false });
      return { success: false, error: errorMsg };
    }
  },

  archiveProfile: async (profileId) => {
    try {
      const res = await profileApi.archiveProfile(profileId);
      if (res.data?.success) {
        const currentActive = get().activeProfile;
        if (currentActive?.id === profileId) {
          // If active profile was archived, switch to another available profile
          const remaining = get().profiles.filter((p) => p.id !== profileId);
          if (remaining.length > 0) {
            await get().setActiveProfile(remaining[0]);
          } else {
            await get().clearActiveProfile();
          }
        }
        await get().fetchProfiles();
        return { success: true };
      }
      throw new Error(res.data?.error || 'Failed to archive profile');
    } catch (err) {
      return { success: false, error: err.response?.data?.error || err.message };
    }
  },

  deleteProfile: async (profileId) => {
    try {
      const res = await profileApi.deleteProfile(profileId);
      if (res.data?.success) {
        const currentActive = get().activeProfile;
        if (currentActive?.id === profileId) {
          const remaining = get().profiles.filter((p) => p.id !== profileId);
          if (remaining.length > 0) {
            await get().setActiveProfile(remaining[0]);
          } else {
            await get().clearActiveProfile();
          }
        }
        await get().fetchProfiles();
        return { success: true };
      }
      throw new Error(res.data?.error || 'Failed to delete profile');
    } catch (err) {
      return { success: false, error: err.response?.data?.error || err.message };
    }
  },
}));
