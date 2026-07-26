import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";


function JobFamilyChart({ data }) {
    if (!data?.length) {
        return (
            <div className="empty-chart">
                No job-family data available.
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
                    left: 35,
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
                    dataKey="name"
                    type="category"
                    width={180}
                    tick={{
                        fontSize: 12,
                    }}
                />

                <Tooltip />

                <Bar
                    dataKey="count"
                    name="Jobs"
                    fill="#2563eb"
                    radius={[0, 6, 6, 0]}
                />
            </BarChart>
        </ResponsiveContainer>
    );
}


export default JobFamilyChart;