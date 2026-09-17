import api from './api';

export const resumeService = {
  /**
   * Upload a resume document (.pdf or .docx) and extract text.
   * Optionally triggers immediate AI ATS analysis.
   */
  async uploadResume(file, targetRole = '', autoAnalyze = true) {
    const formData = new FormData();
    formData.append('file', file);
    if (targetRole) {
      formData.append('target_role', targetRole);
    }
    formData.append('auto_analyze', autoAnalyze ? 'true' : 'false');

    const response = await api.post('/resumes/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Retrieve list of all uploaded resumes for the current user.
   */
  async getResumes() {
    const response = await api.get('/resumes/');
    return response.data;
  },

  /**
   * Retrieve detailed information for a specific resume, including extracted text and analysis.
   */
  async getResume(id) {
    const response = await api.get(`/resumes/${id}/`);
    return response.data;
  },

  /**
   * Trigger or re-run AI evaluation for an uploaded resume with an optional target role.
   */
  async analyzeResume(id, targetRole = '') {
    const payload = {};
    if (targetRole) {
      payload.target_role = targetRole;
    }
    const response = await api.post(`/resumes/${id}/analyze/`, payload);
    return response.data;
  },

  /**
   * Delete an uploaded resume and its associated analysis.
   */
  async deleteResume(id) {
    const response = await api.delete(`/resumes/${id}/`);
    return response.data;
  },
};

export default resumeService;
