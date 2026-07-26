import {
    useEffect,
    useState,
} from "react";

import {
    Link,
} from "react-router-dom";

import {
    getCountries,
    getJobFamilies,
    getJobs,
    getTopSkills,
} from "../api/client";


const PAGE_SIZE = 12;


function JobExplorer() {

    const [jobs, setJobs] = useState([]);

    const [total, setTotal] = useState(0);

    const [totalPages, setTotalPages] =
        useState(0);

    const [page, setPage] = useState(1);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");

    const [jobFamilies, setJobFamilies] =
        useState([]);

    const [countries, setCountries] =
        useState([]);

    const [skills, setSkills] =
        useState([]);


    const [filters, setFilters] = useState({
        search: "",
        job_family: "",
        experience_level: "",
        job_type: "",
        country: "",
        skill: "",
        remote: "",
    });


    // ======================================================
    // Load Filter Options
    // ======================================================

    useEffect(() => {

        async function loadOptions() {

            try {

                const [
                    familyResponse,
                    countryResponse,
                    skillResponse,
                ] = await Promise.all([
                    getJobFamilies(),
                    getCountries(100),
                    getTopSkills(100),
                ]);


                setJobFamilies(
                    familyResponse.data || []
                );

                setCountries(
                    countryResponse.data || []
                );

                setSkills(
                    skillResponse.data || []
                );

            } catch (err) {

                console.error(
                    "Failed to load filter options:",
                    err
                );

            }

        }


        loadOptions();

    }, []);


    // ======================================================
    // Load Jobs
    // ======================================================

    useEffect(() => {

        async function loadJobs() {

            setLoading(true);
            setError("");


            try {

                const params = {
                    page,
                    page_size: PAGE_SIZE,
                };


                Object.entries(filters).forEach(
                    ([key, value]) => {

                        if (
                            value !== "" &&
                            value !== null &&
                            value !== undefined
                        ) {

                            params[key] = value;

                        }

                    }
                );


                if (params.remote === "true") {
                    params.remote = true;
                }


                if (params.remote === "false") {
                    params.remote = false;
                }


                const data =
                    await getJobs(params);


                setJobs(
                    data.jobs || []
                );


                setTotal(
                    data.total || 0
                );


                setTotalPages(
                    data.total_pages || 0
                );

            } catch (err) {

                console.error(
                    "Failed to load jobs:",
                    err
                );


                setError(
                    "Unable to load jobs from the API."
                );

            } finally {

                setLoading(false);

            }

        }


        loadJobs();

    }, [page, filters]);


    // ======================================================
    // Filter Change
    // ======================================================

    const handleChange = (event) => {

        const {
            name,
            value,
        } = event.target;


        setPage(1);


        setFilters((previous) => ({
            ...previous,
            [name]: value,
        }));

    };


    // ======================================================
    // Clear Filters
    // ======================================================

    const clearFilters = () => {

        setPage(1);


        setFilters({
            search: "",
            job_family: "",
            experience_level: "",
            job_type: "",
            country: "",
            skill: "",
            remote: "",
        });

    };


    // ======================================================
    // Render
    // ======================================================

    return (

        <main className="job-explorer">


            {/* =================================================
                HEADER
            ================================================= */}

            <div className="explorer-header">

                <div>

                    <p className="eyebrow">
                        JOB MARKET DATASET
                    </p>


                    <h1>
                        Job Explorer
                    </h1>


                    <p className="explorer-description">

                        Search and explore enriched job
                        postings across companies,
                        technologies, locations and
                        job categories.

                    </p>

                </div>


                <div className="result-counter">

                    <strong>
                        {total}
                    </strong>

                    <span>
                        matching jobs
                    </span>

                </div>

            </div>


            {/* =================================================
                FILTERS
            ================================================= */}

            <section className="filter-panel">


                <div className="search-row">

                    <input
                        className="search-input"
                        type="text"
                        name="search"
                        value={filters.search}
                        onChange={handleChange}
                        placeholder={
                            "Search job title or description..."
                        }
                    />


                    <button
                        className="clear-button"
                        type="button"
                        onClick={clearFilters}
                    >
                        Clear filters
                    </button>

                </div>


                <div className="filter-grid">


                    {/* Job Family */}

                    <select
                        name="job_family"
                        value={
                            filters.job_family
                        }
                        onChange={handleChange}
                    >

                        <option value="">
                            All job families
                        </option>


                        {jobFamilies.map(
                            (item) => (

                                <option
                                    key={item.name}
                                    value={item.name}
                                >
                                    {item.name}
                                </option>

                            )
                        )}

                    </select>


                    {/* Experience */}

                    <select
                        name="experience_level"
                        value={
                            filters.experience_level
                        }
                        onChange={handleChange}
                    >

                        <option value="">
                            All experience levels
                        </option>

                        <option value="Entry">
                            Entry
                        </option>

                        <option value="Mid">
                            Mid
                        </option>

                        <option value="Senior">
                            Senior
                        </option>

                        <option value="Lead">
                            Lead
                        </option>

                        <option value="Executive">
                            Executive
                        </option>

                        <option value="Unknown">
                            Unknown
                        </option>

                    </select>


                    {/* Job Type */}

                    <select
                        name="job_type"
                        value={
                            filters.job_type
                        }
                        onChange={handleChange}
                    >

                        <option value="">
                            All job types
                        </option>

                        <option value="Full-time">
                            Full-time
                        </option>

                        <option value="Part-time">
                            Part-time
                        </option>

                        <option value="Contract">
                            Contract
                        </option>

                        <option value="Internship">
                            Internship
                        </option>

                        <option value="Freelance">
                            Freelance
                        </option>

                        <option value="Temporary">
                            Temporary
                        </option>

                        <option value="Unknown">
                            Unknown
                        </option>

                    </select>


                    {/* Country */}

                    <select
                        name="country"
                        value={
                            filters.country
                        }
                        onChange={handleChange}
                    >

                        <option value="">
                            All countries
                        </option>


                        {countries.map(
                            (item) => (

                                <option
                                    key={item.country}
                                    value={item.country}
                                >
                                    {item.country}
                                </option>

                            )
                        )}

                    </select>


                    {/* Skill */}

                    <select
                        name="skill"
                        value={
                            filters.skill
                        }
                        onChange={handleChange}
                    >

                        <option value="">
                            All skills
                        </option>


                        {skills.map(
                            (item) => (

                                <option
                                    key={item.skill}
                                    value={item.skill}
                                >
                                    {item.skill}
                                </option>

                            )
                        )}

                    </select>


                    {/* Remote */}

                    <select
                        name="remote"
                        value={
                            filters.remote
                        }
                        onChange={handleChange}
                    >

                        <option value="">
                            Remote & On-site
                        </option>

                        <option value="true">
                            Remote
                        </option>

                        <option value="false">
                            Non-remote
                        </option>

                    </select>

                </div>

            </section>


            {/* =================================================
                LOADING
            ================================================= */}

            {loading && (

                <div className="status-message">
                    Loading jobs...
                </div>

            )}


            {/* =================================================
                ERROR
            ================================================= */}

            {error && (

                <div className="status-message error">
                    {error}
                </div>

            )}


            {/* =================================================
                NO RESULTS
            ================================================= */}

            {!loading &&
                !error &&
                jobs.length === 0 && (

                    <div className="status-message">

                        No jobs match the selected
                        filters.

                    </div>

                )}


            {/* =================================================
                JOB CARDS
            ================================================= */}

            {!loading &&
                !error &&
                jobs.length > 0 && (

                    <div className="job-grid">


                        {jobs.map((job) => (


                            <article
                                className="job-card"
                                key={job.id}
                            >


                                <div className="job-card-header">


                                    <div>

                                        <h2>
                                            {job.title}
                                        </h2>


                                        <p className="company-name">

                                            {
                                                job.company?.name ||
                                                "Unknown company"
                                            }

                                        </p>

                                    </div>


                                    {job.location?.remote && (

                                        <span className="remote-badge">
                                            Remote
                                        </span>

                                    )}


                                </div>


                                {/* Location */}

                                <p className="job-location">

                                    {
                                        [
                                            job.location?.city,
                                            job.location?.state,
                                            job.location?.country,
                                        ]
                                            .filter(Boolean)
                                            .join(", ") ||
                                        "Location unavailable"
                                    }

                                </p>


                                {/* Metadata */}

                                <div className="job-metadata">

                                    <span>
                                        {
                                            job.job_family ||
                                            "Unclassified"
                                        }
                                    </span>


                                    <span>
                                        {
                                            job.experience_level ||
                                            "Unknown"
                                        }
                                    </span>


                                    <span>
                                        {
                                            job.job_type ||
                                            "Unknown"
                                        }
                                    </span>

                                </div>


                                {/* Skills */}

                                {job.skills?.length > 0 && (

                                    <div className="skill-tags">


                                        {job.skills
                                            .slice(0, 6)
                                            .map(
                                                (skill) => (

                                                    <span
                                                        className="skill-tag"
                                                        key={
                                                            skill.id ??
                                                            skill.name
                                                        }
                                                    >

                                                        {
                                                            skill.name
                                                        }

                                                    </span>

                                                )
                                            )}

                                    </div>

                                )}


                                {/* Internal Details Page */}

                                <Link
                                    className="view-job"
                                    to={
                                        `/jobs/${job.id}`
                                    }
                                >
                                    View job details →
                                </Link>


                            </article>


                        ))}


                    </div>

                )}


            {/* =================================================
                PAGINATION
            ================================================= */}

            {!loading &&
                totalPages > 1 && (

                    <div className="pagination">


                        <button
                            type="button"
                            disabled={
                                page <= 1
                            }
                            onClick={() =>
                                setPage(
                                    (previous) =>
                                        previous - 1
                                )
                            }
                        >
                            Previous
                        </button>


                        <span>
                            Page {page} of {totalPages}
                        </span>


                        <button
                            type="button"
                            disabled={
                                page >= totalPages
                            }
                            onClick={() =>
                                setPage(
                                    (previous) =>
                                        previous + 1
                                )
                            }
                        >
                            Next
                        </button>


                    </div>

                )}


        </main>

    );

}


export default JobExplorer;

