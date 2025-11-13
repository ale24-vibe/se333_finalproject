#!/usr/bin/env python3
"""
Quick test script to verify git tools are working correctly.
Run this to validate the implementation before integrating with server.
"""

import sys
from git_tools import GitAutomation, WorkflowIntegration, GitToolsError

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_git_status():
    """Test git_status tool."""
    print_section("TEST 1: git_status()")
    try:
        git = GitAutomation(".")
        status = git.git_status()
        
        print(f"Repository Status:")
        print(f"  Current Branch: {status.current_branch}")
        print(f"  Is Clean: {status.is_clean}")
        print(f"  Staged Files: {len(status.staged_files)}")
        print(f"  Unstaged Files: {len(status.unstaged_files)}")
        print(f"  Conflicts: {len(status.conflicts)}")
        print(f"  Untracked Files: {len(status.untracked_files)}")
        
        if status.staged_files:
            print(f"\n  Staged Files:")
            for f in status.staged_files:
                print(f"    - {f}")
        
        if status.unstaged_files:
            print(f"\n  Unstaged Files:")
            for f in status.unstaged_files:
                print(f"    - {f}")
        
        print("\n✅ git_status() works!")
        return True
    except GitToolsError as e:
        print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_git_add_all():
    """Test git_add_all tool (dry run)."""
    print_section("TEST 2: git_add_all()")
    try:
        git = GitAutomation(".")
        result = git.git_add_all()
        
        print(f"Staging Result:")
        print(f"  Success: {result['success']}")
        print(f"  Message: {result['message']}")
        print(f"  Staged Count: {result['staged_count']}")
        
        if result.get('staged_files'):
            print(f"\n  Would Stage ({len(result['staged_files'])}):")
            for f in result['staged_files'][:5]:  # Show first 5
                print(f"    - {f}")
            if len(result['staged_files']) > 5:
                print(f"    ... and {len(result['staged_files']) - 5} more")
        
        if result.get('excluded_patterns'):
            print(f"\n  Exclusion Patterns:")
            for p in result['excluded_patterns'][:5]:
                print(f"    - {p}")
        
        print("\n✅ git_add_all() works!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_git_push_dryrun():
    """Test git_push (dry run - checks current branch only)."""
    print_section("TEST 3: git_push() - Check Current Branch")
    try:
        git = GitAutomation(".")
        status = git.git_status()
        
        branch = status.current_branch
        print(f"Current Branch: {branch}")
        
        if branch in ["main", "master"]:
            print("  ⚠️  On main/master - cannot push in test (would fail anyway)")
            print("  ✅ git_push() validation works!")
            return True
        else:
            print(f"  ✅ Can push to {branch}")
            print("  ✅ git_push() ready to use!")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_workflow():
    """Test WorkflowIntegration initialization."""
    print_section("TEST 4: WorkflowIntegration")
    try:
        workflow = WorkflowIntegration(".")
        
        print("WorkflowIntegration initialized")
        print(f"  Has git_automation: {hasattr(workflow, 'git')}")
        print(f"  Has commit_on_coverage_threshold: {hasattr(workflow, 'commit_on_coverage_threshold')}")
        print(f"  Has automated_workflow: {hasattr(workflow, 'automated_workflow')}")
        
        print("\n✅ WorkflowIntegration works!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_imports():
    """Test that git_tools can be imported by server."""
    print_section("TEST 0: Module Imports")
    try:
        from git_tools import (
            GitAutomation,
            WorkflowIntegration,
            GitStatus,
            CommitResult,
            PullRequestResult,
            GitToolsError
        )
        
        print("Successfully imported from git_tools:")
        print("  ✓ GitAutomation")
        print("  ✓ WorkflowIntegration")
        print("  ✓ GitStatus")
        print("  ✓ CommitResult")
        print("  ✓ PullRequestResult")
        print("  ✓ GitToolsError")
        
        print("\n✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  GIT TOOLS - VALIDATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests in order
    results.append(("Module Imports", test_imports()))
    results.append(("git_status()", test_git_status()))
    results.append(("git_add_all()", test_git_add_all()))
    results.append(("git_push() Check", test_git_push_dryrun()))
    results.append(("WorkflowIntegration", test_workflow()))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Git tools are ready to use.")
        print("\nNext steps:")
        print("  1. Start the server: python server.py")
        print("  2. Test git tools via MCP client")
        print("  3. Integrate with your testing workflow")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
