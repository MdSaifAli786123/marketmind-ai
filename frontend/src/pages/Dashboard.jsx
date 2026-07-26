import {
    useEffect,
    useState,
} from "react";

import {
    getCompanies,
    getCountries,
    getDatasetStatus,
    getExperienceDistribution,
    getJobFamilies,
    getJobTypeDistribution,
    getOverview,
    getRemoteDistribution,
    getTopSkills,
} from "../api/client";

import JobFamilyChart from "../components/JobFamilyChart";
import RemoteChart from "../components/RemoteChart";
import SkillChart from "../components/SkillChart";
import StatCard from "../components/StatCard";


// ==========================================================
// Helpers
// ==========================================================

function formatRefreshTime(value) {
    if (!value) {
        return "No refresh recorded";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Unknown refresh time";
    }

    return date.toLocaleString();
}


function getDatasetLabel(status) {
    if (!status) {
        return "Dataset Status";
    }

    const refreshStatus =
        status.refresh?.status;

    const indexAvailable =
        status.dataset?.vector_index_available;

    const indexInSync =
        status.dataset?.index_in_sync;

    if (indexAvailable === false) {
        return "Index Unavailable";
    }

    if (indexInSync === false) {
        return "Dataset Out of Sync";
    }

    if (refreshStatus === "failed") {
        return "Refresh Failed";
    }

    if (refreshStatus === "partial") {
        return "Dataset Partial";
    }

    if (refreshStatus === "success") {
        return "Live Dataset";
    }

    if (refreshStatus === "never_run") {
        return "Dataset Ready";
    }

    return "Dataset Status";
}


// ==========================================================
// Dashboard
// ==========================================================

function Dashboard() {
    const [overview, setOverview] =
        useState(null);

    const [jobFamilies, setJobFamilies] =
        useState([]);

    const [skills, setSkills] =
        useState([]);

    const [remote, setRemote] =
        useState(null);

    const [experience, setExperience] =
        useState([]);

    const [jobTypes, setJobTypes] =
        useState([]);

    const [countries, setCountries] =
        useState([]);

    const [companies, setCompanies] =
        useState([]);

    const [datasetStatus, setDatasetStatus] =
        useState(null);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState(null);


    // ======================================================
    // Load Dashboard
    // ======================================================

    useEffect(() => {
        const loadDashboard = async () => {
            try {
                setLoading(true);

                const [
                    overviewData,
                    familyData,
                    skillData,
                    remoteData,
                    experienceData,
                    jobTypeData,
                    countryData,
                    companyData,
                    datasetStatusData,
                ] = await Promise.all([
                    getOverview(),
                    getJobFamilies(),
                    getTopSkills(10),
                    getRemoteDistribution(),
                    getExperienceDistribution(),
                    getJobTypeDistribution(),
                    getCountries(10),
                    getCompanies(10),
                    getDatasetStatus(),
                ]);

                setOverview(
                    overviewData
                );

                setJobFamilies(
                    familyData.data ?? []
                );

                setSkills(
                    skillData.data ?? []
                );

                setRemote(
                    remoteData
                );

                setExperience(
                    experienceData.data ?? []
                );

                setJobTypes(
                    jobTypeData.data ?? []
                );

                setCountries(
                    countryData.data ?? []
                );

                setCompanies(
                    companyData.data ?? []
                );

                setDatasetStatus(
                    datasetStatusData
                );

                setError(null);

            } catch (err) {
                console.error(
                    "Dashboard loading failed:",
                    err
                );

                setError(
                    "Unable to load market analytics."
                );

            } finally {
                setLoading(false);
            }
        };

        loadDashboard();
    }, []);


    // ======================================================
    // Loading
    // ======================================================

    if (loading) {
        return (
            <div className="status-screen">
                <h2>
                    Loading market intelligence...
                </h2>
            </div>
        );
    }


    // ======================================================
    // Error
    // ======================================================

    if (error) {
        return (
            <div className="status-screen error">
                <h2>
                    {error}
                </h2>

                <p>
                    Verify that the FastAPI server
                    is running on port 8000.
                </p>
            </div>
        );
    }


    // ======================================================
    // Dataset State
    // ======================================================

    const datasetLabel =
        getDatasetLabel(
            datasetStatus
        );

    const totalIndexed =
        datasetStatus
            ?.dataset
            ?.total_indexed;

    const databaseJobs =
        datasetStatus
            ?.dataset
            ?.total_jobs;

    const refreshStatus =
        datasetStatus
            ?.refresh
            ?.status ??
        "unknown";

    const lastRefresh =
        datasetStatus
            ?.refresh
            ?.completed_at;

    const indexInSync =
        datasetStatus
            ?.dataset
            ?.index_in_sync;


    // ======================================================
    // UI
    // ======================================================

    return (
        <div className="dashboard">

            {/* ============================================= */}
            {/* Header                                        */}
            {/* ============================================= */}

            <header className="dashboard-header">

                <div>
                    <p className="eyebrow">
                        MARKET INTELLIGENCE PLATFORM
                    </p>

                    <h1>
                        AI Job Market Intelligence
                    </h1>

                    <p className="header-description">
                        Explore enriched job-market
                        data, technology demand,
                        hiring patterns and workforce
                        trends.
                    </p>
                </div>


                {/* ========================================= */}
                {/* Real Dataset Status                       */}
                {/* ========================================= */}

                <div
                    className="live-badge"
                    title={
                        `Database jobs: ${
                            databaseJobs ?? "Unknown"
                        }\n` +
                        `Indexed vectors: ${
                            totalIndexed ?? "Unavailable"
                        }\n` +
                        `Refresh status: ${
                            refreshStatus
                        }\n` +
                        `Last refresh: ${
                            formatRefreshTime(
                                lastRefresh
                            )
                        }`
                    }
                >
                    <span
                        className={
                            indexInSync === false
                                ? "live-dot warning"
                                : "live-dot"
                        }
                    />

                    {datasetLabel}
                </div>
            </header>


            {/* ============================================= */}
            {/* Statistics                                    */}
            {/* ============================================= */}

            <section className="stat-grid">

                <StatCard
                    title="Total Jobs"
                    value={
                        overview?.total_jobs ?? 0
                    }
                    subtitle="Jobs analyzed"
                />

                <StatCard
                    title="Companies"
                    value={
                        overview?.total_companies ?? 0
                    }
                    subtitle="Hiring organizations"
                />

                <StatCard
                    title="Locations"
                    value={
                        overview?.total_locations ?? 0
                    }
                    subtitle="Market locations"
                />

                <StatCard
                    title="Skills"
                    value={
                        overview?.unique_skills ?? 0
                    }
                    subtitle="Normalized technologies"
                />

                <StatCard
                    title="Remote Jobs"
                    value={
                        overview?.remote_jobs ?? 0
                    }
                    subtitle={
                        `${
                            overview
                                ?.remote_percentage ??
                            0
                        }% of jobs`
                    }
                />

            </section>


            {/* ============================================= */}
            {/* Job Families + Remote                         */}
            {/* ============================================= */}

            <section className="dashboard-grid">

                <div className="panel panel-large">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Job Family Distribution
                            </h2>

                            <p>
                                Distribution across
                                enriched job categories
                            </p>
                        </div>
                    </div>

                    <JobFamilyChart
                        data={jobFamilies}
                    />

                </div>


                <div className="panel">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Remote Work
                            </h2>

                            <p>
                                Remote versus
                                non-remote positions
                            </p>
                        </div>
                    </div>

                    <RemoteChart
                        data={remote}
                    />

                    <div className="remote-highlight">

                        <strong>
                            {
                                remote
                                    ?.remote_percentage ??
                                0
                            }%
                        </strong>

                        <span>
                            of collected jobs are remote
                        </span>

                    </div>

                </div>

            </section>


            {/* ============================================= */}
            {/* Skills + Experience                           */}
            {/* ============================================= */}

            <section className="dashboard-grid">

                <div className="panel panel-large">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Top Skills
                            </h2>

                            <p>
                                Most frequently detected
                                technologies and skills
                            </p>
                        </div>
                    </div>

                    <SkillChart
                        data={skills}
                    />

                </div>


                <div className="panel">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Experience Levels
                            </h2>

                            <p>
                                Seniority distribution
                            </p>
                        </div>
                    </div>

                    <div className="ranking-list">

                        {experience.map(
                            (item) => (
                                <div
                                    className="ranking-item"
                                    key={item.name}
                                >
                                    <span>
                                        {item.name}
                                    </span>

                                    <strong>
                                        {item.count}
                                    </strong>
                                </div>
                            )
                        )}

                    </div>

                </div>

            </section>


            {/* ============================================= */}
            {/* Job Types + Countries + Companies             */}
            {/* ============================================= */}

            <section className="three-column-grid">

                <div className="panel">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Job Types
                            </h2>

                            <p>
                                Employment structure
                            </p>
                        </div>
                    </div>

                    <div className="ranking-list">

                        {jobTypes.map(
                            (item) => (
                                <div
                                    className="ranking-item"
                                    key={item.name}
                                >
                                    <span>
                                        {item.name}
                                    </span>

                                    <strong>
                                        {item.count}
                                    </strong>
                                </div>
                            )
                        )}

                    </div>

                </div>


                <div className="panel">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Top Countries
                            </h2>

                            <p>
                                Geographic job demand
                            </p>
                        </div>
                    </div>

                    <div className="ranking-list">

                        {countries.map(
                            (item) => (
                                <div
                                    className="ranking-item"
                                    key={item.country}
                                >
                                    <span>
                                        {item.country}
                                    </span>

                                    <strong>
                                        {item.jobs}
                                    </strong>
                                </div>
                            )
                        )}

                    </div>

                </div>


                <div className="panel">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Top Companies
                            </h2>

                            <p>
                                Most active employers
                            </p>
                        </div>
                    </div>

                    <div className="ranking-list">

                        {companies.map(
                            (item) => (
                                <div
                                    className="ranking-item"
                                    key={item.company}
                                >
                                    <span>
                                        {item.company}
                                    </span>

                                    <strong>
                                        {item.jobs}
                                    </strong>
                                </div>
                            )
                        )}

                    </div>

                </div>

            </section>


            {/* ============================================= */}
            {/* Footer                                        */}
            {/* ============================================= */}

            <footer className="dashboard-footer">
                AI Job Market Intelligence

                <span>
                    •
                </span>

                FastAPI + PostgreSQL + React
            </footer>

        </div>
    );
}


export default Dashboard;