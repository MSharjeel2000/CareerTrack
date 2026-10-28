import DashboardCard from '../components/DashboardCard';

function Dashboard({ goals , skills , applications }) {
  return (
    <main>
        <h2>Welcome to CareerTrack</h2>
        <p>Track your goals and grow your career.</p>
        <div className="dashboard-cards">
            <DashboardCard
                title="Career Goals"
                description="Track your professional goals and progress."
                count={goals.filter((goal) => !goal.completed).length}
                countLabel="Goals in progress"
            />

            <DashboardCard
                title="My Skills"
                description="Track your skills and identify areas to improve."
                count={skills.length}
                countLabel="Skills tracked"
            />

            <DashboardCard
                title="Job Applications"
                description="Manage your applications and track their status."
                count={applications.length}
                countLabel="Applications submitted"
            />
        </div>
    </main>
  )
}

export default Dashboard