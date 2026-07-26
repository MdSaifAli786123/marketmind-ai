import axios from "axios";


// ==========================================================
// Configuration
// ==========================================================

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000";


// ==========================================================
// Axios Client
// ==========================================================

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
});


// ==========================================================
// Analytics
// ==========================================================

export const getOverview = async () => {
    const response = await api.get(
        "/analytics/overview"
    );

    return response.data;
};


export const getJobFamilies = async () => {
    const response = await api.get(
        "/analytics/job-families"
    );

    return response.data;
};


export const getTopSkills = async (limit = 10) => {
    const response = await api.get(
        "/analytics/skills",
        {
            params: {
                limit,
            },
        }
    );

    return response.data;
};


export const getRemoteDistribution = async () => {
    const response = await api.get(
        "/analytics/remote"
    );

    return response.data;
};


export const getExperienceDistribution = async () => {
    const response = await api.get(
        "/analytics/experience"
    );

    return response.data;
};


export const getJobTypeDistribution = async () => {
    const response = await api.get(
        "/analytics/job-types"
    );

    return response.data;
};


export const getCountries = async (limit = 10) => {
    const response = await api.get(
        "/analytics/countries",
        {
            params: {
                limit,
            },
        }
    );

    return response.data;
};


export const getCompanies = async (limit = 10) => {
    const response = await api.get(
        "/analytics/companies",
        {
            params: {
                limit,
            },
        }
    );

    return response.data;
};


// ==========================================================
// Jobs
// ==========================================================

export const getJobs = async (params = {}) => {
    const response = await api.get(
        "/jobs",
        {
            params,
        }
    );

    return response.data;
};


export const getJobById = async (jobId) => {
    const response = await api.get(
        `/jobs/${jobId}`
    );

    return response.data;
};


// ==========================================================
// AI Market Intelligence
// ==========================================================

export const askIntelligence = async (question) => {
    const response = await api.post(
        "/intelligence/ask",
        {
            question,
        }
    );

    return response.data;
};


// ==========================================================
// System / Dataset Status
// ==========================================================

export const getDatasetStatus = async () => {
    const response = await api.get(
        "/system/dataset-status"
    );

    return response.data;
};


// ==========================================================
// Default Export
// ==========================================================

export default api;