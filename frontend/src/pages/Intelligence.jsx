import {
    useMemo,
    useState,
} from "react";

import {
    askIntelligence,
} from "../api/client";


// ==========================================================
// Example Questions
// ==========================================================

const EXAMPLE_QUESTIONS = [
    "What are the top 5 skills for remote software engineering jobs?",
    "What skills are common in machine learning jobs?",
    "Show me Python machine learning jobs in India.",
    "What technologies are common in DevOps and cloud roles?",
];


// ==========================================================
// Intelligence Page
// ==========================================================

function Intelligence() {

    // ======================================================
    // State
    // ======================================================

    const [question, setQuestion] = useState("");

    const [result, setResult] = useState(null);

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState("");


    // ======================================================
    // Derived Data
    // ======================================================

    const citations = useMemo(
        () => (
            Array.isArray(result?.citations)
                ? result.citations
                : []
        ),
        [result]
    );


    const semanticEvidence = useMemo(
        () => (
            Array.isArray(result?.semantic_evidence)
                ? result.semantic_evidence
                : []
        ),
        [result]
    );


    const filters = useMemo(
        () => (
            result?.filters &&
            typeof result.filters === "object"
                ? result.filters
                : {}
        ),
        [result]
    );


    const skills = useMemo(
        () => (
            Array.isArray(result?.skills)
                ? result.skills
                : []
        ),
        [result]
    );


    // ======================================================
    // Submit
    // ======================================================

    const handleSubmit = async (event) => {

        event.preventDefault();

        const cleanedQuestion = question.trim();

        if (!cleanedQuestion) {

            setError(
                "Enter a job-market question first."
            );

            return;
        }

        setLoading(true);

        setError("");

        try {

            const data = await askIntelligence(
                cleanedQuestion
            );

            setResult(data);

        } catch (requestError) {

            console.error(
                "Intelligence request failed:",
                requestError
            );

            const detail =
                requestError?.response?.data?.detail;

            setError(
                typeof detail === "string"
                    ? detail
                    : (
                        "The intelligence engine could not "
                        + "process the question."
                    )
            );

        } finally {

            setLoading(false);
        }
    };


    // ======================================================
    // Example Question
    // ======================================================

    const useExample = (example) => {

        setQuestion(example);

        setError("");
    };


    // ======================================================
    // Render
    // ======================================================

    return (

        <main className="intelligence-page">

            {/* ==================================================
                Hero
            ================================================== */}

            <section className="intelligence-hero">

                <p className="eyebrow">
                    AI MARKET INTELLIGENCE
                </p>

                <h1>
                    Ask the Job Market
                </h1>

                <p className="intelligence-description">
                    Ask natural-language questions about the
                    collected job market. Answers combine
                    structured database analytics with
                    semantically retrieved job postings.
                </p>

            </section>


            {/* ==================================================
                Query Panel
            ================================================== */}

            <section className="intelligence-query-panel">

                <form
                    className="intelligence-form"
                    onSubmit={handleSubmit}
                >

                    <label htmlFor="intelligence-question">
                        Ask a question
                    </label>

                    <div className="intelligence-input-row">

                        <input
                            id="intelligence-question"
                            type="text"
                            value={question}
                            onChange={(event) =>
                                setQuestion(
                                    event.target.value
                                )
                            }
                            placeholder={
                                "e.g. What skills are most "
                                + "common in machine learning jobs?"
                            }
                            disabled={loading}
                        />

                        <button
                            type="submit"
                            disabled={
                                loading ||
                                !question.trim()
                            }
                        >
                            {
                                loading
                                    ? "Analyzing..."
                                    : "Ask Intelligence"
                            }
                        </button>

                    </div>

                </form>


                <div className="example-questions">

                    <span>
                        Try an example:
                    </span>

                    <div className="example-question-list">

                        {
                            EXAMPLE_QUESTIONS.map(
                                (example) => (

                                    <button
                                        key={example}
                                        type="button"
                                        onClick={() =>
                                            useExample(
                                                example
                                            )
                                        }
                                        disabled={loading}
                                    >
                                        {example}
                                    </button>

                                )
                            )
                        }

                    </div>

                </div>

            </section>


            {/* ==================================================
                Error
            ================================================== */}

            {
                error && (

                    <section className="intelligence-error">

                        <strong>
                            Request failed
                        </strong>

                        <p>
                            {error}
                        </p>

                    </section>
                )
            }


            {/* ==================================================
                Loading
            ================================================== */}

            {
                loading && (

                    <section className="intelligence-state">

                        <div className="intelligence-loader" />

                        <p>
                            Building structured and semantic
                            evidence...
                        </p>

                    </section>
                )
            }


            {/* ==================================================
                Results
            ================================================== */}

            {
                result &&
                !loading && (

                    <section className="intelligence-results">


                        {/* ======================================
                            Question
                        ====================================== */}

                        <div className="intelligence-question-card">

                            <span>
                                QUESTION
                            </span>

                            <h2>
                                {result.question}
                            </h2>

                        </div>


                        {/* ======================================
                            Answer
                        ====================================== */}

                        <article className="answer-card">

                            <div className="answer-card-header">

                                <div>

                                    <p className="answer-label">
                                        AI ANSWER
                                    </p>

                                    <h2>
                                        Market Intelligence
                                    </h2>

                                </div>


                                <ResponseModeBadge
                                    mode={
                                        result.response_mode
                                    }
                                />

                            </div>


                            <div className="answer-content">

                                <FormattedAnswer
                                    answer={
                                        result.answer
                                    }
                                />

                            </div>

                        </article>


                        {/* ======================================
                            Diagnostics
                        ====================================== */}

                        <div className="intelligence-meta-grid">

                            <MetaCard
                                label="Intent"
                                value={
                                    formatIntent(
                                        result.intent
                                    )
                                }
                            />

                            <MetaCard
                                label="Planner Confidence"
                                value={
                                    formatConfidence(
                                        result.confidence
                                    )
                                }
                            />

                            <MetaCard
                                label="Structured Scope"
                                value={
                                    formatNumber(
                                        result.evidence_scope
                                    )
                                }
                            />

                            <MetaCard
                                label="RAG Documents"
                                value={
                                    formatNumber(
                                        result.retrieval_count
                                    )
                                }
                            />

                            <MetaCard
                                label="Citations"
                                value={
                                    formatNumber(
                                        result.citation_count
                                    )
                                }
                            />

                            <MetaCard
                                label="LLM Model"
                                value={
                                    result.llm_model ||
                                    (
                                        result.response_mode
                                        ===
                                        "Deterministic fallback"
                                            ? "Fallback"
                                            : "Unknown"
                                    )
                                }
                            />

                        </div>


                        {/* ======================================
                            Active Filters
                        ====================================== */}

                        {
                            Object.keys(filters).length > 0 && (

                                <section className="evidence-panel">

                                    <div className="evidence-panel-header">

                                        <div>

                                            <p className="answer-label">
                                                QUERY PLAN
                                            </p>

                                            <h2>
                                                Active Filters
                                            </h2>

                                        </div>

                                    </div>


                                    <div className="filter-chip-list">

                                        {
                                            Object.entries(
                                                filters
                                            ).map(
                                                ([key, value]) => (

                                                    <span
                                                        className="filter-chip"
                                                        key={key}
                                                    >
                                                        <strong>
                                                            {
                                                                formatIntent(
                                                                    key
                                                                )
                                                            }
                                                        </strong>

                                                        {" "}

                                                        {
                                                            formatFilterValue(
                                                                value
                                                            )
                                                        }
                                                    </span>

                                                )
                                            )
                                        }

                                    </div>

                                </section>
                            )
                        }


                        {/* ======================================
                            Planner Skills
                        ====================================== */}

                        {
                            skills.length > 0 && (

                                <section className="evidence-panel">

                                    <div className="evidence-panel-header">

                                        <div>

                                            <p className="answer-label">
                                                QUERY PLAN
                                            </p>

                                            <h2>
                                                Requested Skills
                                            </h2>

                                        </div>

                                    </div>


                                    <div className="skill-chip-list">

                                        {
                                            skills.map(
                                                (skill) => (

                                                    <span
                                                        className="skill-chip"
                                                        key={skill}
                                                    >
                                                        {skill}
                                                    </span>

                                                )
                                            )
                                        }

                                    </div>

                                </section>
                            )
                        }


                        {/* ======================================
                            Structured Evidence
                        ====================================== */}

                        <StructuredEvidence
                            evidence={
                                result.evidence
                            }
                        />


                        {/* ======================================
                            Citations
                        ====================================== */}

                        {
                            citations.length > 0 && (

                                <section className="evidence-panel">

                                    <div className="evidence-panel-header">

                                        <div>

                                            <p className="answer-label">
                                                SOURCES
                                            </p>

                                            <h2>
                                                Retrieved Job Sources
                                            </h2>

                                            <p>
                                                Job postings retrieved as
                                                semantic evidence for the
                                                answer.
                                            </p>

                                        </div>


                                        <span className="evidence-count">
                                            {citations.length}
                                        </span>

                                    </div>


                                    <div className="citation-grid">

                                        {
                                            citations.map(
                                                (citation) => (

                                                    <CitationCard
                                                        key={
                                                            citation.citation_id
                                                        }
                                                        citation={
                                                            citation
                                                        }
                                                    />

                                                )
                                            )
                                        }

                                    </div>

                                </section>
                            )
                        }


                        {/* ======================================
                            Semantic Evidence
                        ====================================== */}

                        {
                            semanticEvidence.length > 0 && (

                                <section className="evidence-panel">

                                    <div className="evidence-panel-header">

                                        <div>

                                            <p className="answer-label">
                                                HYBRID RAG
                                            </p>

                                            <h2>
                                                Retrieval Evidence
                                            </h2>

                                            <p>
                                                Ranked semantic evidence
                                                retrieved from the vector
                                                index.
                                            </p>

                                        </div>


                                        <span className="evidence-count">
                                            {
                                                semanticEvidence.length
                                            }
                                        </span>

                                    </div>


                                    <div className="semantic-list">

                                        {
                                            semanticEvidence.map(
                                                (item, index) => (

                                                    <SemanticEvidenceCard
                                                        key={
                                                            item.job_id
                                                            ??
                                                            index
                                                        }
                                                        item={item}
                                                        index={index}
                                                    />

                                                )
                                            )
                                        }

                                    </div>

                                </section>
                            )
                        }


                        {/* ======================================
                            Pipeline
                        ====================================== */}

                        <section className="evidence-panel">

                            <div className="evidence-panel-header">

                                <div>

                                    <p className="answer-label">
                                        SYSTEM
                                    </p>

                                    <h2>
                                        Intelligence Pipeline
                                    </h2>

                                </div>

                            </div>


                            <div className="pipeline-version-grid">

                                <PipelineVersion
                                    label="Planner"
                                    value={
                                        result.planner_version
                                    }
                                />

                                <PipelineVersion
                                    label="Engine"
                                    value={
                                        result.engine_version
                                    }
                                />

                                <PipelineVersion
                                    label="Context"
                                    value={
                                        result.context_version
                                    }
                                />

                                <PipelineVersion
                                    label="Retriever"
                                    value={
                                        result.retrieval_version
                                    }
                                />

                                <PipelineVersion
                                    label="Generator"
                                    value={
                                        result.generator_version
                                    }
                                />

                                <PipelineVersion
                                    label="Citations"
                                    value={
                                        result.citation_version
                                    }
                                />

                                <PipelineVersion
                                    label="Synthesizer"
                                    value={
                                        result.synthesizer_version
                                    }
                                />

                                <PipelineVersion
                                    label="Service"
                                    value={
                                        result.service_version
                                    }
                                />

                            </div>

                        </section>

                    </section>
                )
            }

        </main>
    );
}


// ==========================================================
// Response Mode Badge
// ==========================================================

function ResponseModeBadge({ mode }) {

    const isLLM = (
        mode === "LLM + Hybrid RAG"
    );

    return (

        <span
            className={
                isLLM
                    ? "response-mode-badge llm"
                    : "response-mode-badge fallback"
            }
        >
            {
                mode ||
                "Unknown mode"
            }
        </span>
    );
}


// ==========================================================
// Meta Card
// ==========================================================

function MetaCard({
    label,
    value,
}) {

    return (

        <div className="intelligence-meta-card">

            <span>
                {label}
            </span>

            <strong>
                {
                    value ??
                    "—"
                }
            </strong>

        </div>
    );
}


// ==========================================================
// Formatted Answer
// ==========================================================

function FormattedAnswer({
    answer,
}) {

    if (!answer) {

        return (
            <p>
                No answer was generated.
            </p>
        );
    }

    const lines = String(answer)
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);


    return (

        <div className="formatted-answer">

            {
                lines.map(
                    (line, index) => {

                        const numbered =
                            /^(\d+)\.\s+(.*)$/.exec(
                                line
                            );

                        if (numbered) {

                            return (

                                <div
                                    className="answer-ranked-item"
                                    key={`${line}-${index}`}
                                >

                                    <span>
                                        {numbered[1]}
                                    </span>

                                    <p>
                                        {numbered[2]}
                                    </p>

                                </div>
                            );
                        }

                        return (

                            <p key={`${line}-${index}`}>
                                {line}
                            </p>
                        );
                    }
                )
            }

        </div>
    );
}


// ==========================================================
// Structured Evidence
// ==========================================================

function StructuredEvidence({
    evidence,
}) {

    if (
        !evidence ||
        typeof evidence !== "object"
    ) {

        return null;
    }


    const data = evidence.data;


    return (

        <section className="evidence-panel">

            <div className="evidence-panel-header">

                <div>

                    <p className="answer-label">
                        DATABASE EVIDENCE
                    </p>

                    <h2>
                        Structured Market Evidence
                    </h2>

                    <p>
                        Aggregated evidence produced from the
                        relational job-market database.
                    </p>

                </div>

            </div>


            {
                typeof evidence.total_matching_jobs
                === "number" && (

                    <div className="structured-highlight">

                        <span>
                            Matching Jobs
                        </span>

                        <strong>
                            {
                                evidence.total_matching_jobs
                            }
                        </strong>

                    </div>
                )
            }


            {
                Array.isArray(data) &&
                data.length > 0 && (

                    <div className="structured-table-wrapper">

                        <table className="structured-table">

                            <thead>

                                <tr>

                                    {
                                        Object.keys(
                                            data[0]
                                        ).map(
                                            (key) => (

                                                <th key={key}>
                                                    {
                                                        formatIntent(
                                                            key
                                                        )
                                                    }
                                                </th>

                                            )
                                        )
                                    }

                                </tr>

                            </thead>


                            <tbody>

                                {
                                    data.map(
                                        (row, rowIndex) => (

                                            <tr key={rowIndex}>

                                                {
                                                    Object.keys(
                                                        data[0]
                                                    ).map(
                                                        (key) => (

                                                            <td
                                                                key={
                                                                    key
                                                                }
                                                            >
                                                                {
                                                                    formatCell(
                                                                        row[
                                                                            key
                                                                        ]
                                                                    )
                                                                }
                                                            </td>

                                                        )
                                                    )
                                                }

                                            </tr>

                                        )
                                    )
                                }

                            </tbody>

                        </table>

                    </div>
                )
            }


            {
                data &&
                !Array.isArray(data) &&
                typeof data === "object" && (

                    <div className="structured-object-grid">

                        {
                            Object.entries(
                                data
                            ).map(
                                ([key, value]) => (

                                    <div
                                        className="structured-object-card"
                                        key={key}
                                    >

                                        <span>
                                            {
                                                formatIntent(
                                                    key
                                                )
                                            }
                                        </span>

                                        <strong>
                                            {
                                                formatCell(
                                                    value
                                                )
                                            }
                                        </strong>

                                    </div>

                                )
                            )
                        }

                    </div>
                )
            }

        </section>
    );
}


// ==========================================================
// Citation Card
// ==========================================================

function CitationCard({
    citation,
}) {

    return (

        <article className="citation-card">

            <div className="citation-card-top">

                <span className="citation-number">
                    [{citation.citation_id}]
                </span>

                {
                    citation.hybrid_score != null && (

                        <span className="citation-score">
                            {
                                Number(
                                    citation.hybrid_score
                                ).toFixed(3)
                            }
                        </span>
                    )
                }

            </div>


            <h3>
                {
                    citation.title ||
                    "Unknown job"
                }
            </h3>


            <p className="citation-company">
                {
                    citation.company ||
                    "Unknown company"
                }
            </p>


            <div className="citation-meta">

                {
                    citation.country && (

                        <span>
                            {citation.country}
                        </span>
                    )
                }

                <span>
                    {
                        citation.remote
                            ? "Remote"
                            : "On-site / Hybrid"
                    }
                </span>

                {
                    citation.source && (

                        <span>
                            {citation.source}
                        </span>
                    )
                }

            </div>


            {
                Array.isArray(
                    citation.skills
                ) &&
                citation.skills.length > 0 && (

                    <div className="skill-chip-list compact">

                        {
                            citation.skills
                                .slice(0, 8)
                                .map(
                                    (skill) => (

                                        <span
                                            className="skill-chip"
                                            key={skill}
                                        >
                                            {skill}
                                        </span>

                                    )
                                )
                        }

                    </div>
                )
            }


            <div className="citation-actions">

                {
                    citation.job_id != null && (

                        <a
                            href={`/jobs/${citation.job_id}`}
                            className="citation-link"
                        >
                            View Job
                        </a>
                    )
                }


                {
                    citation.source_url && (

                        <a
                            href={citation.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="citation-link secondary"
                        >
                            Original Source
                        </a>
                    )
                }

            </div>

        </article>
    );
}


// ==========================================================
// Semantic Evidence Card
// ==========================================================

function SemanticEvidenceCard({
    item,
    index,
}) {

    return (

        <article className="semantic-evidence-card">

            <div className="semantic-rank">
                {index + 1}
            </div>


            <div className="semantic-main">

                <div className="semantic-title-row">

                    <div>

                        <h3>
                            {
                                item.title ||
                                "Unknown job"
                            }
                        </h3>

                        <p>
                            {
                                item.company ||
                                "Unknown company"
                            }
                        </p>

                    </div>


                    {
                        item.hybrid_score != null && (

                            <strong className="hybrid-score">

                                {
                                    Number(
                                        item.hybrid_score
                                    ).toFixed(3)
                                }

                            </strong>
                        )
                    }

                </div>


                <div className="semantic-meta">

                    {
                        item.country && (

                            <span>
                                {item.country}
                            </span>
                        )
                    }

                    {
                        item.job_family && (

                            <span>
                                {item.job_family}
                            </span>
                        )
                    }

                    {
                        item.experience_level && (

                            <span>
                                {item.experience_level}
                            </span>
                        )
                    }

                    {
                        typeof item.remote
                        === "boolean" && (

                            <span>
                                {
                                    item.remote
                                        ? "Remote"
                                        : "Not remote"
                                }
                            </span>
                        )
                    }

                </div>


                {
                    Array.isArray(item.skills) &&
                    item.skills.length > 0 && (

                        <div className="skill-chip-list compact">

                            {
                                item.skills
                                    .slice(0, 10)
                                    .map(
                                        (skill) => (

                                            <span
                                                className="skill-chip"
                                                key={skill}
                                            >
                                                {skill}
                                            </span>

                                        )
                                    )
                            }

                        </div>
                    )
                }

            </div>

        </article>
    );
}


// ==========================================================
// Pipeline Version
// ==========================================================

function PipelineVersion({
    label,
    value,
}) {

    return (

        <div className="pipeline-version">

            <span>
                {label}
            </span>

            <code>
                {
                    value ||
                    "—"
                }
            </code>

        </div>
    );
}


// ==========================================================
// Formatting Helpers
// ==========================================================

function formatIntent(value) {

    if (!value) {
        return "Unknown";
    }

    return String(value)
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) =>
            character.toUpperCase()
        );
}


function formatConfidence(value) {

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return `${Math.round(number * 100)}%`;
}


function formatNumber(value) {

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toLocaleString();
}


function formatFilterValue(value) {

    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }

    if (Array.isArray(value)) {
        return value.join(", ");
    }

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "Any";
    }

    return String(value);
}


function formatCell(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "—";
    }

    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }

    if (Array.isArray(value)) {
        return value.join(", ");
    }

    if (typeof value === "object") {
        return JSON.stringify(value);
    }

    if (typeof value === "number") {
        return value.toLocaleString();
    }

    return String(value);
}


export default Intelligence;