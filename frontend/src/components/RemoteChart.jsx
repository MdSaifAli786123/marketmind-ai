import {
    Cell,
    Legend,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
} from "recharts";


const COLORS = [
    "#2563eb",
    "#dbeafe",
];


function RemoteChart({ data }) {
    if (!data) {
        return (
            <div className="empty-chart">
                No remote-work data available.
            </div>
        );
    }

    const chartData = [
        {
            name: "Remote",
            value: data.remote ?? 0,
        },
        {
            name: "Non-Remote",
            value: data.non_remote ?? 0,
        },
    ];

    return (
        <ResponsiveContainer
            width="100%"
            height={300}
        >
            <PieChart>
                <Pie
                    data={chartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="45%"
                    innerRadius={65}
                    outerRadius={100}
                    paddingAngle={3}
                >
                    {chartData.map(
                        (_, index) => (
                            <Cell
                                key={index}
                                fill={
                                    COLORS[
                                        index %
                                        COLORS.length
                                    ]
                                }
                            />
                        )
                    )}
                </Pie>

                <Tooltip />

                <Legend />
            </PieChart>
        </ResponsiveContainer>
    );
}


export default RemoteChart;