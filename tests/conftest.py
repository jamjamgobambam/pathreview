"""Shared test fixtures for PathReview."""

import logging
import structlog
import pytest


@pytest.fixture
def sample_resume_text() -> str:
    """Return a sample resume text for testing."""
    return """
    Jane Doe
    Software Engineer
    jane.doe@example.com | github.com/janedoe

    Experience:
    - Software Engineer at TechCorp (2022-2024)
      Built REST APIs using Python and FastAPI.

    Education:
    - B.S. Computer Science, State University (2022)

    Skills: Python, JavaScript, React, PostgreSQL, Docker
    """


@pytest.fixture
def sample_readme_text() -> str:
    """Return a sample README text for testing."""
    return """
    # Weather App
    A weather forecasting application built with React and OpenWeatherMap API.

    ## Features
    - Current weather display
    - 5-day forecast
    - Location search

    ## Tech Stack
    - React 18
    - TypeScript
    - Tailwind CSS
    - OpenWeatherMap API
    """
def _test_loggings(text:str):
  
      logger=logging.Logger(__name__)
      other_logger = logging.getLogger("path_review") # This is the one that works
      if not text:
          logger.error("Text is missing code 1")
          other_logger.error('Text is missing code 2')
          return False
      logger.error("Text exist code 1")
      other_logger.error('Text exist code 2')
      return True

def _test_structlogs(text:str):
  
      logger=structlog.getLogger(__name__)
      other_logger = structlog.get_logger("path_review") # This is the one that works
      if not text:
          logger.error(event="Text is missing code 1")
          other_logger.error(event='Text is missing code 2')
          return False
      logger.error("Text exist code 1")
      other_logger.error('Text exist code 2')
      return True
    
    
class TestConfigs:
    """Test suite for validating fixtures and log outputs."""
    
    def test_text(self, caplog):
      t = _test_structlogs("")
      print(f"TEXT: {caplog.text}")
      assert "missing" in caplog.event
      assert "missing" in caplog.text
      
      assert 1 == 2
      
    def test_config_with_caplog(
        self, 
        sample_resume_text: str, 
        sample_readme_text: str, 
        caplog
    ) -> None:
        """Validate sample texts and verify logging behavior using caplog."""
        # Set the logging level to capture debug/info logs if needed
        caplog.set_level(logging.INFO)

        logger = logging.getLogger("path_review")
        logger.info("Processing resume for %s", "Jane Doe")

        assert "Jane Doe" in sample_resume_text
        assert "# Weather App" in sample_readme_text

        assert "Processing resume for Jane Doe" in caplog.text