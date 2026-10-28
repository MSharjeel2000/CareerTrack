
import { useState } from "react";

const API_URL = "http://127.0.0.1:5000/api/goals";

function Goals({ goals, setGoals }) {
  const [goalTitle, setGoalTitle] = useState("");
  const [editingGoalId, setEditingGoalId] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  // CREATE a goal or UPDATE an existing goal
  async function handleAddGoal() {
    const trimmedTitle = goalTitle.trim();

    if (trimmedTitle === "") {
      setErrorMessage("Please enter a goal title.");
      return;
    }

    setErrorMessage("");

    try {
      if (editingGoalId !== null) {
        // Find the goal being edited so we preserve its completion status.
        const goalBeingEdited = goals.find(
          (goal) => goal.id === editingGoalId
        );

        if (!goalBeingEdited) {
          setErrorMessage("The goal could not be found.");
          return;
        }

        // PUT updates the goal in the database.
        const response = await fetch(`${API_URL}/${editingGoalId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: trimmedTitle,
            completed: goalBeingEdited.completed,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to update goal.");
        }

        const updatedGoal = await response.json();

        setGoals((currentGoals) =>
          currentGoals.map((goal) =>
            goal.id === updatedGoal.id ? updatedGoal : goal
          )
        );

        setGoalTitle("");
        setEditingGoalId(null);
      } else {
        // POST creates a new goal in the database.
        const response = await fetch(API_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: trimmedTitle,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to create goal.");
        }

        const newGoal = await response.json();

        setGoals((currentGoals) => [...currentGoals, newGoal]);
        setGoalTitle("");
      }
    } catch (error) {
      console.error("Error saving goal:", error);
      setErrorMessage(error.message || "Something went wrong.");
    }
  }

  // UPDATE a goal's completion status
  async function handleToggleGoal(goalId) {
    const selectedGoal = goals.find((goal) => goal.id === goalId);

    if (!selectedGoal) {
      setErrorMessage("The goal could not be found.");
      return;
    }

    setErrorMessage("");

    try {
      // PATCH changes only the completion status.
      const response = await fetch(`${API_URL}/${goalId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          completed: !selectedGoal.completed,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update goal status.");
      }

      const updatedGoal = await response.json();

      setGoals((currentGoals) =>
        currentGoals.map((goal) =>
          goal.id === updatedGoal.id ? updatedGoal : goal
        )
      );
    } catch (error) {
      console.error("Error updating goal status:", error);
      setErrorMessage(error.message || "Something went wrong.");
    }
  }

  // DELETE a goal
  async function handleDeleteGoal(goalId) {
    setErrorMessage("");

    try {
      const response = await fetch(`${API_URL}/${goalId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete goal.");
      }

      setGoals((currentGoals) =>
        currentGoals.filter((goal) => goal.id !== goalId)
      );

      // If the deleted goal was being edited, reset the form.
      if (editingGoalId === goalId) {
        setGoalTitle("");
        setEditingGoalId(null);
      }
    } catch (error) {
      console.error("Error deleting goal:", error);
      setErrorMessage(error.message || "Something went wrong.");
    }
  }

  // Load an existing goal into the form for editing.
  function handleEditGoal(goalId) {
    const selectedGoal = goals.find((goal) => goal.id === goalId);

    if (!selectedGoal) {
      setErrorMessage("The goal could not be found.");
      return;
    }

    setGoalTitle(selectedGoal.title);
    setEditingGoalId(goalId);
    setErrorMessage("");
  }

  return (
    <main className="goals-page">
      <h2>Career Goals</h2>
      <p>Set your career goals and track your progress.</p>

      {errorMessage && (
        <p role="alert" className="goal-error">
          {errorMessage}
        </p>
      )}

      <div className="goal-form">
        <input
          className="goal-input"
          type="text"
          placeholder="Enter a career goal"
          value={goalTitle}
          onChange={(event) => setGoalTitle(event.target.value)}
        />

        <button onClick={handleAddGoal}>
          {editingGoalId !== null ? "Save Changes" : "Add Goal"}
        </button>
      </div>

      {goals.map((goal) => (
        <div className="goal-card" key={goal.id}>
          <div className="goal-details">
            <h3>{goal.title}</h3>

            <p
              className={
                goal.completed
                  ? "goal-status completed"
                  : "goal-status in-progress"
              }
            >
              {goal.completed ? "Completed" : "In progress"}
            </p>
          </div>

          <div className="goal-actions">
            <button
              onClick={() => handleToggleGoal(goal.id)}
              className="goal-toggle-button"
            >
              {goal.completed ? "Mark Incomplete" : "Mark Complete"}
            </button>

            <button
              onClick={() => handleDeleteGoal(goal.id)}
              className="goal-delete-button"
            >
              Delete
            </button>

            <button
              onClick={() => handleEditGoal(goal.id)}
              className="goal-edit-button"
            >
              Edit
            </button>
          </div>
        </div>
      ))}
    </main>
  );
}

export default Goals;