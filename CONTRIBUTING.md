# Using GitHub

## The workflow

We follow the "typical" GitHub workflow when contributing changes:

1. [Fork](https://help.github.com/articles/fork-a-repo/) a repository into your account.
2. Create a new branch and give it a meaningful name. For example, if you are going to fix issue PICARD-257, branch can be called `picard-257` or `preserve-artwork`.
3. Make your changes and commit them with a [good description](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html). Your commit subject should be written in **imperative voice** and **sentence case**. With regards to the contents of the message itself, you don't need to provide a lot of details, but make sure that people who look at the commit history afterwards can understand what you were changing and why.*
4. [Create](https://help.github.com/articles/creating-a-pull-request/) a new pull request on GitHub. Make sure that the title of your pull request is descriptive and consistent with the rest. If you are fixing issue that exists in our bug tracker reference it like this: `PICARD-257: Allow preserving existing cover-art tags`. **Not** `[PICARD-257] - Allow preserving existing cover-art tags` or `Allow preserving existing cover-art tags (PICARD-257)` or simply `PICARD-257`.
5. Make sure to provide a bug tracker link to the issue that your pull request solves in the description.
6. Do not make one big pull request with a lot of unrelated changes. If you are solving more than one issue, unless they are closely related, split them into multiple pull requests. It makes it easier to review and merge the patches this way.
7. Try to avoid un-necessary commits after code reviews by making use of [git rebase](https://help.github.com/articles/about-git-rebase/) to fix merge conflicts, remove unwanted commits, rewording and editing previous commits or squashing multiple small related changes into one commit.
