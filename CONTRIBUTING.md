# Contributing to VOIDemon

First off, thank you for considering contributing to VOIDemon! It's people like you that make VOIDemon such a great tool.

## Where do I go from here?

If you've noticed a bug or have a feature request, make one! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting to code.

## Fork & create a branch

If this is something you think you can fix, then fork VOIDemon and create a branch with a descriptive name.

A good branch name would be (where issue #325 is the ticket you're working on):

```sh
git checkout -b 325-add-grpc-support
```

## Get the test suite running

Make sure you have Docker installed and the Python dependencies (`requirements.txt`).
Always ensure your new code passes the underlying LQC and Gossip propagation tests.
Test by booting a local 5-node cluster via `docker-compose`.

## Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first.

## Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with VOIDemon's master branch:

```sh
git remote add upstream https://github.com/LokeshMehar/VOIDemon.git
git checkout master
git pull upstream master
```

Then update your feature branch from your local copy of master, and push it!

```sh
git checkout 325-add-grpc-support
git rebase master
git push --set-upstream origin 325-add-grpc-support
```

Finally, go to GitHub and make a Pull Request.

## Keeping your Pull Request updated

If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.
