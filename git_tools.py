"""
Git automation tools for version control workflows.
Integrates with MCP server for automated commit, push, and PR operations.
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class GitStatus:
    """Represents the current git repository status."""
    is_clean: bool
    staged_files: List[str]
    unstaged_files: List[str]
    conflicts: List[str]
    current_branch: str
    untracked_files: List[str]


@dataclass
class CommitResult:
    """Result of a git commit operation."""
    success: bool
    message: str
    commit_hash: Optional[str] = None


@dataclass
class PullRequestResult:
    """Result of a pull request creation."""
    success: bool
    message: str
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None


class GitToolsError(Exception):
    """Base exception for git tool errors."""
    pass


class GitAutomation:
    """Handles automated git operations for the MCP server."""

    def __init__(self, repo_path: str = "."):
        """
        Initialize GitAutomation with repository path.
        
        Args:
            repo_path: Path to the git repository (default: current directory)
        """
        self.repo_path = Path(repo_path)
        self._validate_repo()

    def _validate_repo(self) -> None:
        """Validate that the path is a valid git repository."""
        try:
            self._run_git(["rev-parse", "--git-dir"])
        except subprocess.CalledProcessError:
            raise GitToolsError(f"Not a valid git repository: {self.repo_path}")

    def _run_git(self, args: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Run a git command and return exit code, stdout, stderr.
        
        Args:
            args: List of git command arguments
            capture_output: Whether to capture output
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            raise GitToolsError(f"Git command timed out: {' '.join(cmd)}")
        except Exception as e:
            raise GitToolsError(f"Git command failed: {e}")

    def git_status(self) -> GitStatus:
        """
        Get current git repository status.
        
        Returns:
            GitStatus object with current state
            
        Raises:
            GitToolsError: If git command fails
        """
        # Get status in porcelain format
        returncode, stdout, stderr = self._run_git(["status", "--porcelain"])
        if returncode != 0:
            raise GitToolsError(f"Failed to get git status: {stderr}")

        staged_files = []
        unstaged_files = []
        conflicts = []
        untracked_files = []

        for line in stdout.split("\n"):
            if not line:
                continue
            status = line[:2]
            filename = line[3:]

            # Check for merge conflicts
            if status in ("UU", "AA", "DD", "DU", "UD"):
                conflicts.append(filename)
            # Staged changes
            elif status[0] in ("M", "A", "D", "R"):
                staged_files.append(filename)
            # Unstaged changes
            elif status[1] in ("M", "D"):
                unstaged_files.append(filename)
            # Untracked files
            elif status == "??":
                untracked_files.append(filename)

        # Get current branch
        returncode, branch, stderr = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        current_branch = branch if returncode == 0 else "unknown"

        is_clean = len(staged_files) == 0 and len(unstaged_files) == 0 and len(conflicts) == 0

        return GitStatus(
            is_clean=is_clean,
            staged_files=staged_files,
            unstaged_files=unstaged_files,
            conflicts=conflicts,
            current_branch=current_branch,
            untracked_files=untracked_files
        )

    def git_add_all(self, exclude_patterns: Optional[List[str]] = None) -> Dict:
        """
        Stage all changes with intelligent filtering.
        Excludes build artifacts and temporary files by default.
        
        Args:
            exclude_patterns: List of glob patterns to exclude (e.g., ['*.class', 'target/*'])
            
        Returns:
            Dict with staging result
        """
        if exclude_patterns is None:
            exclude_patterns = [
                "target/*",
                "build/*",
                "__pycache__/*",
                "*.class",
                "*.pyc",
                "*.egg-info/*",
                ".pytest_cache/*",
                ".coverage",
                "*.o",
                "*.so",
                "node_modules/*"
            ]

        try:
            # First, get all modified files
            returncode, stdout, stderr = self._run_git(["status", "--porcelain"])
            if returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to get status: {stderr}",
                    "staged_count": 0
                }

            files_to_add = []
            for line in stdout.split("\n"):
                if not line:
                    continue
                filename = line[3:]

                # Skip files matching exclude patterns
                should_exclude = any(
                    self._matches_pattern(filename, pattern)
                    for pattern in exclude_patterns
                )

                if not should_exclude and filename:
                    files_to_add.append(filename)

            if not files_to_add:
                return {
                    "success": True,
                    "message": "No files to stage (all changes filtered)",
                    "staged_count": 0,
                    "excluded_patterns": exclude_patterns
                }

            # Stage the files
            returncode, stdout, stderr = self._run_git(["add"] + files_to_add)
            if returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to stage files: {stderr}",
                    "staged_count": 0
                }

            return {
                "success": True,
                "message": f"Successfully staged {len(files_to_add)} file(s)",
                "staged_count": len(files_to_add),
                "staged_files": files_to_add,
                "excluded_patterns": exclude_patterns
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error staging files: {str(e)}",
                "staged_count": 0
            }

    def git_commit(self, message: str, coverage_stats: Optional[Dict] = None) -> CommitResult:
        """
        Automated commit with standardized messages and optional coverage stats.
        
        Args:
            message: Commit message
            coverage_stats: Optional coverage statistics to include in commit
            
        Returns:
            CommitResult with commit details
        """
        try:
            # Build commit message with coverage stats if provided
            full_message = message
            if coverage_stats:
                full_message += "\n\n"
                full_message += self._format_coverage_stats(coverage_stats)

            # Verify we have staged changes
            status = self.git_status()
            if not status.staged_files:
                return CommitResult(
                    success=False,
                    message="No staged changes to commit"
                )

            # Perform the commit
            returncode, stdout, stderr = self._run_git(["commit", "-m", full_message])
            if returncode != 0:
                return CommitResult(
                    success=False,
                    message=f"Commit failed: {stderr}"
                )

            # Extract commit hash from output
            commit_hash = self._extract_commit_hash(stdout)

            return CommitResult(
                success=True,
                message=f"Commit successful: {message}",
                commit_hash=commit_hash
            )

        except Exception as e:
            return CommitResult(
                success=False,
                message=f"Error during commit: {str(e)}"
            )

    def git_push(self, remote: str = "origin", branch: Optional[str] = None) -> Dict:
        """
        Push to remote with upstream configuration.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch to push (default: current branch)
            
        Returns:
            Dict with push result
        """
        try:
            # Get current branch if not specified
            if branch is None:
                status = self.git_status()
                branch = status.current_branch

            # Configure upstream and push
            returncode, stdout, stderr = self._run_git(
                ["push", "-u", remote, branch]
            )

            if returncode != 0:
                return {
                    "success": False,
                    "message": f"Push failed: {stderr}",
                    "remote": remote,
                    "branch": branch
                }

            return {
                "success": True,
                "message": f"Successfully pushed {branch} to {remote}",
                "remote": remote,
                "branch": branch,
                "output": stdout
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error during push: {str(e)}",
                "remote": remote,
                "branch": branch
            }

    def git_pull_request(
        self,
        base: str = "main",
        title: Optional[str] = None,
        body: Optional[str] = None,
        coverage_stats: Optional[Dict] = None
    ) -> PullRequestResult:
        """
        Create a pull request via GitHub CLI.
        Requires 'gh' CLI to be installed and authenticated.
        
        Args:
            base: Base branch for PR (default: main)
            title: PR title
            body: PR body/description
            coverage_stats: Optional coverage statistics to include
            
        Returns:
            PullRequestResult with PR details
        """
        try:
            # Check if gh CLI is installed
            if not self._check_command_exists("gh"):
                return PullRequestResult(
                    success=False,
                    message="GitHub CLI (gh) is not installed or not in PATH. "
                    "Install from https://cli.github.com/"
                )

            # Get current branch
            status = self.git_status()
            current_branch = status.current_branch

            if current_branch == "main" or current_branch == "master":
                return PullRequestResult(
                    success=False,
                    message=f"Cannot create PR from {current_branch} branch. "
                    "Create a feature branch first."
                )

            # Build PR body with coverage stats if provided
            pr_body = body or "Automated PR from testing agent"
            if coverage_stats:
                pr_body += "\n\n## Coverage Statistics\n"
                pr_body += self._format_coverage_stats(coverage_stats)

            # Create PR using GitHub CLI
            returncode, stdout, stderr = self._run_git(
                ["credential", "helpers"]  # Just verify credentials are available
            )

            # Use gh CLI to create PR
            cmd = [
                "gh", "pr", "create",
                "--base", base,
                "--title", title or f"Merge {current_branch} into {base}",
                "--body", pr_body,
                "--head", current_branch
            ]

            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    return PullRequestResult(
                        success=False,
                        message=f"Failed to create PR: {result.stderr}"
                    )

                # Extract PR URL and number from output
                pr_url = self._extract_pr_url(result.stdout)
                pr_number = self._extract_pr_number(pr_url)

                return PullRequestResult(
                    success=True,
                    message=f"PR created successfully: {title or current_branch}",
                    pr_url=pr_url,
                    pr_number=pr_number
                )

            except FileNotFoundError:
                return PullRequestResult(
                    success=False,
                    message="GitHub CLI (gh) not found. Install from https://cli.github.com/"
                )

        except Exception as e:
            return PullRequestResult(
                success=False,
                message=f"Error creating PR: {str(e)}"
            )

    # Helper methods
    @staticmethod
    def _matches_pattern(filename: str, pattern: str) -> bool:
        """Check if filename matches a glob pattern."""
        from fnmatch import fnmatch
        return fnmatch(filename, pattern)

    @staticmethod
    def _format_coverage_stats(stats: Dict) -> str:
        """Format coverage statistics for commit/PR message."""
        lines = []
        if isinstance(stats, dict):
            for key, value in stats.items():
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else ""

    @staticmethod
    def _extract_commit_hash(output: str) -> Optional[str]:
        """Extract commit hash from git output."""
        match = re.search(r"\[.*?(\b[a-f0-9]{7}\b)\]", output)
        return match.group(1) if match else None

    @staticmethod
    def _extract_pr_url(output: str) -> str:
        """Extract PR URL from gh CLI output."""
        match = re.search(r"https://github\.com/[\w-]+/[\w-]+/pull/\d+", output)
        return match.group(0) if match else output.strip()

    @staticmethod
    def _extract_pr_number(pr_url: str) -> Optional[int]:
        """Extract PR number from URL."""
        match = re.search(r"/pull/(\d+)", pr_url)
        return int(match.group(1)) if match else None

    @staticmethod
    def _check_command_exists(command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(
                ["where" if subprocess.os.name == "nt" else "which", command],
                capture_output=True,
                timeout=5
            )
            return True
        except Exception:
            return False


class WorkflowIntegration:
    """Integrates git operations with testing workflows."""

    def __init__(self, repo_path: str = "."):
        self.git = GitAutomation(repo_path)

    def commit_on_coverage_threshold(
        self,
        current_coverage: float,
        threshold: float,
        coverage_stats: Optional[Dict] = None
    ) -> CommitResult:
        """
        Automatically commit if coverage threshold is met.
        
        Args:
            current_coverage: Current coverage percentage
            threshold: Required coverage threshold
            coverage_stats: Coverage statistics to include
            
        Returns:
            CommitResult
        """
        if current_coverage >= threshold:
            message = f"chore: coverage improved to {current_coverage:.1f}%"
            return self.git.git_commit(message, coverage_stats)
        else:
            return CommitResult(
                success=False,
                message=f"Coverage {current_coverage:.1f}% below threshold {threshold:.1f}%"
            )

    def automated_workflow(
        self,
        commit_message: str,
        push_remote: str = "origin",
        create_pr: bool = False,
        pr_base: str = "main",
        pr_title: Optional[str] = None,
        coverage_stats: Optional[Dict] = None
    ) -> Dict:
        """
        Execute full automated workflow: stage → commit → push → (optional) PR.
        
        Args:
            commit_message: Message for the commit
            push_remote: Remote to push to
            create_pr: Whether to create a PR
            pr_base: Base branch for PR
            pr_title: Title for PR
            coverage_stats: Coverage statistics
            
        Returns:
            Dict with workflow results
        """
        results = {}

        # Stage changes
        stage_result = self.git.git_add_all()
        results["stage"] = stage_result
        if not stage_result["success"]:
            return results

        # Commit
        commit_result = self.git.git_commit(commit_message, coverage_stats)
        results["commit"] = {
            "success": commit_result.success,
            "message": commit_result.message,
            "hash": commit_result.commit_hash
        }
        if not commit_result.success:
            return results

        # Push
        push_result = self.git.git_push(remote=push_remote)
        results["push"] = push_result
        if not push_result["success"]:
            return results

        # Create PR if requested
        if create_pr:
            pr_result = self.git.git_pull_request(
                base=pr_base,
                title=pr_title,
                coverage_stats=coverage_stats
            )
            results["pr"] = {
                "success": pr_result.success,
                "message": pr_result.message,
                "url": pr_result.pr_url,
                "number": pr_result.pr_number
            }

        return results
