import { useEffect, useState } from 'react';
import useAuth from '../hooks/useAuth';
import { profileService } from '../services/profileService';
import { formatApiError } from '../utils/errorHandler';

export default function Profile() {
  const { profile, updateProfile, refreshProfile } = useAuth();

  const [formData, setFormData] = useState({
    full_name: '',
    education: '',
    college: '',
    degree: '',
    graduation_year: '',
    skills: '',
    interests: '',
    career_goal: '',
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Initialize form data from profile
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await profileService.getProfile();
        setFormData({
          full_name: data.full_name || '',
          education: data.education || '',
          college: data.college || '',
          degree: data.degree || '',
          graduation_year: data.graduation_year || '',
          skills: Array.isArray(data.skills) ? data.skills.join(', ') : data.skills || '',
          interests: Array.isArray(data.interests) ? data.interests.join(', ') : data.interests || '',
          career_goal: data.career_goal || '',
        });
      } catch (err) {
        setErrorMsg(formatApiError(err));
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [refreshProfile]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (successMsg) setSuccessMsg('');
    if (errorMsg) setErrorMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg('');
    setErrorMsg('');

    // Prepare payload for backend PUT /api/v1/profile/
    const payload = {
      full_name: formData.full_name,
      education: formData.education,
      college: formData.college,
      degree: formData.degree,
      graduation_year: formData.graduation_year ? parseInt(formData.graduation_year, 10) : null,
      skills: formData.skills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      interests: formData.interests
        .split(',')
        .map((i) => i.trim())
        .filter(Boolean),
      career_goal: formData.career_goal,
    };

    try {
      await updateProfile(payload);
      setSuccessMsg('Profile updated successfully!');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setErrorMsg(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading your profile details...</p>
      </div>
    );
  }

  // Parse current skills/interests for live tag previews
  const previewSkills = formData.skills
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  const previewInterests = formData.interests
    .split(',')
    .map((i) => i.trim())
    .filter(Boolean);

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="profile-header">
          <div className="auth-badge">Account Settings</div>
          <h1>Your Career Profile</h1>
          <p>
            Manage your personal background, education, skills, and goals. This data powers your AI Agent recommendations.
          </p>
        </div>

        {successMsg && (
          <div className="alert alert-success" role="alert">
            <span className="alert-icon">✅</span>
            <div className="alert-content">{successMsg}</div>
          </div>
        )}

        {errorMsg && (
          <div className="alert alert-error" role="alert">
            <span className="alert-icon">⚠️</span>
            <div className="alert-content">{errorMsg}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="profile-form">
          {/* Identity & Account Card */}
          <div className="form-section">
            <h2 className="section-title">👤 Personal Identity</h2>
            <div className="form-grid-2">
              <div className="form-group">
                <label htmlFor="email">Email Address (Read-Only)</label>
                <input
                  id="email"
                  type="email"
                  value={profile?.email || ''}
                  disabled
                  className="input-disabled"
                />
                <span className="input-hint">Your email is your unique login credential.</span>
              </div>

              <div className="form-group">
                <label htmlFor="full_name">Full Name</label>
                <input
                  id="full_name"
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  placeholder="e.g. John Doe"
                  disabled={saving}
                />
              </div>
            </div>
          </div>

          {/* Academic Background */}
          <div className="form-section">
            <h2 className="section-title">🎓 Education &amp; Academic Background</h2>
            <div className="form-grid-2">
              <div className="form-group">
                <label htmlFor="education">Education Level</label>
                <input
                  id="education"
                  type="text"
                  name="education"
                  value={formData.education}
                  onChange={handleChange}
                  placeholder="e.g. Undergraduate, Post Graduate, High School"
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="college">College / University</label>
                <input
                  id="college"
                  type="text"
                  name="college"
                  value={formData.college}
                  onChange={handleChange}
                  placeholder="e.g. Stanford University"
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="degree">Degree / Major</label>
                <input
                  id="degree"
                  type="text"
                  name="degree"
                  value={formData.degree}
                  onChange={handleChange}
                  placeholder="e.g. B.S. in Computer Science"
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="graduation_year">Graduation Year</label>
                <input
                  id="graduation_year"
                  type="number"
                  name="graduation_year"
                  value={formData.graduation_year}
                  onChange={handleChange}
                  placeholder="e.g. 2026"
                  min="1950"
                  max="2100"
                  disabled={saving}
                />
              </div>
            </div>
          </div>

          {/* Skills & Goals */}
          <div className="form-section">
            <h2 className="section-title">⚡ Skills, Interests &amp; Career Aspirations</h2>

            <div className="form-group">
              <label htmlFor="skills">Skills (Comma-separated)</label>
              <input
                id="skills"
                type="text"
                name="skills"
                value={formData.skills}
                onChange={handleChange}
                placeholder="e.g. Python, Django, React, Machine Learning, SQL"
                disabled={saving}
              />
              {previewSkills.length > 0 && (
                <div className="tags-preview">
                  <span className="preview-label">Live Tags:</span>
                  {previewSkills.map((skill, index) => (
                    <span key={index} className="tag tag-skill">
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="interests">Interests (Comma-separated)</label>
              <input
                id="interests"
                type="text"
                name="interests"
                value={formData.interests}
                onChange={handleChange}
                placeholder="e.g. AI Agents, Distributed Systems, Web3, Cloud Architecture"
                disabled={saving}
              />
              {previewInterests.length > 0 && (
                <div className="tags-preview">
                  <span className="preview-label">Live Tags:</span>
                  {previewInterests.map((interest, index) => (
                    <span key={index} className="tag tag-interest">
                      {interest}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="career_goal">Primary Career Goal</label>
              <textarea
                id="career_goal"
                name="career_goal"
                value={formData.career_goal}
                onChange={handleChange}
                rows="3"
                placeholder="e.g. Become an AI Software Engineer at a leading technology firm specializing in autonomous multi-agent systems."
                disabled={saving}
              ></textarea>
              <span className="input-hint">
                The Supervisor Agent will use this goal to generate targeted skill-gap roadmaps and project recommendations.
              </span>
            </div>
          </div>

          {/* Metadata Footer */}
          {profile?.created_at && (
            <div className="profile-metadata">
              <span>Member since: {new Date(profile.created_at).toLocaleDateString()}</span>
              {profile?.updated_at && (
                <span>Last updated: {new Date(profile.updated_at).toLocaleDateString()}</span>
              )}
            </div>
          )}

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={saving}
            >
              {saving ? (
                <span className="btn-loading">
                  <span className="spinner-sm"></span> Saving Profile...
                </span>
              ) : (
                'Save Profile Changes'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
