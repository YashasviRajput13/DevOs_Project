import asyncio

from app.services.github import GitHubService


async def main():

    github = GitHubService()

    repo = await github.get_repository(
        "YashasviRajput13",
        "DevOs_Project",
    )

    print("Repository:")
    print(repo["full_name"])

    branch = repo["default_branch"]

    print("Default branch:")
    print(branch)

    files = await github.get_repository_tree(
        "YashasviRajput13",
        "DevOs_Project",
        branch,
    )

    print("\nFiles found:", len(files))

    for file in files[:20]:
        print(file["path"])


asyncio.run(main())