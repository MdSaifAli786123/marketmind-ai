from pipeline.enrichment.semantic_classifier import (
    SemanticJobClassifier,
)


def main() -> None:
    classifier = SemanticJobClassifier()

    test_jobs = [
        {
            "title": "Senior Machine Learning Engineer",
            "description": (
                "Build and deploy machine learning models for "
                "recommendation systems. Work with PyTorch, model "
                "training, inference pipelines and production ML systems."
            ),
            "skills": [
                "python",
                "pytorch",
                "machine learning",
                "mlops",
            ],
        },
        {
            "title": "Generative AI Engineer",
            "description": (
                "Develop enterprise applications using large language "
                "models, retrieval augmented generation, vector databases, "
                "AI agents and prompt engineering."
            ),
            "skills": [
                "llm",
                "rag",
                "langchain",
                "python",
            ],
        },
        {
            "title": "Backend Software Engineer",
            "description": (
                "Design backend APIs and distributed services using "
                "Python, FastAPI, PostgreSQL and Docker."
            ),
            "skills": [
                "python",
                "fastapi",
                "postgresql",
                "docker",
            ],
        },
        {
            "title": "Data Engineer",
            "description": (
                "Build scalable ETL pipelines, data warehouses and "
                "distributed data processing infrastructure."
            ),
            "skills": [
                "spark",
                "airflow",
                "sql",
                "etl",
            ],
        },
        {
            "title": "Cloud DevOps Engineer",
            "description": (
                "Manage Kubernetes infrastructure, CI/CD pipelines, "
                "Terraform and cloud deployment systems."
            ),
            "skills": [
                "kubernetes",
                "terraform",
                "docker",
                "aws",
            ],
        },
        {
            "title": "Clinical Pharmacist",
            "description": (
                "Provide pharmaceutical care, medication reviews and "
                "clinical support to patients."
            ),
            "skills": [
                "pharmacy",
                "clinical care",
                "medication management",
            ],
        },
        {
            "title": "Senior Data Scientist",
            "description": (
                "Develop statistical models, experiments and predictive "
                "analytics solutions using Python and data science methods."
            ),
            "skills": [
                "python",
                "statistics",
                "data science",
            ],
        },
        {
            "title": "Cybersecurity Analyst",
            "description": (
                "Investigate security incidents, monitor threats and "
                "support vulnerability management and security operations."
            ),
            "skills": [
                "cybersecurity",
                "siem",
                "security operations",
            ],
        },
    ]

    print("\nSEMANTIC CLASSIFIER TEST")
    print("=" * 75)

    for index, job in enumerate(test_jobs, start=1):
        result = classifier.classify(
            title=job["title"],
            description=job["description"],
            skills=job["skills"],
        )

        print(f"\n{index}. {job['title']}")
        print(f"   Family     : {result.family}")
        print(f"   Confidence : {result.confidence:.4f}")
        print(f"   Accepted   : {result.accepted}")

    print("\n" + "=" * 75)
    print("Test complete.")


if __name__ == "__main__":
    main()