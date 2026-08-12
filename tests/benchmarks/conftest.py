import pytest


@pytest.fixture
def large_portfolio():
    """Return a tuple (repos, resume_content) representing a large portfolio.

    Repos are simple dicts compatible with the repo analyzer mocks used in the
    benchmark test. The resume content is bytes to mimic a PDF/text payload.
    """
    resume_content = b"Sample resume content\n" * 100
    repos = []
    for i in range(5):
        repos.append({"name": f"repo{i}", "description": "Sample repo content\n" * 100})

    return repos, resume_content
