import api from './api';

export const careerService = {
  /**
   * Retrieve the authenticated user's career profile.
   */
  async getCareerProfile() {
    const response = await api.get('/career/profile/');
    return response.data;
  },

  /**
   * Fully or partially update the authenticated user's career profile.
   */
  async updateCareerProfile(profileData) {
    const response = await api.put('/career/profile/', profileData);
    return response.data;
  },

  /**
   * Retrieve list of all available system skills, with optional search query.
   */
  async getSkills(search = '') {
    const params = search ? { search } : {};
    const response = await api.get('/career/skills/', { params });
    return response.data;
  },

  /**
   * Create or lookup an available skill.
   */
  async createSkill(name) {
    const response = await api.post('/career/skills/', { name });
    return response.data;
  },

  /**
   * Retrieve the authenticated user's assigned skills.
   */
  async getUserSkills() {
    const response = await api.get('/career/user-skills/');
    return response.data;
  },

  /**
   * Add a skill for the authenticated user.
   */
  async addUserSkill({ skill_id, name, level }) {
    const payload = skill_id ? { skill_id, level } : { name, level };
    const response = await api.post('/career/user-skills/', payload);
    return response.data;
  },

  /**
   * Update level for an authenticated user's skill.
   */
  async updateUserSkill(id, level) {
    const response = await api.patch(`/career/user-skills/${id}/`, { level });
    return response.data;
  },

  /**
   * Remove a skill for the authenticated user.
   */
  async deleteUserSkill(id) {
    const response = await api.delete(`/career/user-skills/${id}/`);
    return response.data;
  },

  /**
   * Synchronize the complete list of user skills in one call.
   */
  async syncUserSkills(skills) {
    const response = await api.post('/career/user-skills/sync/', { skills });
    return response.data;
  },

  /**
   * Trigger an AI Career Analysis for the authenticated user.
   */
  async analyzeCareer(data = {}) {
    const response = await api.post('/career/analyze/', data);
    return response.data;
  },

  /**
   * Retrieve the latest career analysis for the authenticated user.
   */
  async getLatestAnalysis() {
    const response = await api.get('/career/analysis/');
    return response.data;
  },

  /**
   * Retrieve historical list of career analyses.
   */
  async getAnalysisHistory() {
    const response = await api.get('/career/analysis/', { params: { all: true } });
    return response.data;
  },
};

export default careerService;
