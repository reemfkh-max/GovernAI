import { JOB_LEVELS } from '../profile.js'

// Username + job level inputs, shared by sign-up and the complete-profile step.
export default function ProfileFields({ username, jobLevel, onUsername, onJobLevel }) {
  return (
    <>
      <div className="field">
        <label htmlFor="profile-username">Username</label>
        <input
          id="profile-username"
          autoComplete="username"
          value={username}
          onChange={(event) => onUsername(event.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="profile-job-level">Job level</label>
        <select
          id="profile-job-level"
          value={jobLevel}
          onChange={(event) => onJobLevel(event.target.value)}
        >
          <option value="" disabled>
            Select your job level
          </option>
          {JOB_LEVELS.map((level) => (
            <option key={level.value} value={level.value}>
              {level.label}
            </option>
          ))}
        </select>
      </div>
    </>
  )
}
