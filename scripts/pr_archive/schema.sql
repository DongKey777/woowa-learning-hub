PRAGMA foreign_keys = ON;

-- Repository metadata
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT NOT NULL UNIQUE,
    track TEXT,
    mission_name TEXT,
    source_type TEXT NOT NULL DEFAULT 'github-pr',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Current PR snapshot
CREATE TABLE IF NOT EXISTS pull_requests_current (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER NOT NULL,
    github_pr_id INTEGER NOT NULL UNIQUE,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    state TEXT NOT NULL,
    author_login TEXT NOT NULL,
    base_ref_name TEXT,
    head_ref_name TEXT,
    head_sha TEXT,
    mergeable INTEGER,
    mergeable_state TEXT,
    changed_files INTEGER,
    commits_count INTEGER,
    additions INTEGER,
    deletions INTEGER,
    issue_comments_count INTEGER,
    review_comments_count INTEGER,
    created_at TEXT,
    updated_at TEXT,
    closed_at TEXT,
    merged_at TEXT,
    html_url TEXT,
    last_collected_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    is_missing INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (repository_id) REFERENCES repositories(id),
    UNIQUE (repository_id, number)
);

CREATE INDEX IF NOT EXISTS idx_pull_requests_current_repo_state
    ON pull_requests_current(repository_id, state);

CREATE INDEX IF NOT EXISTS idx_pull_requests_current_author
    ON pull_requests_current(author_login);

CREATE INDEX IF NOT EXISTS idx_pull_requests_current_updated_at
    ON pull_requests_current(updated_at);

-- Current file snapshot and latest patch
CREATE TABLE IF NOT EXISTS pull_request_files_current (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_request_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    previous_filename TEXT,
    status TEXT,
    additions INTEGER,
    deletions INTEGER,
    changes_count INTEGER,
    patch_text TEXT,
    patch_hash TEXT,
    is_binary INTEGER NOT NULL DEFAULT 0,
    last_collected_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    is_missing INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests_current(id),
    UNIQUE (pull_request_id, path)
);

CREATE INDEX IF NOT EXISTS idx_pr_files_current_pr
    ON pull_request_files_current(pull_request_id);

CREATE INDEX IF NOT EXISTS idx_pr_files_current_path
    ON pull_request_files_current(path);

-- Current reviews
CREATE TABLE IF NOT EXISTS pull_request_reviews_current (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_request_id INTEGER NOT NULL,
    github_review_id INTEGER NOT NULL UNIQUE,
    reviewer_login TEXT NOT NULL,
    state TEXT NOT NULL,
    body TEXT,
    submitted_at TEXT,
    commit_id TEXT,
    last_collected_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    is_missing INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests_current(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_reviews_current_pr
    ON pull_request_reviews_current(pull_request_id);

CREATE INDEX IF NOT EXISTS idx_pr_reviews_current_reviewer
    ON pull_request_reviews_current(reviewer_login);

-- Current inline review comments
CREATE TABLE IF NOT EXISTS pull_request_review_comments_current (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_request_id INTEGER NOT NULL,
    github_review_id INTEGER,
    github_comment_id INTEGER NOT NULL UNIQUE,
    user_login TEXT NOT NULL,
    path TEXT,
    position INTEGER,
    original_position INTEGER,
    line INTEGER,
    original_line INTEGER,
    start_line INTEGER,
    side TEXT,
    start_side TEXT,
    commit_id TEXT,
    original_commit_id TEXT,
    in_reply_to_github_comment_id INTEGER,
    diff_hunk TEXT,
    body TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT,
    html_url TEXT,
    last_collected_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    is_missing INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests_current(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_review_comments_current_pr
    ON pull_request_review_comments_current(pull_request_id);

CREATE INDEX IF NOT EXISTS idx_pr_review_comments_current_path
    ON pull_request_review_comments_current(path);

CREATE INDEX IF NOT EXISTS idx_pr_review_comments_current_reply
    ON pull_request_review_comments_current(in_reply_to_github_comment_id);

-- Current issue comments on the PR conversation tab
CREATE TABLE IF NOT EXISTS pull_request_issue_comments_current (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_request_id INTEGER NOT NULL,
    github_comment_id INTEGER NOT NULL UNIQUE,
    user_login TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT,
    html_url TEXT,
    last_collected_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    is_missing INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests_current(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_issue_comments_current_pr
    ON pull_request_issue_comments_current(pull_request_id);

-- Synchronization runs
CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    success INTEGER NOT NULL DEFAULT 0,
    pr_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (repository_id) REFERENCES repositories(id)
);

CREATE TABLE IF NOT EXISTS collection_run_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_run_id INTEGER NOT NULL,
    github_pr_number INTEGER,
    stage TEXT NOT NULL,
    error_message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id)
);

-- History: PR body revisions
CREATE TABLE IF NOT EXISTS pull_request_body_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_request_id INTEGER NOT NULL,
    body TEXT,
    body_hash TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests_current(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_body_history_pr
    ON pull_request_body_history(pull_request_id);

-- History: head SHA revisions
CREATE TABLE IF NOT EXISTS pull_request_head_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_request_id INTEGER NOT NULL,
    head_sha TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests_current(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_head_history_pr
    ON pull_request_head_history(pull_request_id);

-- History: file patch revisions
CREATE TABLE IF NOT EXISTS pull_request_file_patch_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_request_file_current_id INTEGER NOT NULL,
    patch_text TEXT,
    patch_hash TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY (pull_request_file_current_id) REFERENCES pull_request_files_current(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_file_patch_history_file
    ON pull_request_file_patch_history(pull_request_file_current_id);

-- History: review comment body revisions
CREATE TABLE IF NOT EXISTS pull_request_review_comment_body_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_comment_current_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    body_hash TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY (review_comment_current_id) REFERENCES pull_request_review_comments_current(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_review_comment_body_history_comment
    ON pull_request_review_comment_body_history(review_comment_current_id);

-- History: state revisions
CREATE TABLE IF NOT EXISTS pull_request_state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pull_request_id INTEGER NOT NULL,
    state TEXT NOT NULL,
    mergeable INTEGER,
    mergeable_state TEXT,
    captured_at TEXT NOT NULL,
    FOREIGN KEY (pull_request_id) REFERENCES pull_requests_current(id)
);

CREATE INDEX IF NOT EXISTS idx_pr_state_history_pr
    ON pull_request_state_history(pull_request_id);

-- Full text search tables
CREATE VIRTUAL TABLE IF NOT EXISTS pr_body_fts USING fts5(
    pull_request_id UNINDEXED,
    title,
    body
);

CREATE VIRTUAL TABLE IF NOT EXISTS review_comment_fts USING fts5(
    review_comment_id UNINDEXED,
    path,
    body,
    diff_hunk
);

CREATE VIRTUAL TABLE IF NOT EXISTS patch_fts USING fts5(
    pull_request_file_id UNINDEXED,
    path,
    patch_text
);
