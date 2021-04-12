from invoke import Collection, task

from tasks.changelog_check import changelog_check
from tasks.lint import lint
from tasks.release import release
from tasks.test import coverage, test
from tasks.typecheck import typecheck

namespace = Collection()

namespace.add_task(changelog_check)
namespace.add_task(coverage)
namespace.add_task(lint)
namespace.add_task(release)
namespace.add_task(test)
namespace.add_task(typecheck)


@namespace.add_task
@task(post=[changelog_check, lint, typecheck, test])
def verify(_ctx):
    """Run all verification steps."""
