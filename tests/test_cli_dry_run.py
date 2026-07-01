import pytest
from click.testing import CliRunner
from unittest.mock import patch
from tjbench.cli import cli


@patch("tjbench.cli.run_proof")
def test_run_dry_run(mock_run_proof):
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--benchmark", "samples", "--original", "mock:original", "--mock", "--dry-run"])
    assert result.exit_code == 0
    assert "Dry-Run Execution Plan" in result.output
    assert "Benchmark" in result.output
    assert "samples" in result.output
    assert "Original" in result.output
    assert "mock:original" in result.output
    assert "Mode" in result.output
    assert "OFFLINE" in result.output
    mock_run_proof.assert_not_called()


@patch("tjbench.cli.run_agent_proof")
def test_agent_dry_run(mock_run_agent_proof):
    runner = CliRunner()
    result = runner.invoke(cli, ["agent", "--benchmark", "sample-agent", "--original", "mock:original", "--mock", "--dry-run"])
    assert result.exit_code == 0
    assert "Dry-Run Execution Plan" in result.output
    assert "Benchmark" in result.output
    assert "sample-agent" in result.output
    assert "Original" in result.output
    assert "mock:original" in result.output
    assert "Mode" in result.output
    assert "OFFLINE" in result.output
    mock_run_agent_proof.assert_not_called()
