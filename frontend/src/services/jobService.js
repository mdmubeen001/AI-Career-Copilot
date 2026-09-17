import api from './api';

export const jobService = {
  /**
   * Create a new Job Description for the authenticated user.
   */
  async createJobDescription(data) {
    const response = await api.post('/jobs/', data);
    return response.data;
  },

  /**
   * Retrieve all Job Descriptions created by the authenticated user.
   */
  async getJobDescriptions() {
    const response = await api.get('/jobs/');
    return response.data;
  },

  /**
   * Retrieve an individual Job Description by ID.
   */
  async getJobDescription(id) {
    const response = await api.get(`/jobs/${id}/`);
    return response.data;
  },

  /**
   * Delete an individual Job Description by ID.
   */
  async deleteJobDescription(id) {
    const response = await api.delete(`/jobs/${id}/`);
    return response.data;
  },

  /**
   * Trigger AI Job Matching between a specified Job Description and Resume.
   */
  async matchJob(jobId, resumeId) {
    const response = await api.post(`/jobs/${jobId}/match/`, { resume_id: resumeId });
    return response.data;
  },

  /**
   * Retrieve previous Job Matches for the authenticated user.
   */
  async getJobMatches() {
    const response = await api.get('/jobs/matches/');
    return response.data;
  },

  /**
   * Retrieve details of a specific Job Match.
   */
  async getJobMatch(id) {
    const response = await api.get(`/jobs/matches/${id}/`);
    return response.data;
  },
};

export default jobService;
