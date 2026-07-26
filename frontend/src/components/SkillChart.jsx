import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";


function SkillChart({ data }) {
    if (!data?.length) {
        return (
            <div className="empty-chart">
                No skill data available.
            </div>
        );
    }

    return (
        <ResponsiveContainer
            width="100%"
            height={340}
        >
            <BarChart
                data={data}
                layout="vertical"
                margin={{
                    top: 10,
                    right: 30,
                    left: 25,
                    bottom: 10,
                }}
            >
                <CartesianGrid
                    strokeDasharray="3 3"
                />

                <XAxis
                    type="number"
                    allowDecimals={false}
                />

                <YAxis
                    dataKey="skill"
                    type="category"
                    width={150}
                    tick={{
                        fontSize: 12,
                    }}
                />

                <Tooltip />

                <Bar
                    dataKey="jobs"
                    name="Jobs"
                    fill="#7c3aed"
                    radius={[0, 6, 6, 0]}
                />
            </BarChart>
        </ResponsiveContainer>
    );
}


export default SkillChart;