# Contributing to Lexonomy

We would be delighted if you contribute to Lexonomy and make it even
better than it is today!

- [Question or Problem?](#question)
- [Issues and Bugs](#issue)
- [Feature Requests](#feature)
- [Submission Guidelines](#submit)
- [Coding Rules](#rules)
- [Commit Message Guidelines](#commit)
- [Releasing Lexonomy](#releasing-lexonomy)
- [Signing the CLA](#cla)
- [Code of Conduct](#coc)


## <a name="question"></a> Got a Question or a Problem?

Do not open issues for support questions, as we want to keep GitHub
issues for bug reports and feature requests. You have a much better chance of
getting an answer to your question on the [elexis-lexonomy Google
Group][elexis-lexonomy-group].


## <a name="issue"></a> Found a Bug?
If you find a bug, you can help us by [submitting an issue](#submit-issue) to
our [GitHub Repository][github].

## <a name="feature"></a> Missing a Feature?
You can *request* a new feature by [submitting an issue](#submit-issue) to our
[GitHub Repository][github].  If you would like to *implement* a new feature,
please submit an issue with a proposal for your work first.

## <a name="submit"></a> Submission Guidelines

### <a name="submit-issue"></a> Submitting an Issue

Before you submit an issue, please search the issue tracker, maybe an issue for
your problem already exists and the discussion might inform you of workarounds
readily available.

Before fixing a bug we need to understand and confirm it. In order to
understand bugs, we will ask you to provide all necessary information.

You can file new issues by selecting from our [new issue
templates](https://github.com/elexis-eu/lexonomy/issues/new/choose) and filling
out the issue template.


## <a name="rules"></a> Coding Rules

To ensure consistency throughout the source code, keep these rules in mind as
you are working:

* We follow the following style guides
  - [JavaScript standardjs.com Style][js-style-guide] for JavaScript
  - [PEP 8 - Style Guide for Python Code][py-style-guide] for Python
* Features or bug fixes **should be tested** by one or more specs.
* All public API methods **must be documented**.


## <a name="commit"></a> Commit Message Guidelines

We have a few ideas about how git commit messages should be formatted. We
think, this leads to **more readable messages** that are easy to follow when
looking through the **project history**.

### Commit Message Format
Each commit message consists of a **subject**, a **body** and a **footer**.

```
<subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

Any line of the commit message should not be longer 100 characters! This allows
the message to be easier to read on GitHub as well as in various git tools.

[Samples](https://github.com/elexis-eu/lexonomy/commits/master)


### Subject
The subject contains a succinct description of the change:

* do capitalize the first letter
* use the imperative, present tense: "change" not "changed" nor "changes"
* no dot (.) at the end

### Body
Just as in the **subject**, use the imperative, present tense: "change" not
"changed" nor "changes".  The body should include the motivation for the change
and contrast this with previous behavior.

### Footer
The footer should contain a [closing reference to an
issue](https://help.github.com/articles/closing-issues-via-commit-messages/) if
any.


## Releasing Lexonomy

Start with a clean checkout that has the full Git history and tags. See
[Release setup](#release-setup) if this is your first release.
Run `python scripts -h` to list the repository commands.

```sh
git switch develop
python scripts release --push
```

Choose patch, minor, or major. After the checks pass, edit the release notes,
then save and close the draft. The script commits `releases/<version>.md`, tags
the release, advances `main`, and pushes to `origin`. GitHub Actions builds the
tagged commit and publishes `x.y.z`, `x.y`, and `x` to Docker Hub.

### Release setup

- **Local.** Install Python 3.12, Node.js 22.12 or newer, and
  [uv](https://docs.astral.sh/uv/getting-started/installation/). Run
  `python scripts install-frontend` once and `python scripts check` to run the
  release checks independently. On Windows, start Docker with Linux containers
  for the API tests. On other platforms, install the ICU build prerequisites
  listed in [source setup](INSTALL.md#install-from-source).
- **GitHub.** Set the repository variable `DOCKERHUB_IMAGE` to `namespace/repository`.
  Add your username as `DOCKERHUB_USERNAME` and a token with write access as
  `DOCKERHUB_TOKEN`. Save both as GitHub secrets.

### Other release tasks

- **Prepare locally.** Run `python scripts release`. To publish later, run
  the push command it prints.
- **Maintain an older major.** A major release creates `maintenance/<major>` at
  the previous major's last stable tag. Run the release script on that branch
  for patch or minor releases.
- **Publish a release candidate.** Tag a commit that contains the Docker release
  workflow. GitHub Actions publishes only the exact image tag.

  ```sh
  git tag -a 2.0.0-rc.1 -m 'Release candidate 2.0.0-rc.1'
  git push origin refs/tags/2.0.0-rc.1
  ```

- **Build a Docker image locally.** With Docker Buildx and the Git tag available,
  run `python scripts build-docker 2.0.0-rc.1`. To publish from your machine,
  run `docker login`, set `DOCKERHUB_IMAGE`, and add `--push` to the build command.


## <a name="cla"></a> Signing the CLA

Please sign our Contributor License Agreement (CLA) before sending pull
requests. The CLA must have been signed for code changes to be accepted. 
It won't take long, we promise!

* [For individuals][individual-cla].
* [For corporations][corporate-cla].


## <a name="coc"></a> Code of Conduct

Help us keep Lexonomy open and inclusive. Please read and follow our [Code of Conduct][coc].


[elexis-lexonomy-group]: https://groups.google.com/forum/#!forum/elexis-lexonomy
[github]: https://github.com/elexis-eu/lexonomy/
[js-style-guide]: https://standardjs.com/rules.html
[py-style-guide]: https://www.python.org/dev/peps/pep-0008/
[individual-cla]: FIXME
[corporate-cla]: FIXME
[coc]: https://github.com/elexis-eu/lexonomy/blob/master/CODE_OF_CONDUCT.md
