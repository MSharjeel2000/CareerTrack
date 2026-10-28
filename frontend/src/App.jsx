import { Routes, Route, NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";
import Goals from "./pages/Goals";
import Skills from "./pages/Skills";
import Applications from "./pages/Applications";
import "./App.css";

function App() {
  const [goals, setGoals] = useState([]);
  const [skills, setSkills] = useState([]);
  const [applications, setApplications] = useState([]);

  // Load career goals from the backend
  useEffect(() => {
    fetch("/api/goals")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load goals");
        }
        return response.json();
      })
      .then((data) => {
        setGoals(data);
      })
      .catch((error) => {
        console.error("Error loading goals:", error);
      });
  }, []);

  // Load skills from the backend
  useEffect(() => {
    fetch("/api/skills")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load skills");
        }
        return response.json();
      })
      .then((data) => {
        setSkills(data);
      })
      .catch((error) => {
        console.error("Error loading skills:", error);
      });
  }, []);

  // Load job applications from the backend
  useEffect(() => {
    fetch("/api/applications")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load applications");
        }
        return response.json();
      })
      .then((data) => {
        const formattedApplications = data.map((application) => ({
          ...application,
          jobTitle: application.job_title,
          applicationDate: application.applied_date ?? "",
        }));

        setApplications(formattedApplications);
      })
      .catch((error) => {
        console.error("Error loading applications:", error);
      });
  }, []);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h1>CareerTrack</h1>
        <nav>
          <ul>
            <li className="active">
              <NavLink to="/">Dashboard</NavLink>
            </li>
            <li>
              <NavLink to="/goals">Career Goals</NavLink>
            </li>
            <li>
              <NavLink to="/skills">My Skills</NavLink>
            </li>
            <li>
              <NavLink to="/applications">Job Applications</NavLink>
            </li>
          </ul>
        </nav>
      </aside>

      <div className="page-area">
        <main className="main-content">
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  goals={goals}
                  skills={skills}
                  applications={applications}
                />
              }
            />
            <Route
              path="/goals"
              element={
                <Goals goals={goals} setGoals={setGoals} />
              }
            />
            <Route
              path="/skills"
              element={
                <Skills skills={skills} setSkills={setSkills} />
              }
            />
            <Route
              path="/applications"
              element={
                <Applications
                  applications={applications}
                  setApplications={setApplications}
                />
              }
            />
          </Routes>
        </main>

        <footer className="site-footer">
          <div className="footer-content">
            <h3>CareerTrack, Developed by Muhammad Sharjeel</h3>
            <p>Organize your goals. Build your future.</p>
            <p className="footer-copyright">
              © 2026 CareerTrack. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;