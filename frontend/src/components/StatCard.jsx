function StatCard({ title, value, subtitle }) {
    return (
        <article className="stat-card">
            <p className="stat-title">{title}</p>

            <h2 className="stat-value">
                {value}
            </h2>

            {subtitle && (
                <p className="stat-subtitle">
                    {subtitle}
                </p>
            )}
        </article>
    );
}

export default StatCard;