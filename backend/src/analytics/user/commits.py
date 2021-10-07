from typing import Any, Dict, List, Tuple, Union

from src.models.user.analytics import LanguageStats, RepoStats
from src.models.user.package import UserPackage

dict_type = Dict[str, Union[str, int, float]]


def get_top_languages(
    data: UserPackage, include_private: bool
) -> Tuple[List[LanguageStats], int]:
    raw_languages = (
        data.contribs.total_stats.languages
        if include_private
        else data.contribs.public_stats.languages
    )

    languages_list: List[dict_type] = [
        {
            "lang": lang,
            "color": stats.color,
            "additions": stats.additions,
            "deletions": stats.deletions,
        }
        for lang, stats in raw_languages.items()
    ]

    total_additions = sum([int(lang["additions"]) for lang in languages_list])
    total_deletions = sum([int(lang["deletions"]) for lang in languages_list])
    total_changed = total_additions + total_deletions + 1  # avoids division by zero
    total: dict_type = {
        "lang": "Total",
        "additions": total_additions,
        "deletions": total_deletions,
    }

    languages_list = sorted(
        languages_list,
        key=lambda x: int(x["additions"]) + int(x["deletions"]),
        reverse=True,
    )
    other: dict_type = {
        "lang": "Other",
        "additions": 0,
        "deletions": 0,
        "color": "#ededed",
    }
    for language in languages_list[4:]:
        other["additions"] = int(other["additions"]) + int(language["additions"])
        other["deletions"] = int(other["deletions"]) + int(language["deletions"])

    languages_list = [total] + languages_list[:4] + [other]

    new_languages_list: List[LanguageStats] = []
    for lang in languages_list:
        lang["added"] = int(lang["additions"]) - int(lang["deletions"])
        lang["changed"] = int(lang["additions"]) + int(lang["deletions"])
        lang["percent"] = float(round(100 * lang["changed"] / total_changed, 2))
        if lang["percent"] > 0:
            new_languages_list.append(LanguageStats.parse_obj(lang))

    commits_excluded = data.contribs.public_stats.other_count
    if include_private:
        commits_excluded = data.contribs.total_stats.other_count

    return new_languages_list, commits_excluded


def get_top_repos(
    data: UserPackage, include_private: bool
) -> Tuple[List[RepoStats], int]:
    repos: List[Any] = [
        {
            "repo": repo,
            "private": repo_stats.private,
            "langs": [
                {
                    "lang": x[0],
                    "color": x[1].color,
                    "additions": x[1].additions,
                    "deletions": x[1].deletions,
                }
                for x in list(repo_stats.languages.items())
            ],
            "additions": sum([x.additions for x in repo_stats.languages.values()]),
            "deletions": sum([x.deletions for x in repo_stats.languages.values()]),
        }
        for repo, repo_stats in data.contribs.repo_stats.items()
        if include_private or not repo_stats.private
    ]

    for repo in repos:
        repo["added"] = int(repo["additions"]) - int(repo["deletions"])
        repo["changed"] = int(repo["additions"]) + int(repo["deletions"])
        repo["langs"] = [
            x
            for x in repo["langs"]
            if x["additions"] + x["deletions"] > 0.05 * repo["changed"]
        ]

    repos = sorted(repos, key=lambda x: x["changed"], reverse=True)

    new_repos = [
        RepoStats.parse_obj(x)
        for x in repos
        if x["changed"] > 0.01 * repos[0]["changed"]
    ]

    commits_excluded = data.contribs.public_stats.other_count
    if include_private:
        commits_excluded = data.contribs.total_stats.other_count

    return new_repos[:5], commits_excluded
