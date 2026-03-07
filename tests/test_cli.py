from sealimg.cli import main


def test_main_help_exits_successfully() -> None:
    rc = main([])
    assert rc == 0


def test_version_exits_successfully() -> None:
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
