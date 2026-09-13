import api from './api';

export const profileService = {
  /**
   * Retrieve the authenticated user's profile.
   */
  async getProfile() {
    const response = await api.get('/profile/');
    return response.data;
  },

  /**
   * Fully update the authenticated user's profile.
   */
  async updateProfile(profileData) {
    const response = await api.put('/profile/', profileData);
    return response.data;
  },

  /**
   * Partially update the authenticated user's profile.
   */
  async patchProfile(partialData) {
    const response = await api.patch('/profile/', partialData);
    return response.data;
  },
};

export default profileService;
