from PySide6.QtWidgets import QApplication
from naughty_cat.ui.welcome_wizard import WelcomeWizard


def test_wizard_has_three_pages(qtbot):
    wizard = WelcomeWizard()
    qtbot.addWidget(wizard)
    assert wizard.pageIds()
    assert len(wizard.pageIds()) == 3


def test_wizard_sets_first_run_false(qtbot):
    wizard = WelcomeWizard()
    qtbot.addWidget(wizard)
    settings = wizard.get_settings()
    assert "first_run" in settings
    assert settings["first_run"] is False
