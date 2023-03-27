import os
import random
import re
import shutil
import string
import subprocess
import sys
from abc import abstractmethod, ABC
from os import PathLike
from pathlib import Path
from subprocess import Popen
from typing import List, Optional, Tuple

from fuzzingbook.Grammars import Grammar, srange, is_valid_grammar
from isla.derivation_tree import DerivationTree
from isla.fuzzer import GrammarFuzzer

from tests4py.framework.constants import Environment
from tests4py.grammars.utils import GrammarVisitor
from tests4py.projects import Project, Status, TestingFramework, TestStatus
from tests4py.tests.generator import UnittestGenerator, SystemtestGenerator
from tests4py.tests.utils import API, TestResult


class CookieCutter(Project):
    def __init__(
        self,
        bug_id: int,
        python_version: str,
        python_path: str,
        buggy_commit_id: str,
        fixed_commit_id: str,
        test_file: List[Path],
        test_cases: List[str],
        darwin_python_version: Optional[str] = None,
        test_status_fixed: TestStatus = TestStatus.PASSING,
        test_status_buggy: TestStatus = TestStatus.FAILING,
        unittests: Optional[UnittestGenerator] = None,
        systemtests: Optional[SystemtestGenerator] = None,
        api: Optional[API] = None,
    ):
        super().__init__(
            bug_id=bug_id,
            project_name="cookiecutter",
            github_url="https://github.com/cookiecutter/cookiecutter",
            status=Status.OK,
            cause="N.A.",
            python_version=python_version,
            python_path=python_path,
            buggy_commit_id=buggy_commit_id,
            fixed_commit_id=fixed_commit_id,
            testing_framework=TestingFramework.PYTEST,
            test_file=test_file,
            test_cases=test_cases,
            darwin_python_version=darwin_python_version,
            test_status_fixed=test_status_fixed,
            test_status_buggy=test_status_buggy,
            unittests=unittests,
            systemtests=systemtests,
            api=api,
            grammar=grammar,
        )  # TODO adjust parameters


def register():
    CookieCutter(
        bug_id=1,
        python_version="3.6.9",
        darwin_python_version="3.6.15",  # version 3.6.9 do not work on mac os
        python_path="cookiecutter/build/lib/",
        buggy_commit_id="c15633745df6abdb24e02746b82aadb20b8cdf8c",
        fixed_commit_id="7f6804c4953a18386809f11faf4d86898570debc",
        test_file=[
            Path("tests", "test_generate_context.py"),
            Path("tests", "test-generate-context", "non_ascii.json"),
        ],
        test_cases=[
            "tests/test_generate_context.py::test_generate_context_decodes_non_ascii_chars"
        ],
        test_status_buggy=TestStatus.PASSING,  # It was just a missing test file
    )
    CookieCutter(
        bug_id=2,
        python_version="3.6.9",
        darwin_python_version="3.6.15",  # version 3.8.1-3 do not work on mac os
        python_path="cookiecutter/build/lib/",
        buggy_commit_id="d7e7b28811e474e14d1bed747115e47dcdd15ba3",
        fixed_commit_id="90434ff4ea4477941444f1e83313beb414838535",
        test_file=[Path("tests", "test_hooks.py")],
        test_cases=[
            "tests/test_hooks.py::TestFindHooks::test_find_hook",
            "tests/test_hooks.py::TestExternalHooks::test_run_hook",
        ],
        api=CookieCutter2API(),
        systemtests=CookieCutter2SystemtestGenerator(),
    )
    CookieCutter(
        bug_id=3,
        python_version="3.6.9",
        darwin_python_version="3.6.15",  # version 3.8.1-3 do not work on mac os
        python_path="cookiecutter/build/lib/",
        buggy_commit_id="5c282f020a8db7e5e7c4e7b51b010556ca31fb7f",
        fixed_commit_id="7129d474206761a6156925db78eee4b62a0e3944",
        test_file=[Path("tests", "test_read_user_choice.py")],
        test_cases=["tests/test_read_user_choice.py::test_click_invocation"],
        api=CookieCutter3API(),
        systemtests=CookieCutter3SystemtestGenerator(),
    )
    CookieCutter(
        bug_id=4,
        python_version="3.6.9",
        darwin_python_version="3.6.15",  # version 3.8.1-3 do not work on mac os
        python_path="cookiecutter/build/lib/",
        buggy_commit_id="9568ab6ecd2d6836646006c59473c4a4ac0dee04",
        fixed_commit_id="457a1a4e862aab4102b644ff1d2b2e2b5a766b3c",
        test_file=[Path("tests", "test_hooks.py")],
        test_cases=["tests/test_hooks.py::TestExternalHooks::test_run_failing_hook"],
        api=CookieCutter4API(),
        systemtests=CookieCutter4SystemtestGenerator(),
    )
    # TODO implement the 4 bugs of cookiecutter


class CookieCutterAPI(API, GrammarVisitor):
    REPO_PATH = "tests4py_repo"

    def __init__(self, default_timeout: int = 5):
        API.__init__(self, default_timeout=default_timeout)
        GrammarVisitor.__init__(self, grammar=grammar)
        self.config = None
        self.pre_hooks = []
        self.post_hooks = []
        self.path = []
        self.pre_hook_crash = False
        self.post_hook_crash = False

    def visit_hooks(self, node: DerivationTree):
        self.pre_hooks = []
        self.post_hooks = []
        self.pre_hook_crash = False
        self.post_hook_crash = False
        for children in node.children:
            self.visit(children)

    def visit_config(self, node: DerivationTree):
        self.config = node.to_string()
        for child in node.children:
            self.visit(child)

    def visit_repo_name(self, node: DerivationTree):
        self.path = list(
            map(lambda x: x.replace('"', ""), node.children[1].to_string().split(","))
        )

    def _set_hook_crash(self, hook: str, pre: bool = True):
        c, v = hook.split(",")
        if c == "exit" and v != "0":
            if pre:
                self.pre_hook_crash = True
            else:
                self.post_hook_crash = True

    def visit_pre_hook(self, node: DerivationTree):
        hook = node.children[1].to_string()
        self._set_hook_crash(hook)
        self.pre_hooks.append(hook)

    def visit_post_hook(self, node: DerivationTree):
        hook = node.children[1].to_string()
        self._set_hook_crash(hook, pre=False)
        self.post_hooks.append(hook)

    @staticmethod
    def _write_hook(hooks_path, hooks, file):
        for i, hook in enumerate(hooks):
            c, v = hook.split(",")
            with open(os.path.join(hooks_path, f"{file}.{i}"), "w") as fp:
                if sys.platform.startswith("win"):
                    if c == "exit":
                        fp.write(f"exit \\b {v}\n")
                    else:
                        fp.write("@echo off\n")
                        fp.write(f"echo {v}\n")
                else:
                    fp.write("#!/bin/sh\n")
                    if c == "exit":
                        fp.write(f"exit {v}\n")
                    else:
                        fp.write(f'echo "{v}"\n')

    def _setup(self):
        if os.path.exists(self.REPO_PATH):
            if os.path.isdir(self.REPO_PATH):
                shutil.rmtree(self.REPO_PATH, ignore_errors=True)
            else:
                os.remove(self.REPO_PATH)

        os.makedirs(self.REPO_PATH)

        with open(os.path.join(self.REPO_PATH, "cookiecutter.json"), "w") as fp:
            fp.write(self.config)

        repo_path = os.path.join(self.REPO_PATH, "{{cookiecutter.repo_name}}")
        os.makedirs(repo_path)

        with open(os.path.join(repo_path, "README.rst"), "w") as fp:
            fp.write(
                "============\nFake Project\n============\n\n"
                "Project name: **{{ cookiecutter.project_name }}**\n\n"
                "Blah!!!!\n"
            )

        if self.pre_hooks or self.post_hooks:
            hooks_path = os.path.join(self.REPO_PATH, "hooks")
            os.makedirs(hooks_path)
            if self.pre_hooks:
                self._write_hook(hooks_path, self.pre_hooks, "pre_gen_project")
            if self.post_hooks:
                self._write_hook(hooks_path, self.post_hooks, "post_gen_project")

    @abstractmethod
    def _validate(self, process: subprocess.Popen, stdout, stderr) -> TestResult:
        pass

    @abstractmethod
    def _get_command_parameters(self) -> List[str]:
        return []

    def _communicate(self, process: Popen) -> Tuple[bytes, bytes] | Tuple[str, str]:
        return process.communicate(20 * b"\n", self.default_timeout)

    # noinspection PyBroadException
    def run(self, system_test_path: PathLike, environ: Environment) -> TestResult:
        try:
            with open(system_test_path, "r") as fp:
                content = fp.read()
            self.visit_source(content)
            self._setup()
            if self.path:
                for p in self.path:
                    shutil.rmtree(p, ignore_errors=True)
            process = subprocess.Popen(
                ["cookiecutter"] + self._get_command_parameters() + [self.REPO_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environ,
            )
            stdout, stderr = self._communicate(process)
            return self._validate(process, stdout, stderr)
        except subprocess.TimeoutExpired:
            return TestResult.UNDEFINED
        except Exception:
            return TestResult.UNDEFINED
        finally:
            if self.path:
                for p in self.path:
                    shutil.rmtree(p, ignore_errors=True)
            shutil.rmtree(self.REPO_PATH, ignore_errors=True)


class CookieCutter2API(CookieCutterAPI):
    def _get_command_parameters(self) -> List[str]:
        return ["--no-input", "-v"]

    def _validate(
        self, process: subprocess.Popen, stdout: bytes | str, stderr: bytes | str
    ) -> TestResult:
        if process.returncode != 0:
            return TestResult.UNDEFINED
        if isinstance(stdout, str):
            output = stdout
        else:
            output = stdout.decode("utf-8")
        for hook in self.pre_hooks + self.post_hooks:
            command, hook = hook.split(",")
            if command == "echo":
                hook_repr = "\n" + hook + "\n"
                if hook_repr in output:
                    output = output.replace(hook_repr, "\n", 1)
                else:
                    return TestResult.FAILING
            else:
                return TestResult.UNDEFINED
        return TestResult.PASSING


class CookieCutter3API(CookieCutterAPI):
    def __init__(self, default_timeout: int = 5):
        super().__init__(default_timeout=default_timeout)
        self.choice_pattern = re.compile(r"Choose from \d+(, \d)+ \(\d+(, \d)+\)")

    def _get_command_parameters(self) -> List[str]:
        return []

    def _validate(
        self, process: subprocess.Popen, stdout: bytes | str, stderr: bytes | str
    ) -> TestResult:
        if process.returncode != 0:
            return TestResult.UNDEFINED
        if isinstance(stdout, str):
            output = stdout
        else:
            output = stdout.decode("utf-8")
        if self.choice_pattern.search(output):
            return TestResult.FAILING
        return TestResult.PASSING


class CookieCutter4API(CookieCutterAPI):
    def __init__(self, default_timeout: int = 5):
        super().__init__(default_timeout=default_timeout)

    def _get_command_parameters(self) -> List[str]:
        return ["-v"]

    def _validate(
        self, process: subprocess.Popen, stdout: bytes | str, stderr: bytes | str
    ) -> TestResult:
        if isinstance(stderr, str):
            output = stderr
        else:
            output = stderr.decode("utf-8")
        captured = True
        if self.pre_hook_crash:
            if (
                "Stopping generation because pre_gen_project hook script didn't exit sucessfully"
                in output
            ):
                return TestResult.PASSING
            else:
                return TestResult.FAILING
        if self.post_hook_crash:
            if (
                "cookiecutter.exceptions.FailedHookException: Hook script failed"
                in output
            ):
                return TestResult.PASSING
            if self.post_hook_crash:
                return TestResult.FAILING
        return TestResult.PASSING


class CookieCutterSystemtestGenerator(SystemtestGenerator, ABC):
    def __init__(self):
        SystemtestGenerator.__init__(self)
        self.pre_hook_fuzzer = GrammarFuzzer(grammar, start_symbol="<pre_hook>")
        self.post_hook_fuzzer = GrammarFuzzer(grammar, start_symbol="<post_hook>")
        self.str_fuzzer = GrammarFuzzer(grammar, start_symbol="<str>")
        self.str_with_spaces_fuzzer = GrammarFuzzer(
            grammar, start_symbol="<str_with_spaces>"
        )
        self.email_fuzzer = GrammarFuzzer(grammar, start_symbol="<email_address>")
        self.date_fuzzer = GrammarFuzzer(grammar, start_symbol="<date>")
        self.int_fuzzer = GrammarFuzzer(grammar, start_symbol="<int>")
        self.version_fuzzer = GrammarFuzzer(grammar, start_symbol="<v>")

    def _generate_default_config(
        self,
        full_name=None,
        email=None,
        github_username=None,
        project_name=None,
        repo_name=None,
        project_short_description=None,
        release_date=None,
        year=None,
        version=None,
    ) -> str:
        full_name = (
            f'"{self.str_with_spaces_fuzzer.fuzz()}"'
            if full_name is None
            else full_name
        )
        email = f'"{self.email_fuzzer.fuzz()}"' if email is None else email
        github_username = (
            f'"{self.str_fuzzer.fuzz()}"'
            if github_username is None
            else github_username
        )
        project_name = (
            f'"{self.str_with_spaces_fuzzer.fuzz()}"'
            if project_name is None
            else project_name
        )
        repo_name = f'"{self.str_fuzzer.fuzz()}"' if repo_name is None else repo_name
        project_short_description = (
            f'"{self.str_with_spaces_fuzzer.fuzz()}"'
            if project_short_description is None
            else project_short_description
        )
        release_date = (
            f'"{self.date_fuzzer.fuzz()}"' if release_date is None else release_date
        )
        year = f'"{self.int_fuzzer.fuzz()}"' if year is None else year
        version = f'"{self.version_fuzzer.fuzz()}"' if version is None else version
        return (
            f'{{"full_name":{full_name},'
            f'"email":{email},'
            f'"github_username":{github_username},'
            f'"project_name":{project_name},'
            f'"repo_name":{repo_name},'
            f'"project_short_description":{project_short_description},'
            f'"release_date":{release_date},'
            f'"year":{year},'
            f'"version":{version}}}'
        )

    def _generate_config_with_choices(self, selection=None, n=4) -> str:
        choices = [
            "full_name",
            "email",
            "github_username",
            "project_name",
            "repo_name",
            "project_short_description",
            "release_date",
            "year",
            "version",
        ]
        if selection is None:
            n = max(1, min(n, len(choices)))
            selection = random.sample(
                choices,
                random.randint(1, n),
            )
        parameters = dict()
        for s in selection:
            if s in ["full_name", "project_name", "project_short_description"]:
                fuzzer = self.str_with_spaces_fuzzer
            elif s == "email":
                fuzzer = self.email_fuzzer
            elif s == "release_date":
                fuzzer = self.date_fuzzer
            elif s == "year":
                fuzzer = self.int_fuzzer
            elif s == "version":
                fuzzer = self.version_fuzzer
            else:
                fuzzer = self.str_fuzzer
            value = ",".join(f'"{fuzzer.fuzz()}"' for _ in range(random.randint(2, 5)))
            parameters[s] = f"[{value}]"
        return self._generate_default_config(**parameters)

    def _generate_hook(
        self, pre=True, echo=True, exit_=False, exit_codes: str | list = "0"
    ) -> str:
        hook_contents = []
        if exit_:
            hook_contents.append(lambda: f"exit,{random.choice(exit_codes)}")
        if echo:
            hook_contents.append(lambda: f"echo,{self.str_with_spaces_fuzzer.fuzz()}")
        if hook_contents:
            hook_content = random.choice(hook_contents)()
        else:
            hook_content = f"echo,{self.str_with_spaces_fuzzer.fuzz()}"
        if pre:
            return f"pre:{hook_content}"
        else:
            return f"post:{hook_content}"

    def _generate_hooks(
        self,
        pre=True,
        pre_min=0,
        pre_max=1,
        post_min=0,
        post_max=1,
        echo=True,
        exit_=False,
        exit_codes: str | list = "0",
    ) -> List[str]:
        hooks = [
            self._generate_hook(pre=pre, echo=echo, exit_=exit_, exit_codes=exit_codes)
            for _ in range(0, random.randint(pre_min, pre_max))
        ] + [
            self._generate_hook(
                pre=not pre, echo=echo, exit_=exit_, exit_codes=exit_codes
            )
            for _ in range(0, random.randint(post_min, post_max))
        ]
        if hooks:
            random.shuffle(hooks)
            return hooks
        else:
            return [""]


class CookieCutter2SystemtestGenerator(CookieCutterSystemtestGenerator):
    def generate_failing_test(self) -> Tuple[str, TestResult]:
        pre = random.choice([True, False])
        hooks = self._generate_hooks(pre=pre, pre_min=2, pre_max=5, post_max=5)
        return "\n".join([self._generate_default_config()] + hooks), TestResult.FAILING

    def generate_passing_test(self) -> Tuple[str, TestResult]:
        hooks = self._generate_hooks()
        return "\n".join([self._generate_default_config()] + hooks), TestResult.PASSING


class CookieCutter3SystemtestGenerator(CookieCutterSystemtestGenerator):
    def generate_failing_test(self) -> Tuple[str, TestResult]:
        hooks = self._generate_hooks(pre_max=2, post_max=2, exit_=True)
        return (
            "\n".join(
                [self._generate_config_with_choices(n=random.randint(1, 5))] + hooks
            ),
            TestResult.FAILING,
        )

    def generate_passing_test(self) -> Tuple[str, TestResult]:
        hooks = self._generate_hooks(pre_max=2, post_max=2, exit_=True)
        return "\n".join([self._generate_default_config()] + hooks), TestResult.PASSING


class CookieCutter4SystemtestGenerator(CookieCutterSystemtestGenerator):
    def generate_failing_test(self) -> Tuple[str, TestResult]:
        hooks = self._generate_hooks(
            pre_max=0,
            post_min=1,
            echo=False,
            exit_=True,
            exit_codes=list(range(1, 256)),
        )
        hooks += self._generate_hooks(post_max=0, exit_=True)
        if "" in hooks:
            hooks.remove("")
        random.shuffle(hooks)
        return (
            "\n".join(
                [self._generate_config_with_choices(n=random.randint(1, 5))] + hooks
            ),
            TestResult.FAILING,
        )

    def generate_passing_test(self) -> Tuple[str, TestResult]:
        hooks = self._generate_hooks(post_max=0, exit_=True, exit_codes="001")
        hooks += self._generate_hooks(pre_max=0, post_max=1, exit_=True)
        if "" in hooks:
            hooks.remove("")
        random.shuffle(hooks)
        return "\n".join([self._generate_default_config()] + hooks), TestResult.PASSING


grammar: Grammar = {
    "<start>": ["<config>\n<hooks>"],
    "<config>": ["{<pairs>}", "{}"],
    "<hooks>": ["", "<hook_list>"],
    "<hook_list>": ["<hook>", "<hook_list>\n<hook>"],
    "<hook>": ["<pre_hook>", "<post_hook>"],
    "<pre_hook>": ["pre:<hook_content>"],
    "<post_hook>": ["post:<hook_content>"],
    "<hook_content>": ["echo,<str_with_spaces>", "exit,<int>"],
    "<pairs>": ["<pair>", "<pairs>,<pair>"],
    "<pair>": [
        "<full_name>",
        "<email>",
        "<github_username>",
        "<project_name>",
        "<repo_name>",
        "<project_short_description>",
        "<release_date>",
        "<year>",
        "<version>",
    ],
    "<full_name>": [
        '"full_name":"<str_with_spaces>"',
        '"full_name":[<str_with_spaces_list>]',
    ],
    "<email>": ['"email":"<email_address>"', '"email":[<email_list>]'],
    "<github_username>": [
        '"github_username":"<str>"',
        '"github_username":[<str_list>]',
    ],
    "<project_name>": [
        '"project_name":"<str_with_spaces>"',
        '"project_name":[<str_with_spaces_list>]',
    ],
    "<repo_name>": ['"repo_name":"<str>"', '"repo_name":[<str_list>]'],
    "<project_short_description>": [
        '"project_short_description":"<str_with_spaces>"',
        '"project_short_description":[<str_with_spaces_list>]',
    ],
    "<release_date>": ['"release_date":"<date>"', '"release_date":[<date_list>]'],
    "<year>": ['"year":"<int>"', '"year":[<int_list>]'],
    "<version>": ['"version":"<v>"', '"version":[<version_list>]'],
    "<str_with_spaces_list>": [
        '"<str_with_spaces>"',
        '<str_with_spaces_list>,"<str_with_spaces>"',
    ],
    "<email_list>": ['"<email_address>"', '<email_list>,"<email_address>"'],
    "<str_list>": ['"<str>"', '<str_list>,"<str>"'],
    "<int_list>": ['"<int>"', '<int_list>,"<int>"'],
    "<date_list>": ['"<date>"', '<date_list>,"<date>"'],
    "<version_list>": ['"<v>"', '<version_list>,"<v>"'],
    "<chars>": ["", "<chars><char>"],
    "<char>": srange(string.ascii_letters + string.digits + "_"),
    "<chars_with_spaces>": ["", "<chars_with_spaces><char_with_spaces>"],
    "<char_with_spaces>": srange(string.ascii_letters + string.digits + "_ "),
    "<str>": ["<char><chars>"],
    "<str_with_spaces>": ["<char_with_spaces><chars_with_spaces>"],
    "<email_address>": ["<str>@<str>.<str>"],
    "<date>": ["<day>.<month>.<int>", "<int>-<month>-<day>"],
    "<month>": ["0<nonzero>", "<nonzero>", "10", "11", "12"],
    "<day>": [
        "0<nonzero>",
        "<nonzero>",
        "10",
        "1<nonzero>",
        "20",
        "2<nonzero>",
        "30",
        "31",
    ],
    "<v>": ["<digit><digits>", "<v>.<digit><digits>"],
    "<int>": ["<nonzero><digits>", "0"],
    "<digits>": ["", "<digits><digit>"],
    "<nonzero>": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
    "<digit>": srange(string.digits),
}

assert is_valid_grammar(grammar)