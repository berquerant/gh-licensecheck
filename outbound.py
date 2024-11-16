import json
import logging
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator, TextIO


def scriptd() -> Path:
    """Directory where this script resides."""
    return Path(__file__).parent


def setupLogging(debug: bool = False):
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s:%(lineno)d|%(message)s",
    )


def json_dumps(x) -> str:
    return json.dumps(x, separators=(",", ":"))


@contextmanager
def chdir(p: str):
    pwd = os.getcwd()
    try:
        os.chdir(p)  # pushd
        yield
    finally:
        os.chdir(pwd)  # popd


# gh repo license list
# https://choosealicense.com/appendix
GITHUB_LICENSE_KEY_TO_SPDX = {
    "agpl-3.0": "AGPL-3.0",
    "apache-2.0": "Apache-2.0",
    "bsd-2-clause": "BSD-2-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "bsl-1.0": "BSL-1.0",
    "cc0-1.0": "CC0-1.0",
    "epl-2.0": "EPL-2.0",
    "gpl-2.0": "GPL-2.0",
    "gpl-3.0": "GPL-3.0",
    "lgpl-2.1": "LGPL-2.1",
    "mit": "MIT",
    "mpl-2.0": "MPL-2.0",
    "unlicense": "Unlicense",
}

# flict list
SPDX_TO_FLICT = {
    "AGPL-3.0": "AGPL-3.0-only",
    "Apache-2.0": "Apache-2.0",
    "BSD-2-Clause": "BSD-2-Clause",
    "BSD-3-Clause": "BSD-3-Clause",
    "BSL-1.0": "BSL-1.0",
    "EPL-2.0": "EPL-2.0",
    "GPL-2.0": "GPL-2.0-only",
    "GPL-3.0": "GPL-3.0-only",
    "LGPL-2.1": "LGPL-2.1-only",
    "MIT": "MIT",
    "MPL-2.0": "MPL-2.0",
    "Unlicense": "Unlicense",
}


def github_license_key_to_flict(key: str) -> str | None:
    return SPDX_TO_FLICT.get(GITHUB_LICENSE_KEY_TO_SPDX.get(key, ""))


def run(*args) -> str:
    """Run command and return stdout."""
    logging.debug("run: %s", " ".join(args))
    r = subprocess.run(
        args, shell=False, check=True, text=True, capture_output=True
    ).stdout.rstrip()
    logging.debug("run: %s -> %s", " ".join(args), r)
    return r


@dataclass
class GitHubLicenseInfo:
    key: str
    name: str

    @staticmethod
    def from_obj(v) -> "GitHubLicenseInfo":
        return GitHubLicenseInfo(
            key=v.get("key", ""),
            name=v.get("name", ""),
        )

    def into_dict(self):
        return asdict(self)


@dataclass
class GitHubLicenseResult:
    repo: str
    url: str
    info: GitHubLicenseInfo

    @staticmethod
    def from_obj(v) -> "GitHubLicenseResult":
        return GitHubLicenseResult(
            repo=v.get("nameWithOwner", ""),
            url=v.get("url", ""),
            info=GitHubLicenseInfo.from_obj(v.get("licenseInfo", {})),
        )

    def into_dict(self):
        return {
            "nameWithOwner": self.repo,
            "url": self.url,
            "licenseInfo": self.info.into_dict(),
        }


class GitHub:
    def get_license_info(self, repo: str) -> GitHubLicenseResult:
        return GitHubLicenseResult.from_obj(
            json.loads(
                run(
                    "gh",
                    "repo",
                    "view",
                    repo,
                    "--json",
                    "nameWithOwner,url,licenseInfo",
                )
            )
        )


class CachedGitHub:
    def __init__(
        self,
        client: GitHub,
        cache_file: Path,
        ignore_cache: bool = False,
        interval_sec: int = 3,
    ):
        self.__client = client
        self.__data = self.load(cache_file)
        self.__ignore_cache = ignore_cache
        self.__interval_sec = interval_sec
        self.__filename = cache_file

    def get_lincense_info(self, repos: TextIO) -> Iterator[GitHubLicenseResult]:
        for i, repo in enumerate(repos):
            repo = repo.rstrip()
            logging.debug("Get github license info: repo=%s", repo)
            if not self.__ignore_cache and repo in self.__data:
                logging.debug("Get github license info: repo=%s cache hit", repo)
                yield self.__data[repo]
                continue
            if i != 0:
                time.sleep(self.__interval_sec)
            try:
                r = self.__client.get_license_info(repo)
                self.__data[r.repo] = r  # write to cache
                yield r
            except Exception as e:
                logging.error("Get github license info: repo=%s err=%s", repo, str(e))
                yield GitHubLicenseResult(
                    repo=repo,
                    url="",
                    info=GitHubLicenseInfo(key="UNKNOWN", name="UNKNOWN"),
                )

    def flush(self):
        logging.debug("Flush cached github license info")
        with self.__filename.open(mode="w") as f:
            for v in self.__data.values():
                # make cache persistent
                print(json_dumps(v.into_dict()), file=f)

    @staticmethod
    def load(cache_file: Path) -> dict[str, GitHubLicenseResult]:
        data: dict[str, GitHubLicenseResult] = {}
        cache_file.touch()
        with cache_file.open() as f:
            for i, line in enumerate(f):
                line = line.rstrip()
                linum = i + 1
                logging.debug(
                    "Load github license cache: linum=%d line=%s", linum, line
                )
                try:
                    r = GitHubLicenseResult.from_obj(json.loads(line))
                    data[r.repo] = r
                except Exception as e:
                    logging.warning(
                        "Load github license cache: linum=%d line=%s err=%s",
                        linum,
                        line,
                        str(e),
                    )
        return data


class Flict:
    def get_outbound(self, licenses: list[str]) -> list[str]:
        if len(licenses) == 0:
            logging.warning("Cannot calculate outbound due to no input for flict")
            return []
        args = " and ".join(licenses).split()
        with chdir(str(scriptd())):
            return json.loads(run(*["./flict", "outbound-candidate", *args]))


@contextmanager
def cached_github(filename: Path, ignore_cache: bool = False) -> Iterator[CachedGitHub]:
    resource = CachedGitHub(GitHub(), filename, ignore_cache=ignore_cache)
    try:
        yield resource
    finally:
        resource.flush()


def main(w: TextIO, r: TextIO, cache_filename: Path, ignore_cache: bool, debug: bool):
    setupLogging(debug)

    licenses: list[str] = []
    with cached_github(cache_filename, ignore_cache) as gh:
        for info in gh.get_lincense_info(r):
            result = github_license_key_to_flict(info.info.key)
            logging.info(
                "license: repo=%s github=%s flict=%s", info.repo, info.info.key, result
            )
            if result is None:
                logging.error(
                    "license unknown: repo=%s license=%s", info.repo, info.info.key
                )
                continue
            licenses.append(result)

    flict = Flict()
    for x in flict.get_outbound(licenses):
        print(x, file=w)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        usage="""Read dependency repos from stdin, suggest outbound licenses."""
    )
    parser.add_argument(
        "--ignore-cache", action="store_true", help="without reading cache from --cache"
    )
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument(
        "--cache",
        default=str(scriptd() / ".gh-licensecheck_github_cache"),
        action="store",
        type=str,
        help="cache file",
    )
    args = parser.parse_args()

    main(sys.stdout, sys.stdin, Path(args.cache), args.ignore_cache, args.debug)
