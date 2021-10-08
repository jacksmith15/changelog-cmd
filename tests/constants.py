from typing import Dict

DEFAULT_HEADER: str = """# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to
[Semantic Versioning].

### Types of changes

| Name       | Description                       | Version bump |
| ---------- | --------------------------------- | ------------ |
| Added      | New features                      | minor        |
| Changed    | Changes in existing functionality | minor        |
| Deprecated | Soon-to-be removed features       | minor        |
| Removed    | Removes features                  | major        |
| Fixed      | For bug fixes                     | patch        |
| Security   | In case of vulnerabilities        | patch        |
"""

DEFAULT_LINKS: Dict[str, str] = {
    "Keep a Changelog": "http://keepachangelog.com/en/1.0.0/",
    "Semantic Versioning": "http://semver.org/spec/v2.0.0.html",
}
