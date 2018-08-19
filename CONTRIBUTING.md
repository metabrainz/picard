# Contributing to Picard

## Coding Style

As most of the other projects written in Python, we use the [PEP 8](https://www.python.org/dev/peps/pep-0008/). Though, we ignore some of the recommendations:

* E501 - Maximum line length (79 characters). The general limit we have is somewhere around 120-130.

*Recommended video: "[Beyond PEP 8 -- Best practices for beautiful intelligible code](https://www.youtube.com/watch?v=wf-BqAjZb8M)" by Raymond Hettinger at PyCon 2015, which talks about the famous P versus NP problem.*

The general idea is to make the code within a project consistent and easy to interpret (for humans).

To fix or preserve imports style, one can use `isort -rc .` command (requires `isort` tool, see `.isort.cfg`).

### Docstrings

Unless the function is easy to understand quickly, it should probably have a docstring describing what it does, how it does it, what the arguments are, and what the expected output is.

We recommend using ["Google-style" docstrings](https://google.github.io/styleguide/pyguide.html?showone=Comments#Comments) for writing docstrings.

### Picard specific code

Picard has some auto-generated `picard/ui/ui_*.py` PyQt UI related files. Please do not change them directly. To modify them, use Qt-Designer to edit the `ui/*.ui` and use the command `python setup.py build_ui` to generate the corresponding `ui_*.py` files.

We use snake-case to name all functions and variables except for the pre-generated PyQt functions/variables.

`gettext` and `gettext-noop` have been built-in the Picard code as `_` and `N_` respectively to provide support for internationalization/localization. You can use them without imports across all of Picard code. Make sure to mark all displayable strings for translation using `_` or `N_` as applicable. You can read more about python-gettext [here](https://docs.python.org/2/library/gettext.html).

## Git Work-flow

We follow the "typical" GitHub workflow when contributing changes:

1. [Fork](https://help.github.com/articles/fork-a-repo/) a repository into your account.
2. Create a new branch and give it a meaningful name. For example, if you are going to fix issue PICARD-257, branch can be called `picard-257` or `preserve-artwork`.
3. Make your changes and commit them with a [good description](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html). Your commit subject should be written in **imperative voice** and **sentence case**. With regards to the contents of the message itself, you don't need to provide a lot of details, but make sure that people who look at the commit history afterwards can understand what you were changing and why.
4. [Create](https://help.github.com/articles/creating-a-pull-request/) a new pull request on GitHub. Make sure that the title of your pull request is descriptive and consistent with the rest. If you are fixing issue that exists in our bug tracker reference it like this: `PICARD-257: Allow preserving existing cover-art tags`. **Not** `[PICARD-257] - Allow preserving existing cover-art tags` or `Allow preserving existing cover-art tags (PICARD-257)` or simply `PICARD-257`.
5. Make sure to provide a bug tracker link to the issue that your pull request solves in the description.
6. Do not make one big pull request with a lot of unrelated changes. If you are solving more than one issue, unless they are closely related, split them into multiple pull requests. It makes it easier to review and merge the patches this way.
7. Try to avoid un-necessary commits after code reviews by making use of [git rebase](https://help.github.com/articles/about-git-rebase/) to fix merge conflicts, remove unwanted commits, rewording and editing previous commits or squashing multiple small related changes into one commit.
