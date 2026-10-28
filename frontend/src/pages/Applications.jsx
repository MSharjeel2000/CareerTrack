import { useState } from "react";

const API_URL = "/api/applications";

function Applications({ applications, setApplications }) {
  const [company, setCompany] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [applicationDate, setApplicationDate] = useState("");
  const [status, setStatus] = useState("Applied");
  const [editingApplicationId, setEditingApplicationId] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  function resetForm() {
    setCompany("");
    setJobTitle("");
    setApplicationDate("");
    setStatus("Applied");
    setEditingApplicationId(null);
    setErrorMessage("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage("");

    const trimmedCompany = company.trim();
    const trimmedJobTitle = jobTitle.trim();

    if (
      trimmedCompany === "" ||
      trimmedJobTitle === "" ||
      applicationDate === ""
    ) {
      setErrorMessage("Please complete all required fields.");
      return;
    }

    const applicationData = {
      company: trimmedCompany,
      job_title: trimmedJobTitle,
      applied_date: applicationDate,
      status,
    };

    try {
      if (editingApplicationId !== null) {
        // PATCH updates only the fields provided by this form.
        const response = await fetch(
          `${API_URL}/${editingApplicationId}`,
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(applicationData),
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.error || "Failed to update the application."
          );
        }

        const updatedApplication = await response.json();

        setApplications((currentApplications) =>
          currentApplications.map((application) =>
            application.id === editingApplicationId
              ? {
                  ...application,
                  ...updatedApplication,
                  jobTitle: updatedApplication.job_title,
                  applicationDate:
                    updatedApplication.applied_date ?? "",
                }
              : application
          )
        );
      } else {
        const response = await fetch(API_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(applicationData),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.error || "Failed to add the application."
          );
        }

        const newApplication = await response.json();

        setApplications((currentApplications) => [
          ...currentApplications,
          {
            ...newApplication,
            jobTitle: newApplication.job_title,
            applicationDate: newApplication.applied_date ?? "",
          },
        ]);
      }

      resetForm();
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong.");
    }
  }

  function handleEdit(applicationId) {
    const selectedApplication = applications.find(
      (application) => application.id === applicationId
    );

    if (!selectedApplication) return;

    setCompany(selectedApplication.company);
    setJobTitle(
      selectedApplication.jobTitle ??
        selectedApplication.job_title ??
        ""
    );
    setApplicationDate(
      selectedApplication.applicationDate ??
        selectedApplication.applied_date ??
        ""
    );
    setStatus(selectedApplication.status);
    setEditingApplicationId(applicationId);
    setErrorMessage("");
  }

  async function handleDelete(applicationId) {
    setErrorMessage("");

    try {
      const response = await fetch(`${API_URL}/${applicationId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || "Failed to delete the application."
        );
      }

      setApplications((currentApplications) =>
        currentApplications.filter(
          (application) => application.id !== applicationId
        )
      );

      if (editingApplicationId === applicationId) {
        resetForm();
      }
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong.");
    }
  }

  return (
    <main className="applications-page">
      <h2>Job Applications</h2>
      <p>
        Organize your applications and keep track of your progress.
      </p>

      <form className="application-form" onSubmit={handleSubmit}>
        <div className="application-form-field">
          <label htmlFor="company">Company name</label>
          <input
            id="company"
            type="text"
            placeholder="e.g. Acme Technologies"
            value={company}
            onChange={(event) => setCompany(event.target.value)}
            required
          />
        </div>

        <div className="application-form-field">
          <label htmlFor="jobTitle">Job title</label>
          <input
            id="jobTitle"
            type="text"
            placeholder="e.g. Frontend Developer"
            value={jobTitle}
            onChange={(event) => setJobTitle(event.target.value)}
            required
          />
        </div>

        <div className="application-form-field">
          <label htmlFor="applicationDate">Application date</label>
          <input
            id="applicationDate"
            type="date"
            value={applicationDate}
            onChange={(event) => setApplicationDate(event.target.value)}
            required
          />
        </div>

        <div className="application-form-field">
          <label htmlFor="applicationStatus">Status</label>
          <select
            id="applicationStatus"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="Applied">Applied</option>
            <option value="Interview">Interview</option>
            <option value="Offer">Offer</option>
            <option value="Accepted">Accepted</option>
            <option value="Rejected">Rejected</option>
            <option value="Withdrawn">Withdrawn</option>
          </select>
        </div>

        <div className="application-form-actions">
          <button type="submit">
            {editingApplicationId !== null
              ? "Save Changes"
              : "Add Application"}
          </button>

          {editingApplicationId !== null && (
            <button
              type="button"
              className="application-cancel-button"
              onClick={resetForm}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {errorMessage && (
        <p role="alert" className="application-error">
          {errorMessage}
        </p>
      )}

      <div className="applications-list">
        {applications.length === 0 ? (
          <p className="applications-empty">
            No applications yet. Add your first application above.
          </p>
        ) : (
          applications.map((application) => (
            <article className="application-card" key={application.id}>
              <div className="application-details">
                <h3>
                  {application.jobTitle ?? application.job_title}
                </h3>

                <p className="application-company">
                  {application.company}
                </p>

                <p className="application-date">
                  Applied on:{" "}
                  {application.applicationDate ??
                    application.applied_date ??
                    ""}
                </p>

                <span
                  className={`application-status status-${application.status.toLowerCase()}`}
                >
                  {application.status}
                </span>
              </div>

              <div className="application-actions">
                <button
                  type="button"
                  className="application-edit-button"
                  onClick={() => handleEdit(application.id)}
                >
                  Edit
                </button>

                <button
                  type="button"
                  className="application-delete-button"
                  onClick={() => handleDelete(application.id)}
                >
                  Delete
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </main>
  );
}

export default Applications;