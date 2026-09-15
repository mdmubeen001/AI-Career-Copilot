import { useEffect, useState } from 'react';
import useAuth from '../hooks/useAuth';
import { careerService } from '../services/careerService';
import { profileService } from '../services/profileService';
import { formatApiError } from '../utils/errorHandler';

const EXPERIENCE_LEVEL_OPTIONS = [
  'Student / Intern',
  'Entry-level (0-2 years)',
  'Mid-level (3-5 years)',
  'Senior (5-8 years)',
  'Lead / Principal (8+ years)',
  'Executive / Engineering Manager',
];

const SKILL_LEVEL_OPTIONS = ['Beginner', 'Intermediate', 'Advanced'];

export default function Profile() {
  const { profile, updateProfile, refreshProfile } = useAuth();

  // Accounts Profile state
  const [accountData, setAccountData] = useState({
    full_name: '',
    education: '',
    college: '',
    degree: '',
    graduation_year: '',
    interests: '',
  });

  // Career Profile state
  const [careerData, setCareerData] = useState({
    current_role: '',
    target_role: '',
    experience_level: 'Entry-level (0-2 years)',
    bio: '',
  });

  // User Skills state
  const [userSkills, setUserSkills] = useState([]);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillLevel, setNewSkillLevel] = useState('Intermediate');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Fetch initial profile & career data
  useEffect(() => {
    let isMounted = true;

    async function loadAllData() {
      try {
        setLoading(true);
        setErrorMsg('');

        // Fetch Accounts Profile, Career Profile, and User Skills concurrently
        const [accProfile, carProfile, carSkills] = await Promise.all([
          profileService.getProfile(),
          careerService.getCareerProfile(),
          careerService.getUserSkills(),
        ]);

        if (!isMounted) return;

        setAccountData({
          full_name: accProfile.full_name || '',
          education: accProfile.education || '',
          college: accProfile.college || '',
          degree: accProfile.degree || '',
          graduation_year: accProfile.graduation_year || '',
          interests: Array.isArray(accProfile.interests)
            ? accProfile.interests.join(', ')
            : accProfile.interests || '',
        });

        setCareerData({
          current_role: carProfile.current_role || '',
          target_role: carProfile.target_role || accProfile.career_goal || '',
          experience_level: carProfile.experience_level || 'Entry-level (0-2 years)',
          bio: carProfile.bio || '',
        });

        // Map user skills from career app
        if (Array.isArray(carSkills) && carSkills.length > 0) {
          setUserSkills(
            carSkills.map((s) => ({
              id: s.id,
              name: s.skill_name || s.name || '',
              level: s.level || 'Beginner',
            }))
          );
        } else if (Array.isArray(accProfile.skills) && accProfile.skills.length > 0) {
          // Fallback to legacy skills in accounts profile if career skills not yet set
          setUserSkills(
            accProfile.skills.map((s) => ({
              name: typeof s === 'string' ? s : s.name || '',
              level: 'Intermediate',
            }))
          );
        }
      } catch (err) {
        if (!isMounted) return;
        setErrorMsg(formatApiError(err));
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadAllData();

    return () => {
      isMounted = false;
    };
  }, [refreshProfile]);

  const handleAccountChange = (e) => {
    const { name, value } = e.target;
    setAccountData((prev) => ({ ...prev, [name]: value }));
    if (successMsg) setSuccessMsg('');
    if (errorMsg) setErrorMsg('');
  };

  const handleCareerChange = (e) => {
    const { name, value } = e.target;
    setCareerData((prev) => ({ ...prev, [name]: value }));
    if (successMsg) setSuccessMsg('');
    if (errorMsg) setErrorMsg('');
  };

  const handleAddSkill = (e) => {
    if (e) e.preventDefault();
    const trimmed = newSkillName.trim();
    if (!trimmed) return;

    // Avoid duplicate names (case-insensitive)
    const exists = userSkills.some(
      (s) => s.name.toLowerCase() === trimmed.toLowerCase()
    );

    if (exists) {
      // Update the level of existing skill
      setUserSkills((prev) =>
        prev.map((s) =>
          s.name.toLowerCase() === trimmed.toLowerCase()
            ? { ...s, level: newSkillLevel }
            : s
        )
      );
    } else {
      setUserSkills((prev) => [
        ...prev,
        { name: trimmed, level: newSkillLevel },
      ]);
    }

    setNewSkillName('');
    if (successMsg) setSuccessMsg('');
  };

  const handleRemoveSkill = (indexToRemove) => {
    setUserSkills((prev) => prev.filter((_, idx) => idx !== indexToRemove));
    if (successMsg) setSuccessMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg('');
    setErrorMsg('');

    // Prepare Account Profile payload
    const accountPayload = {
      full_name: accountData.full_name,
      education: accountData.education,
      college: accountData.college,
      degree: accountData.degree,
      graduation_year: accountData.graduation_year
        ? parseInt(accountData.graduation_year, 10)
        : null,
      interests: accountData.interests
        .split(',')
        .map((i) => i.trim())
        .filter(Boolean),
      career_goal: careerData.target_role,
      skills: userSkills.map((s) => s.name),
    };

    // Prepare Career Profile payload
    const careerPayload = {
      current_role: careerData.current_role,
      target_role: careerData.target_role,
      experience_level: careerData.experience_level,
      bio: careerData.bio,
    };

    // Prepare User Skills payload for bulk sync
    const skillsPayload = userSkills.map((s) => ({
      name: s.name,
      level: s.level,
    }));

    try {
      // Save all three parts concurrently
      await Promise.all([
        updateProfile(accountPayload),
        careerService.updateCareerProfile(careerPayload),
        careerService.syncUserSkills(skillsPayload),
      ]);

      setSuccessMsg('Career profile, personal details, and skills updated successfully!');
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
        <p>Loading your career profile...</p>
      </div>
    );
  }

  const previewInterests = accountData.interests
    .split(',')
    .map((i) => i.trim())
    .filter(Boolean);

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="profile-header">
          <div className="auth-badge">Career &amp; Account Settings</div>
          <h1>Your Career Profile</h1>
          <p>
            Manage your career trajectory, target role, professional bio, and competencies.
            This information powers your AI Agent recommendations and roadmaps.
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
                  value={accountData.full_name}
                  onChange={handleAccountChange}
                  placeholder="e.g. Jane Doe"
                  disabled={saving}
                />
              </div>
            </div>
          </div>

          {/* Career & Professional Trajectory (CareerProfile API) */}
          <div className="form-section">
            <h2 className="section-title">🎯 Career &amp; Professional Trajectory</h2>
            <div className="form-grid-2">
              <div className="form-group">
                <label htmlFor="current_role">Current Role</label>
                <input
                  id="current_role"
                  type="text"
                  name="current_role"
                  value={careerData.current_role}
                  onChange={handleCareerChange}
                  placeholder="e.g. Junior Full-Stack Developer, CS Student"
                  disabled={saving}
                />
                <span className="input-hint">Where you currently stand in your career.</span>
              </div>

              <div className="form-group">
                <label htmlFor="target_role">Target Career Role / Goal</label>
                <input
                  id="target_role"
                  type="text"
                  name="target_role"
                  value={careerData.target_role}
                  onChange={handleCareerChange}
                  placeholder="e.g. Senior AI Systems Engineer"
                  disabled={saving}
                  required
                />
                <span className="input-hint">The specific role or destination you want to reach.</span>
              </div>

              <div className="form-group">
                <label htmlFor="experience_level">Experience Level</label>
                <select
                  id="experience_level"
                  name="experience_level"
                  value={careerData.experience_level}
                  onChange={handleCareerChange}
                  disabled={saving}
                >
                  {EXPERIENCE_LEVEL_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
                <span className="input-hint">Assists the AI Copilot in calibrating roadmap difficulty.</span>
              </div>

              <div className="form-group">
                <label htmlFor="interests">Interests &amp; Focus Domains</label>
                <input
                  id="interests"
                  type="text"
                  name="interests"
                  value={accountData.interests}
                  onChange={handleAccountChange}
                  placeholder="e.g. LLM Agents, Distributed Systems, Cloud"
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
            </div>

            <div className="form-group">
              <label htmlFor="bio">Professional Bio &amp; Summary</label>
              <textarea
                id="bio"
                name="bio"
                value={careerData.bio}
                onChange={handleCareerChange}
                rows="4"
                placeholder="Share a brief overview of your background, career interests, key achievements, or what inspires you in your engineering journey..."
                disabled={saving}
              ></textarea>
              <span className="input-hint">
                Used by the Supervisor and Career Agents to customize resume bullet points and interview prep.
              </span>
            </div>
          </div>

          {/* Skills Management (Skill & UserSkill APIs) */}
          <div className="form-section">
            <h2 className="section-title">⚡ Skills &amp; Competencies</h2>

            {/* Interactive Add Skill Bar */}
            <div className="skill-add-bar">
              <div className="skill-name-input">
                <input
                  id="new_skill_name"
                  type="text"
                  value={newSkillName}
                  onChange={(e) => setNewSkillName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddSkill();
                    }
                  }}
                  placeholder="Add skill (e.g. Python, Docker, PyTorch)"
                  disabled={saving}
                />
              </div>

              <div className="skill-level-select">
                <select
                  id="new_skill_level"
                  value={newSkillLevel}
                  onChange={(e) => setNewSkillLevel(e.target.value)}
                  disabled={saving}
                  aria-label="Skill proficiency level"
                >
                  {SKILL_LEVEL_OPTIONS.map((lvl) => (
                    <option key={lvl} value={lvl}>
                      {lvl}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="button"
                className="btn btn-outline"
                onClick={handleAddSkill}
                disabled={saving || !newSkillName.trim()}
              >
                + Add Skill
              </button>
            </div>

            {/* Rendered Skill Chips */}
            <div className="form-group">
              <label>Current Skills ({userSkills.length})</label>
              {userSkills.length > 0 ? (
                <div className="tags-container">
                  {userSkills.map((skill, index) => (
                    <span key={index} className="skill-tag-removable">
                      <span>{skill.name}</span>
                      <span
                        className={`skill-level-badge skill-level-${skill.level.toLowerCase()}`}
                      >
                        {skill.level}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveSkill(index)}
                        className="skill-remove-btn"
                        title={`Remove ${skill.name}`}
                        aria-label={`Remove ${skill.name}`}
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
              ) : (
                <p className="input-hint">
                  No skills added yet. Type a skill name above and click &ldquo;+ Add Skill&rdquo;.
                </p>
              )}
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
                  value={accountData.education}
                  onChange={handleAccountChange}
                  placeholder="e.g. Undergraduate, Master's Degree"
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="college">College / University</label>
                <input
                  id="college"
                  type="text"
                  name="college"
                  value={accountData.college}
                  onChange={handleAccountChange}
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
                  value={accountData.degree}
                  onChange={handleAccountChange}
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
                  value={accountData.graduation_year}
                  onChange={handleAccountChange}
                  placeholder="e.g. 2026"
                  min="1950"
                  max="2100"
                  disabled={saving}
                />
              </div>
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
                  <span className="spinner-sm"></span> Saving Profile &amp; Career Details...
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
