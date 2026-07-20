# PathReview

**AI-powered portfolio review assistant** that helps early-career developers strengthen their professional portfolios.

PathReview analyzes GitHub profiles, resumes, and project repositories to generate structured, actionable feedback on portfolio completeness, project quality, skill gaps, and presentation improvements.

## Features

- **Profile Ingestion** — Upload a resume (PDF or Markdown), connect a GitHub profile, and link project repositories
- **RAG-Powered Feedback** — Retrieval-augmented generation produces specific, evidence-based feedback referencing your actual work
- **Multi-Tool Agent** — An AI agent orchestrates GitHub analysis, skill extraction, README scoring, and market comparison
- **Safety Guardrails** — Bias detection, content filtering, PII scrubbing, and prompt injection defense ensure feedback is constructive and safe
- **Web Dashboard** — View results, track improvement over time, and export shareable review summaries

## Quick Start

> **Windows users:** Use [Git Bash](https://git-scm.com/download/win) to run these commands, not PowerShell. See [docs/SETUP.md](docs/SETUP.md) for Windows-specific setup including installing `make`.

```bash
# Clone and enter the repo
git clone https://github.com/ascherj/pathreview.git
cd pathreview

# Configure environment (add your OPENROUTER_API_KEY to .env)
cp .env.example .env

# Start backing services — must be running before make setup
docker compose up -d

# Run first-time setup (installs deps, runs migrations, seeds DB, installs frontend)
make setup

# Start the application
make run
```

Then open http://localhost:5173 in your browser.

For detailed setup instructions including platform-specific notes, see [docs/SETUP.md](docs/SETUP.md).

### Environment Setup: Step Zero

Before choosing an issue or writing code, confirm your baseline:

```mermaid
flowchart TD
    A["Before coding"] --> B["Check 1: App starts"]
    A --> C["Check 2: Tests pass"]
    A --> D["Check 3: Bug is reproducible"]
    B --> B1{"App starts cleanly?"}
    B1 -->|No| B2["Read full error output<br/>missing dependency? env var? service failure?"]
    B1 -->|Yes| E["Baseline partially confirmed"]
    C --> C1{"Existing tests pass?"}
    C1 -->|No| C2["Record failing tests<br/>check issue tracker for known failures"]
    C1 -->|Yes| F["Test baseline confirmed"]
    D --> D1{"Can reproduce issue?"}
    D1 -->|No| D2["Stop before implementing<br/>do not fix unseen bug"]
    D1 -->|Yes| G["Safe to investigate and plan"]
```

## Architecture

PathReview is structured as a multi-service Python + React application with five major subsystems:

| Subsystem | Directory | Description |
|---|---|---|
| API Layer | `api/` | FastAPI REST API with authentication, validation, and rate limiting |
| Ingestion Pipeline | `ingestion/` | Document parsing, chunking, and embedding generation |
| RAG System | `rag/` | Hybrid retrieval, LLM-based review generation, and quality evaluation |
| Agent System | `agent/` | Multi-tool orchestration with planning, state management, and error handling |
| Safety Layer | `safety/` | Content filtering, bias detection, PII scrubbing, and prompt defense |
| Frontend | `frontend/` | React + TypeScript dashboard with Vite |

For a detailed architecture overview, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### System Overview

```mermaid
flowchart TD
    User["User"] --> Frontend["React + TypeScript frontend"]
    Frontend --> ApiClient["frontend/src/services/api.ts"]
    ApiClient --> FastAPI["FastAPI API layer"]
    FastAPI --> Middleware["Middleware"]
    Middleware --> Auth["Authentication"]
    Middleware --> RequestID["Request ID"]
    Middleware --> CORS["CORS"]
    FastAPI --> AuthRoutes["api/routes/auth.py"]
    FastAPI --> ProfileRoutes["api/routes/profiles.py"]
    FastAPI --> ReviewRoutes["api/routes/reviews.py"]
    FastAPI --> HealthRoutes["api/routes/health.py"]
    ProfileRoutes --> ProfileService["core/services/profile_service.py"]
    ReviewRoutes --> ReviewService["core/services/review_service.py"]
    ProfileService --> Models["core/models"]
    ReviewService --> Models
    Models --> DB[("PostgreSQL / async SQLAlchemy database")]
    ReviewService --> Ingestion["Ingestion pipeline"]
    Ingestion --> Parsers["Parsers: resume, README, repo analyzer"]
    Ingestion --> Chunking["Chunking strategies"]
    Ingestion --> Embeddings["Embedding provider and batch processor"]
    ReviewService --> Agent["Agent system"]
    Agent --> GitHubTool["GitHub analysis tool"]
    Agent --> SkillExtractor["Skill extractor"]
    Agent --> ReadmeScorer["README scorer"]
    Agent --> MarketAnalyzer["Market analyzer"]
    Agent --> TechDetector["Tech detector"]
    ReviewService --> RAG["RAG system"]
    RAG --> HybridRetrieval["Hybrid retrieval"]
    HybridRetrieval --> VectorSearch["Vector store"]
    HybridRetrieval --> KeywordSearch["Keyword search"]
    RAG --> Generator["LLM review generator"]
    RAG --> Evaluator["Relevance and faithfulness evaluators"]
    ReviewService --> Safety["Safety layer"]
    Safety --> PromptDefense["Prompt defense"]
    Safety --> ContentFilter["Content filter"]
    Safety --> BiasDetector["Bias detector"]
    Safety --> PIIScrubber["PII scrubber"]
    Safety --> ReviewOutput["Structured portfolio review"]
    ReviewOutput --> Frontend
```

### Frontend Routes and Navigation

```mermaid
flowchart TD
    App["frontend/src/App.tsx"] --> Router["React Router"]
    Router --> PublicRoutes["Public routes"]
    Router --> ProtectedRoutes["Protected routes"]
    PublicRoutes --> Login["LoginPage"]
    PublicRoutes --> Register["RegisterPage"]
    ProtectedRoutes --> NavBar["NavBar"]
    ProtectedRoutes --> Dashboard["DashboardPage"]
    ProtectedRoutes --> NewProfile["NewProfilePage"]
    ProtectedRoutes --> ReviewPage["ReviewPage"]
    ProtectedRoutes --> ReviewHistory["ReviewHistoryPage"]
    Dashboard --> StartReview["Start a New Review button"]
    StartReview --> NewProfilePath["navigate to /profiles/new"]
    Dashboard --> RecentReview["Recent review item"]
    RecentReview --> ReviewPath["navigate to /reviews/{review_id}"]
    Dashboard --> AllReviews["View all reviews link"]
    AllReviews --> ReviewHistoryPath["navigate to /reviews"]
    NewProfile --> BackDashboard1["Back to Dashboard"]
    BackDashboard1 --> DashboardPath1["navigate to /dashboard"]
    NewProfile --> ProfileForm["ProfileForm"]
    ProfileForm --> AfterProfile["onSuccess(profile_id)"]
    AfterProfile --> CreateReview["apiClient.createReview(profile_id)"]
    CreateReview --> ReviewPath2["navigate to /reviews/{review_id}"]
    ReviewPage --> BackDashboard2["Back to Dashboard"]
    BackDashboard2 --> DashboardPath2["navigate to /dashboard"]
```

### Frontend API Client Map

```mermaid
flowchart LR
    subgraph Frontend["React frontend"]
        LoginPage["LoginPage"]
        RegisterPage["RegisterPage"]
        DashboardPage["DashboardPage"]
        NewProfilePage["NewProfilePage"]
        ProfileForm["ProfileForm"]
        ReviewPage["ReviewPage"]
        UseProfileSubmit["useProfileSubmit hook"]
        UseReviewStatus["useReviewStatus hook"]
    end
    subgraph ApiClient["frontend/src/services/api.ts"]
        LoginMethod["login(email, password)"]
        RegisterMethod["register(email, password)"]
        CreateProfile["createProfile(formData)"]
        GetProfile["getProfile(id)"]
        CreateReview["createReview(profileId)"]
        GetReview["getReview(id)"]
        GetReviewStatus["getReviewStatus(id)"]
        ListReviews["listReviews(page, pageSize)"]
        DeleteProfile["deleteProfile(id)"]
    end
    subgraph BackendAPI["FastAPI endpoints expected by frontend"]
        AuthLogin["POST /api/auth/login"]
        AuthRegister["POST /api/auth/register"]
        ProfilesPost["POST /api/profiles"]
        ProfilesGet["GET /api/profiles/{id}"]
        ProfilesDelete["DELETE /api/profiles/{id}"]
        ReviewsPost["POST /api/reviews"]
        ReviewsGet["GET /api/reviews/{id}"]
        ReviewsStatus["GET /api/reviews/{id}/status"]
        ReviewsList["GET /api/reviews?page=...&page_size=..."]
    end
    LoginPage --> LoginMethod --> AuthLogin
    RegisterPage --> RegisterMethod --> AuthRegister
    ProfileForm --> UseProfileSubmit --> CreateProfile --> ProfilesPost
    NewProfilePage --> CreateReview --> ReviewsPost
    DashboardPage --> ListReviews --> ReviewsList
    ReviewPage --> UseReviewStatus --> GetReviewStatus --> ReviewsStatus
    ReviewPage --> GetReview --> ReviewsGet
    GetProfile --> ProfilesGet
    DeleteProfile --> ProfilesDelete
```

### Frontend to FastAPI Request Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as React UI
    participant ApiClient as frontend/src/services/api.ts
    participant FastAPI as api/main.py
    participant Auth as Auth middleware
    participant Routes as FastAPI routes
    participant Services as core/services
    participant DB as Async database
    User->>UI: Log in or register
    UI->>ApiClient: login or register
    ApiClient->>FastAPI: POST /api/auth/login or /api/auth/register
    FastAPI->>Routes: auth router
    Routes-->>ApiClient: JWT access token
    ApiClient-->>UI: Store token in localStorage
    User->>UI: Create profile with GitHub username, resume, optional portfolio URL
    UI->>ApiClient: createProfile(formData)
    ApiClient->>FastAPI: POST /api/profiles with Authorization header
    FastAPI->>Auth: get_current_user
    Auth-->>FastAPI: current user
    FastAPI->>Routes: profiles router
    Routes->>Services: create_profile(...)
    Services->>DB: Insert Profile
    DB-->>Services: Profile saved
    Services-->>Routes: Profile
    Routes-->>ApiClient: ProfileResponse
    ApiClient-->>UI: profile_id
    UI->>ApiClient: createReview(profile_id)
    ApiClient->>FastAPI: POST /api/reviews
    FastAPI->>Auth: get_current_user
    FastAPI->>Routes: reviews router
    Routes->>Services: create_review(...)
    Services->>DB: Insert Review with status pending
    DB-->>Services: Review saved
    Routes-->>ApiClient: ReviewResponse with status pending
    ApiClient-->>UI: review_id
    UI->>UI: Navigate to /reviews/{review_id}
```

### Profile Creation Flow

```mermaid
flowchart TD
    A["User opens NewProfilePage"] --> B["ProfileForm"]
    B --> C["User enters GitHub username"]
    B --> D["User uploads resume file"]
    B --> E["User optionally enters portfolio URL"]
    C --> F["validateForm"]
    D --> F
    E --> F
    F --> G{"Valid input?"}
    G -->|No| H["Show form errors"]
    H --> B
    G -->|Yes| I["Build FormData"]
    I --> I1["github_username"]
    I --> I2["resume file"]
    I --> I3["portfolio_url if present"]
    I --> J["useProfileSubmit.submit(formData)"]
    J --> K["apiClient.createProfile(formData)"]
    K --> L["POST /api/profiles"]
    L --> M["profiles route checks current user"]
    M --> N["Validate resume type PDF or Markdown"]
    N --> O["create_profile service"]
    O --> P["Insert Profile in database"]
    P --> Q["Return ProfileResponse"]
    Q --> R["onSuccess(profile.id)"]
    R --> S["NewProfilePage calls apiClient.createReview(profile.id)"]
    S --> T["POST /api/reviews"]
    T --> U["Create pending review"]
    U --> V["Navigate to /reviews/{review_id}"]
```

### Async Review Processing Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as ReviewPage
    participant ApiClient as apiClient
    participant ReviewRoute as api/routes/reviews.py
    participant ReviewService as core/services/review_service.py
    participant DB as Database
    participant Ingestion as Ingestion pipeline
    participant Agent as Agent orchestration
    participant RAG as RAG retrieval plus generation
    participant Safety as Safety checks
    User->>UI: Start review from NewProfilePage
    UI->>ApiClient: createReview(profile_id)
    ApiClient->>ReviewRoute: POST /reviews
    ReviewRoute->>ReviewService: create_review(profile_id, user_id)
    ReviewService->>DB: Create Review status pending
    DB-->>ReviewService: Saved review
    ReviewRoute-->>ApiClient: Return pending review immediately
    ApiClient-->>UI: Navigate to /reviews/{review_id}
    ReviewRoute->>ReviewService: Schedule process_review in background
    ReviewService->>DB: Set status processing
    ReviewService->>Ingestion: Run ingestion pipeline on profile sources
    Ingestion-->>ReviewService: Ingested source data
    ReviewService->>Agent: Run agent orchestration
    Agent-->>ReviewService: Initial analysis sections and score
    ReviewService->>RAG: Run retrieval plus generation
    RAG-->>ReviewService: Enhanced review output
    ReviewService->>Safety: Run safety checks
    Safety-->>ReviewService: Pass or fail
    alt Safety passes and processing succeeds
        ReviewService->>DB: Set status complete and store sections plus score
    else Error or unsafe output
        ReviewService->>DB: Set status failed and store error_message
    end
    loop While status is pending or processing
        UI->>ApiClient: getReviewStatus(review_id)
        ApiClient->>ReviewRoute: GET /reviews/{review_id}/status
        ReviewRoute->>ReviewService: get_review(...)
        ReviewService->>DB: Query review
        DB-->>ReviewService: status and progress
        ReviewRoute-->>UI: status response
    end
    UI->>ApiClient: getReview(review_id)
    ApiClient->>ReviewRoute: GET /reviews/{review_id}
    ReviewRoute->>ReviewService: get_review(...)
    ReviewService->>DB: Query completed review
    ReviewRoute-->>UI: Full review sections and score
```

## Issue Selection (AI201 Module 3)

Module 3 spans four phases across Weeks 7–10:

```mermaid
stateDiagram-v2
    [*] --> Week7IssueSelection
    Week7IssueSelection --> Week7_8ReproductionPlanning
    Week7_8ReproductionPlanning --> Week8_9BuildPR
    Week8_9BuildPR --> Week10IterationReflection
    Week10IterationReflection --> [*]
    Week7IssueSelection: Choose issue
    Week7IssueSelection: Fork repo
    Week7IssueSelection: Setup commits
    Week7IssueSelection: Issue link plus problem summary
    Week7_8ReproductionPlanning: Reproduce issue locally
    Week7_8ReproductionPlanning: Write markdown plan
    Week7_8ReproductionPlanning: Record short walkthrough
    Week8_9BuildPR: Implement fix iteratively
    Week8_9BuildPR: Add or update tests
    Week8_9BuildPR: Run checks
    Week8_9BuildPR: Submit PR by end of Week 9
    Week10IterationReflection: Respond to review feedback
    Week10IterationReflection: Document what you learned
    Week10IterationReflection: Submit reflection
```

### Week 7 Contribution Workflow

```mermaid
flowchart TD
    A["Start Week 7: PathReview issue selection"] --> B["Fork PathReview repo"]
    B --> C["Clone your fork, not the original repo"]
    C --> D["Add upstream remote"]
    D --> E["Run make setup"]
    E --> F["Run make run"]
    F --> G{"App loads at localhost:5173?"}
    G -->|No| H["Fix setup first<br/>read docs/SETUP.md<br/>inspect error output"]
    H --> E
    G -->|Yes| I["Browse issue tracker by tier"]
    I --> J["Use issue selection checklist"]
    J --> K{"Issue is realistic?"}
    K -->|No| I
    K -->|Yes| L["Comment on issue to claim/check availability"]
    L --> M["Add issue to cohort ledger"]
    M --> N["Create branch using convention"]
    N --> O["Make setup/JOURNAL.md commit"]
    O --> P["Create JOURNAL.md Week 7 section"]
    P --> Q["Submit branch URL ending in /tree/your-branch"]
```

### Five Questions Before You Commit

Screen candidates quickly — five questions, five minutes:

```mermaid
flowchart TD
    A["Candidate GitHub issue"] --> B{"1. Is it actually open?"}
    B -->|No / unclear| Reject1["Skip or verify current state"]
    B -->|Yes| C{"2. Is the scope clear?"}
    C -->|No| Reject2["Skip vague issue"]
    C -->|Yes| D{"3. Is it the right size?"}
    D -->|Too large| Reject3["Avoid scope trap"]
    D -->|Manageable| E{"4. Is maintainer active?"}
    E -->|No activity| Reject4["Proceed cautiously or skip"]
    E -->|Active| F{"5. Does it match your current skill?"}
    F -->|Double learning curve| Reject5["Maybe choose easier tier"]
    F -->|Good fit| Pick["Good candidate issue"]
```

### Reading the Issue Thread

The description is only part of the story — look for these signals:

```mermaid
mindmap
  root((Issue thread signals))
    Maintainer responded
      Direction given
      Active issue
      Worth pursuing
    Linked failed PRs
      Read them
      Show what did not work
      Reveal hidden constraints
    Caution labels
      stale
      blocked
      needs investigation
      Slow down before committing
    Old issue with recent comment
      Could be active
      Could be dead
      Read response pattern
```

### Issue Selection and Contribution Workflow

```mermaid
flowchart TD
    A["Start PathReview contribution"] --> B["Fork repository"]
    B --> C["Clone your fork"]
    C --> D["Add upstream remote"]
    D --> E["Run docker compose up -d"]
    E --> F["Run make setup"]
    F --> G["Run make run"]
    G --> H{"App loads at localhost:5173?"}
    H -->|No| HFix["Fix setup before choosing too deeply"]
    HFix --> E
    H -->|Yes| I["Browse open issues by tier"]
    I --> J["Apply five issue-selection questions"]
    J --> K{"Actually open?"}
    K -->|No| I
    K -->|Yes| L{"Scope clear?"}
    L -->|No| I
    L -->|Yes| M{"Right size?"}
    M -->|No| I
    M -->|Yes| N{"Maintainer active?"}
    N -->|No or stale| I
    N -->|Yes| O{"Matches your current skill level?"}
    O -->|No| I
    O -->|Yes| P["Read issue thread and failed PRs"]
    P --> Q["Comment that you want to work on it"]
    Q --> R["Add issue to cohort ledger"]
    R --> S["Create branch using convention"]
    S --> T["Create JOURNAL.md Week 7 section"]
    T --> U["Make at least one setup or journal commit"]
    U --> V["Push branch to your fork"]
    V --> W["Submit branch URL ending in /tree/{branch}"]
```

### Routing by Issue Label

Use the issue label to narrow where to start in the codebase:

```mermaid
flowchart LR
    Issue["Selected GitHub issue"] --> Symptom{"What kind of symptom?"}
    Symptom --> Parser["Resume or README parsing fails"]
    Symptom --> Chunking["Embedding or chunking problem"]
    Symptom --> Retrieval["Retrieval returns wrong results"]
    Symptom --> API["API endpoint error or wrong status"]
    Symptom --> DBData["Data missing from database"]
    Symptom --> FrontendBug["UI display, form, polling, navigation bug"]
    Symptom --> CI["CI, lint, typecheck, or test failure"]
    Parser --> ParserFiles["Start in ingestion/parsers"]
    Chunking --> ChunkFiles["Start in ingestion/chunking or ingestion/embeddings"]
    Retrieval --> RetrieverFiles["Start in rag/retriever"]
    API --> APIFiles["Start in api/routes and core/services"]
    DBData --> ModelFiles["Start in core/models and alembic"]
    FrontendBug --> FrontendFiles["Start in frontend/src/pages, components, hooks, services"]
    CI --> CIFiles["Start in .github/workflows/ci.yml, pyproject.toml, Makefile"]
```

### Solution Plan Structure

A solution plan is a living document — especially the known-unknowns section:

```mermaid
mindmap
  root((Solution Plan))
    Problem summary
      User perspective
      What is broken or missing
      What success looks like
    Reproduction steps
      Minimum reliable steps
      Input or scenario
      Observed wrong behavior
    Known unknowns
      Specific questions
      Investigation strategy
      Risk areas
    Proposed approach
      Current best hypothesis
      Likely files
      Expected changes
    Scope estimate
      Files
      Tests
      Time range
      Uncertainty
```

## Contributing

We welcome contributions! Please read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) before submitting a pull request.

## Development

```bash
make help          # Show all available commands
make test-unit     # Run unit tests (~30 seconds)
make check         # Run linter + formatter + type checker
make run           # Start the dev servers
```

### Test and CI Coverage

```mermaid
flowchart TD
    Tests["PathReview test and CI coverage"]
    Tests --> CI[".github/workflows/ci.yml"]
    CI --> Lint["lint job"]
    CI --> Typecheck["typecheck job"]
    CI --> Unit["test-unit job"]
    CI --> Integration["test-integration job"]
    CI --> FrontendCI["frontend job"]
    Lint --> Ruff["ruff check"]
    Lint --> Black["black --check"]
    Typecheck --> Mypy["mypy api core ingestion rag agent safety"]
    Unit --> PytestUnit["pytest tests/unit"]
    Unit --> MockLLM["LLM_PROVIDER=mock"]
    Integration --> Postgres["PostgreSQL service"]
    Integration --> Redis["Redis service"]
    Integration --> PytestIntegration["pytest tests/integration"]
    FrontendCI --> NpmCI["cd frontend && npm ci"]
    FrontendCI --> NpmTest["cd frontend && npm test -- --run"]
    Tests --> BackendReviewTests["tests/unit/test_review_service.py"]
    BackendReviewTests --> CreateReviewTests["create_review tests"]
    BackendReviewTests --> GetReviewTests["get_review ownership/query tests"]
    BackendReviewTests --> ListReviewsTests["list_reviews pagination/count/order tests"]
    Tests --> SharedFixtures["tests/conftest.py"]
    SharedFixtures --> ResumeFixture["sample_resume_text"]
    SharedFixtures --> ReadmeFixture["sample_readme_text"]
    Tests --> FrontendTestFiles["Frontend component tests from repo file list"]
    FrontendTestFiles --> ProfileFormTest["ProfileForm.test.tsx"]
    FrontendTestFiles --> ReviewSectionTest["ReviewSection.test.tsx"]
    Tests --> OtherUnitAreas["Additional unit tests from repo file list"]
    OtherUnitAreas --> IngestionTests["resume/readme parsers, chunkers, embeddings"]
    OtherUnitAreas --> RagTests["retrieval, generation parsing, relevance, faithfulness"]
    OtherUnitAreas --> SafetyTests["PII, bias, prompt defense, rate limiting"]
    OtherUnitAreas --> AgentToolTests["readme scorer, skill extractor, tech detector"]
```

## License

MIT
