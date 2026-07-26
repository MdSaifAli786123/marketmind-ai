import {
    useEffect,
    useState,
} from "react";

import {
    Link,
    useParams,
} from "react-router-dom";

import {
    getJobById,
} from "../api/client";


function JobDetail() {

    const { jobId } = useParams();


    const [job, setJob] =
        useState(null);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");


    // ======================================================
    // Load Job
    // ======================================================

    useEffect(() => {

        async function loadJob() {

            setLoading(true);
            setError("");


            try {

                const data =
                    await getJobById(jobId);


                setJob(data);

            } catch (err) {

                console.error(
                    "Failed to load job:",
                    err
                );


                if (
                    err.response?.status === 404
                ) {

                    setError(
                        "This job could not be found."
                    );

                } else {

                    setError(
                        "Unable to load the job details."
                    );

                }

            } finally {

                setLoading(false);

            }

        }


        loadJob();

    }, [jobId]);


    // ======================================================
    // Loading
    // ======================================================

    if (loading) {

        return (

            <div className="status-screen">
                Loading job details...
            </div>

        );

    }


    // ======================================================
    // Error
    // ======================================================

    if (error) {

        return (

            <main className="job-detail-page">


                <Link
                    to="/jobs"
                    className="back-link"
                >
                    ← Back to Job Explorer
                </Link>


                <div className="status-message error">
                    {error}
                </div>


            </main>

        );

    }


    if (!job) {
        return null;
    }


    // ======================================================
    // Location
    // ======================================================

    const locationText = [

        job.location?.city,
        job.location?.state,
        job.location?.country,

    ]
        .filter(Boolean)
        .join(", ");


    // ======================================================
    // Posted Date
    // ======================================================

    let postedDate =
        "Not available";


    if (job.posted_at) {

        const date =
            new Date(job.posted_at);


        if (
            !Number.isNaN(
                date.getTime()
            )
        ) {

            postedDate =
                date.toLocaleDateString(
                    undefined,
                    {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                    }
                );

        }

    }


    // ======================================================
    // Render
    // ======================================================

    return (

        <main className="job-detail-page">


            {/* Back */}

            <Link
                to="/jobs"
                className="back-link"
            >
                ← Back to Job Explorer
            </Link>


            {/* =================================================
                HERO
            ================================================= */}

            <section className="job-detail-hero">


                <div className="job-detail-heading">


                    <div>

                        <p className="eyebrow">
                            JOB DETAILS
                        </p>


                        <h1>
                            {job.title}
                        </h1>


                        <p className="job-detail-company">

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


                <div className="job-detail-location">

                    {
                        locationText ||
                        "Location unavailable"
                    }

                </div>


            </section>


            {/* =================================================
                POSITION OVERVIEW
            ================================================= */}

            <section className="job-detail-section">


                <div className="job-detail-section-header">

                    <h2>
                        Position Overview
                    </h2>

                    <p>
                        Structured information extracted
                        from this job posting.
                    </p>

                </div>


                <div className="job-detail-metadata">


                    <MetadataItem
                        label="Job Family"
                        value={
                            job.job_family ||
                            "Unclassified"
                        }
                    />


                    <MetadataItem
                        label="Experience"
                        value={
                            job.experience_level ||
                            "Unknown"
                        }
                    />


                    <MetadataItem
                        label="Job Type"
                        value={
                            job.job_type ||
                            "Unknown"
                        }
                    />


                    <MetadataItem
                        label="Posted"
                        value={postedDate}
                    />


                    <MetadataItem
                        label="Source"
                        value={
                            job.source ||
                            "Unknown"
                        }
                    />


                    <MetadataItem
                        label="Work Mode"
                        value={
                            job.location?.remote
                                ? "Remote"
                                : "On-site / Hybrid"
                        }
                    />


                </div>


            </section>


            {/* =================================================
                SKILLS
            ================================================= */}

            <section className="job-detail-section">


                <div className="job-detail-section-header">

                    <h2>
                        Skills
                    </h2>

                    <p>
                        Normalized skills associated
                        with this position.
                    </p>

                </div>


                {job.skills?.length > 0 ? (


                    <div className="detail-skill-tags">


                        {job.skills.map(
                            (skill) => (

                                <span
                                    className="detail-skill-tag"
                                    key={
                                        skill.id ??
                                        skill.name
                                    }
                                >
                                    {skill.name}
                                </span>

                            )
                        )}


                    </div>


                ) : (


                    <p className="detail-empty-text">

                        No normalized skills were
                        extracted for this job.

                    </p>


                )}


            </section>


            {/* =================================================
                DESCRIPTION
            ================================================= */}

            <section className="job-detail-section">


                <div className="job-detail-section-header">

                    <h2>
                        Job Description
                    </h2>

                    <p>
                        Cleaned description from
                        the collected posting.
                    </p>

                </div>


                <div className="job-description">

                    {
                        job.description ||
                        "No description is available."
                    }

                </div>


            </section>


            {/* =================================================
                ORIGINAL POSTING
            ================================================= */}

            {job.source_url && (

                <div className="job-detail-actions">

                    <a
                        href={job.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="primary-action"
                    >
                        View Original Posting
                    </a>

                </div>

            )}


        </main>

    );

}


// ==========================================================
// Metadata Item
// ==========================================================

function MetadataItem({
    label,
    value,
}) {

    return (

        <div className="metadata-item">


            <span className="metadata-label">
                {label}
            </span>


            <strong>
                {value}
            </strong>


        </div>

    );

}


export default JobDetail;