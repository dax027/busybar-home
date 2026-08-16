from busybar_home.cli import main


def test_cli_uses_fake_client_by_default(monkeypatch, capsys) -> None:
    monkeypatch.delenv("BUSYBAR_CLIENT", raising=False)
    monkeypatch.delenv("BUSYBAR_ALLOW_HARDWARE", raising=False)

    exit_code = main(["FOCUS"])

    assert exit_code == 0
    assert "Client: fake" in capsys.readouterr().out


def test_cli_refuses_unapproved_hardware(monkeypatch, capsys) -> None:
    monkeypatch.setenv("BUSYBAR_CLIENT", "official")
    monkeypatch.setenv("BUSYBAR_ALLOW_HARDWARE", "false")

    exit_code = main([])

    assert exit_code == 2
    assert "Configuration error" in capsys.readouterr().out
