import axiosInstance from './axiosInstance';
import { Endpoints } from '../constants/endpoints';

export const profileApi = {
  // Profiles
  listProfiles: () => axiosInstance.get(Endpoints.PROFILES),
  createProfile: (profileData) => axiosInstance.post(Endpoints.PROFILES, profileData),
  getProfile: (profileId) => axiosInstance.get(`${Endpoints.PROFILES}/${profileId}`),
  updateProfile: (profileId, data) => axiosInstance.patch(`${Endpoints.PROFILES}/${profileId}`, data),
  archiveProfile: (profileId) => axiosInstance.post(`${Endpoints.PROFILES}/${profileId}/archive`),
  deleteProfile: (profileId) => axiosInstance.delete(`${Endpoints.PROFILES}/${profileId}`),

  // Profile-specific measurements
  getProfileMeasurements: (profileId) => axiosInstance.get(`${Endpoints.PROFILES}/${profileId}/measurements`),
  getProfileLatestMeasurement: (profileId) => axiosInstance.get(`${Endpoints.PROFILES}/${profileId}/measurements/latest`),
  deleteProfileMeasurement: (profileId, analysisId) =>
    axiosInstance.delete(`${Endpoints.PROFILES}/${profileId}/measurements/${analysisId}`),

  // Invitations & Unlocking
  createInvite: (inviteData) => axiosInstance.post(Endpoints.PROFILE_INVITES, inviteData),
  listInvites: () => axiosInstance.get(Endpoints.PROFILE_INVITES),
  revokeInvite: (inviteId) => axiosInstance.delete(`${Endpoints.PROFILE_INVITES}/${inviteId}`),
  claimInvite: (claimData) => axiosInstance.post(Endpoints.CLAIM_INVITE, claimData),
  getAvailableProfiles: () => axiosInstance.get('/api/profiles/available'),
  unlockInvitedProfile: (invited_email) => axiosInstance.post('/api/profiles/unlock-invited', { invited_email }),
  unlockOwnerProfile: (password) => axiosInstance.post('/api/profiles/unlock-owner', password ? { password } : {}),
};
