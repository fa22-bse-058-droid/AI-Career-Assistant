"""
Tests for CV Analyzer logic (no Django dependencies needed for these).
"""
import pytest
from apps.cv_analyzer.analyzer import (
    extract_skills_from_text,
    extract_sections,
    compute_cv_score,
    compute_skill_gaps,
    validate_magic_bytes,
)


class TestExtractSkills:
    def test_extracts_programming_languages(self):
        text = "I have experience with Python, JavaScript, and TypeScript."
        result = extract_skills_from_text(text)
        assert "Python" in result["all"]
        assert "JavaScript" in result["all"]
        assert "TypeScript" in result["all"]

    def test_extracts_by_category(self):
        text = "Proficient in React, Django, MySQL, and Docker."
        result = extract_skills_from_text(text)
        assert "web_frontend" in result["by_category"]
        assert "web_backend" in result["by_category"]

    def test_case_insensitive(self):
        text = "PYTHON django REACT"
        result = extract_skills_from_text(text)
        assert len(result["all"]) >= 3

    def test_empty_text(self):
        result = extract_skills_from_text("")
        assert result["all"] == []
        assert result["by_category"] == {}


class TestExtractSections:
    def test_detects_contact(self):
        text = "Email: test@example.com\nPhone: 123-456-7890"
        sections = extract_sections(text)
        assert sections["contact"] is True

    def test_detects_experience(self):
        text = "Work Experience\nSoftware Engineer at XYZ"
        sections = extract_sections(text)
        assert sections["experience"] is True

    def test_detects_education(self):
        text = "Education\nBS Computer Science, University of XYZ"
        sections = extract_sections(text)
        assert sections["education"] is True

    def test_missing_sections(self):
        text = "Random text without any standard sections"
        sections = extract_sections(text)
        assert sections["contact"] is False


class TestComputeCVScore:
    def test_score_in_range(self):
        text = "Python Django React AWS Docker Git Email: test@example.com Experience Education Skills Summary"
        skills = extract_skills_from_text(text)
        sections = extract_sections(text)
        scores = compute_cv_score(text, skills, sections)
        assert 0 <= scores["overall"] <= 100
        assert 0 <= scores["keyword_relevance"] <= 100
        assert 0 <= scores["completeness"] <= 100
        assert 0 <= scores["skill_density"] <= 100
        assert 0 <= scores["formatting"] <= 100

    def test_empty_cv_low_score(self):
        text = "Hello"
        skills = extract_skills_from_text(text)
        sections = extract_sections(text)
        scores = compute_cv_score(text, skills, sections)
        assert scores["overall"] < 50

    def test_strong_cv_higher_score(self):
        text = (
            "Email: dev@example.com Summary: Full-stack developer "
            "Experience: 3 years at Tech Corp Education: BS CS "
            "Skills: Python Django React TypeScript Docker AWS Git MySQL Redis "
            "Kubernetes Terraform " * 5
        )
        skills = extract_skills_from_text(text)
        sections = extract_sections(text)
        scores = compute_cv_score(text, skills, sections)
        assert scores["overall"] > 50


class TestComputeSkillGaps:
    def test_identifies_missing_skills(self):
        user_skills = ["Python", "Django"]
        gaps = compute_skill_gaps(user_skills, "Full Stack Developer")
        assert "Full Stack Developer" in gaps
        gap = gaps["Full Stack Developer"]
        assert "React" in gap["missing_required"]
        assert "MySQL" in gap["missing_required"]

    def test_no_gaps_when_all_covered(self):
        user_skills = ["React", "Node.js", "MySQL", "Docker", "Git",
                       "TypeScript", "Redis", "AWS", "Kubernetes"]
        gaps = compute_skill_gaps(user_skills, "Full Stack Developer")
        # Full Stack Developer: required = React, Node.js, MySQL, Docker, Git
        if "Full Stack Developer" in gaps:
            assert len(gaps["Full Stack Developer"].get("missing_required", [])) == 0

    def test_all_roles_when_no_target(self):
        user_skills = ["Python"]
        gaps = compute_skill_gaps(user_skills)
        assert len(gaps) > 1

    def test_match_percentage_included(self):
        user_skills = ["Python", "Django"]
        gaps = compute_skill_gaps(user_skills, "Full Stack Developer")
        assert "Full Stack Developer" in gaps
        gap = gaps["Full Stack Developer"]
        assert "match_percentage" in gap
        assert 0 <= gap["match_percentage"] <= 100

    def test_match_percentage_correct(self):
        # Backend Developer required: Python, Django, MySQL, REST API, Git (5 total)
        # User has Python and Django → 2 matched → 40%
        user_skills = ["Python", "Django"]
        gaps = compute_skill_gaps(user_skills, "Backend Developer")
        assert "Backend Developer" in gaps
        gap = gaps["Backend Developer"]
        assert gap["matched_required"] == 2
        assert gap["total_required"] == 5
        assert gap["match_percentage"] == 40


class TestValidateMagicBytes:
    def test_valid_pdf(self):
        assert validate_magic_bytes(b"%PDF-1.4 rest of content", "test.pdf") is True

    def test_invalid_pdf(self):
        assert validate_magic_bytes(b"Not a PDF", "test.pdf") is False

    def test_valid_docx(self):
        assert validate_magic_bytes(b"PK\x03\x04 rest of zip", "test.docx") is True

    def test_invalid_docx(self):
        assert validate_magic_bytes(b"Not a zip", "test.docx") is False
