function DashboardCard(props) {
    return (
        <div className="dashboard-card">
            <h3>{props.title}</h3>
            <p>{props.description}</p>
            <p className="card-count">{props.count}</p>
            <p className="count-label">{props.countLabel}</p>
        </div>
    )
}

export default DashboardCard