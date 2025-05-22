"""Simple entrypoint as MCP server.

.. important::

   This source include trial codes.
   Clean up until publish on GitHub.
"""

import argparse
import sys
import logging
import tomllib
from pathlib import Path

import httpx
from pydantic import BaseModel
from packaging.requirements import Requirement

from . import mcp


class SearchResult(BaseModel):
    url: str
    title: str
    highlight: str


parser = argparse.ArgumentParser()
parser.add_argument("--workspace", type=str, default=str(Path.cwd()))

args = parser.parse_args()

# Load pyproject.
pyproject_toml = (Path(args.workspace) or Path.cwd()) / "pyproject.toml"
if not pyproject_toml.exists():
    sys.stderr.write("This server requires 'pyproject.toml'!")
    sys.exit(1)
pyproject_data = tomllib.loads(pyproject_toml.read_text(encoding="utf8"))
if "project" not in pyproject_data or "dependencies" not in pyproject_data["project"]:
    sys.stderr.write(
        "This server requires 'project.dependencies' property in 'pyproject.toml'!"
    )
    sys.exit(1)
projects = [Requirement(dep).name for dep in pyproject_data["project"]["dependencies"]]
logging.info("Found %s projects", len(projects))


@mcp.resource("data://supported-projects", name="List of supported projects")
def get_supported_project() -> list[str]:
    """Provides list of project name that are supported for search documents."""
    return projects


@mcp.tool()
def search_document(project_name: str, word: str) -> list[SearchResult]:
    """Search pages of document from specified project.

    :param project_name: Search target project. This must be one of data://supported-projects.
    :param word: Search keyword.
    :returns: List of search result that includes page title, URL and hilights.
    """
    params = {
        "q": f'project:{project_name} "{word}"',
        "page_size": 5,
    }
    resp = httpx.get("https://readthedocs.org/api/v3/search/", params=params)
    data = resp.json()
    return [
        SearchResult(url=f"{r['domain']}{r['path']}", title=r["title"], highlight="")
        for r in data["results"]
    ]


mcp.run()
