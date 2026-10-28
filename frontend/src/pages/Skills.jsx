import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";
const API_URL = `${API_BASE_URL}/api/skills`;

function Skills({ skills, setSkills }) {
  const [skillName, setSkillName] = useState("");
  const [skillLevel, setSkillLevel] = useState("Beginner");
  const [editingSkillId, setEditingSkillId] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  // CREATE a skill or UPDATE an existing skill
  async function handleAddSkill(event) {
    event.preventDefault();

    const trimmedName = skillName.trim();

    if (trimmedName === "") {
      setErrorMessage("Please enter a skill name.");
      return;
    }

    setErrorMessage("");

    try {
      if (editingSkillId !== null) {
        // PUT updates an existing skill in the database.
        const response = await fetch(`${API_URL}/${editingSkillId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: trimmedName,
            level: skillLevel,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || "Failed to update skill.");
        }

        const updatedSkill = await response.json();

        setSkills((currentSkills) =>
          currentSkills.map((skill) =>
            skill.id === updatedSkill.id ? updatedSkill : skill
          )
        );

        setEditingSkillId(null);
      } else {
        // POST creates a new skill in the database.
        const response = await fetch(API_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: trimmedName,
            level: skillLevel,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || "Failed to create skill.");
        }

        const newSkill = await response.json();

        setSkills((currentSkills) => [...currentSkills, newSkill]);
      }

      setSkillName("");
      setSkillLevel("Beginner");
    } catch (error) {
      console.error("Error saving skill:", error);
      setErrorMessage(error.message || "Something went wrong.");
    }
  }

  // LOAD an existing skill into the form for editing
  function handleEditSkill(skillId) {
    const selectedSkill = skills.find(
      (skill) => skill.id === skillId
    );

    if (!selectedSkill) return;

    setSkillName(selectedSkill.name);
    setSkillLevel(selectedSkill.level);
    setEditingSkillId(skillId);
    setErrorMessage("");
  }

  // DELETE a skill from the database
  async function handleDeleteSkill(skillId) {
    setErrorMessage("");

    try {
      const response = await fetch(`${API_URL}/${skillId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "Failed to delete skill.");
      }

      setSkills((currentSkills) =>
        currentSkills.filter((skill) => skill.id !== skillId)
      );

      if (editingSkillId === skillId) {
        setSkillName("");
        setSkillLevel("Beginner");
        setEditingSkillId(null);
      }
    } catch (error) {
      console.error("Error deleting skill:", error);
      setErrorMessage(error.message || "Something went wrong.");
    }
  }

  return (
    <main className="skills-page">
      <h2>My Skills</h2>
      <p>Track your skills and identify areas to improve.</p>

      {errorMessage && (
        <p role="alert" className="skill-error">
          {errorMessage}
        </p>
      )}

      <form className="skill-form" onSubmit={handleAddSkill}>
        <div className="skill-form-field">
          <label htmlFor="skillName">Skill name</label>
          <input
            id="skillName"
            type="text"
            placeholder="e.g. JavaScript"
            value={skillName}
            onChange={(event) => setSkillName(event.target.value)}
          />
        </div>

        <div className="skill-form-field">
          <label htmlFor="skillLevel">Proficiency level</label>
          <select
            id="skillLevel"
            value={skillLevel}
            onChange={(event) => setSkillLevel(event.target.value)}
          >
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>
        </div>

        <button type="submit">
          {editingSkillId !== null ? "Save Changes" : "Add Skill"}
        </button>
      </form>

      <div className="skills-list">
        {skills.map((skill) => (
          <div className="skill-card" key={skill.id}>
            <h3>{skill.name}</h3>
            <p>{skill.level}</p>

            <div className="skill-actions">
              <button
                type="button"
                className="skill-edit-button"
                onClick={() => handleEditSkill(skill.id)}
              >
                Edit
              </button>

              <button
                type="button"
                className="skill-delete-button"
                onClick={() => handleDeleteSkill(skill.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}

export default Skills;