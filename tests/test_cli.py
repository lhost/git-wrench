from git_wrench.cli import main


def test_main_execution(capsys):
    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "git-wrench is ready for work!" in captured.out