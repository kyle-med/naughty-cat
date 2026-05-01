from PySide6.QtCore import QCoreApplication
from naughty_cat.cat_manager import CatManager


def test_cat_manager_initial_state(qtbot):
    manager = CatManager()
    assert manager.cat_count == 0


def test_spawn_cats_creates_windows(qtbot):
    manager = CatManager()
    manager.spawn_cats(count=2, size=100, active_cat_gifs=[
        "波仔.gif", "咣当.gif", "Bender.gif"
    ])
    assert manager.cat_count == 2


def test_dismiss_all_hides_windows(qtbot):
    manager = CatManager()
    manager.spawn_cats(count=2, size=100, active_cat_gifs=[
        "波仔.gif", "咣当.gif"
    ])
    dismiss_requested = False

    def on_dismiss():
        nonlocal dismiss_requested
        dismiss_requested = True

    manager.dismiss_requested.connect(on_dismiss)
    manager.dismiss_all()

    def check():
        return dismiss_requested is True

    qtbot.waitUntil(check, timeout=3000)
    assert dismiss_requested is True


def test_remove_all_destroys_windows(qtbot):
    manager = CatManager()
    manager.spawn_cats(count=2, size=100, active_cat_gifs=[
        "波仔.gif", "咣当.gif"
    ])
    manager.remove_all()
    assert manager.cat_count == 0


def test_double_spawn_replaces_cats(qtbot):
    manager = CatManager()
    manager.spawn_cats(count=1, size=100, active_cat_gifs=["波仔.gif"])
    first_cats = manager._windows.copy()
    manager.spawn_cats(count=3, size=100, active_cat_gifs=["波仔.gif", "咣当.gif", "Bender.gif"])
    assert manager.cat_count == 3
    # Old windows should be destroyed
    for w in first_cats:
        assert not w.isVisible()
