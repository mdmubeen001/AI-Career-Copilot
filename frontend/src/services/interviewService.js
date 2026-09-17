import api from './api';

export const interviewService = {
  /**
   * Create a new interview session.
   * @param {Object} data { resume_id, target_role, interview_type, difficulty, total_questions }
   */
  async createInterview(data) {
    const response = await api.post('/interviews/', data);
    return response.data;
  },

  /**
   * List all interview sessions for the authenticated user.
   */
  async getInterviews() {
    const response = await api.get('/interviews/');
    return response.data;
  },

  /**
   * Retrieve specific interview session details.
   * @param {number|string} id Session ID
   */
  async getInterview(id) {
    const response = await api.get(`/interviews/${id}/`);
    return response.data;
  },

  /**
   * Start an interview session (generates questions and sets status to in_progress).
   * @param {number|string} id Session ID
   */
  async startInterview(id) {
    const response = await api.post(`/interviews/${id}/start/`);
    return response.data;
  },

  /**
   * Retrieve questions for a specific session.
   * @param {number|string} id Session ID
   */
  async getQuestions(id) {
    const response = await api.get(`/interviews/${id}/questions/`);
    return response.data;
  },

  /**
   * Submit an answer to a question in an interview session.
   * @param {number|string} sessionId Session ID
   * @param {number|string} questionId Question ID
   * @param {Object} data { answer_text: string }
   */
  async submitAnswer(sessionId, questionId, data) {
    const response = await api.post(
      `/interviews/${sessionId}/questions/${questionId}/answer/`,
      data
    );
    return response.data;
  },

  /**
   * Complete an interview session and generate final evaluation.
   * @param {number|string} id Session ID
   */
  async completeInterview(id) {
    const response = await api.post(`/interviews/${id}/complete/`);
    return response.data;
  },

  /**
   * Retrieve final evaluation and results breakdown for an interview session.
   * @param {number|string} id Session ID
   */
  async getInterviewResult(id) {
    const response = await api.get(`/interviews/${id}/result/`);
    return response.data;
  },
};

export default interviewService;
