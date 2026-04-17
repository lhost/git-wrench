"""
Curses-based interactive TUI for git-wrench.

Layout
──────
┌───────────────────────────────────────────┐
│  git-wrench  v0.1.0                        │  ← header bar
├───────────────────────────────────────────┤
│  [Repos]  [Sync]  [Config]  [Quit]        │  ← tab bar
├───────────────────────────────────────────┤
│                                           │
│   (active panel content)                  │  ← main area
│                                           │
├───────────────────────────────────────────┤
│  <arrows> navigate  <Enter> action  <q> quit  │  ← status bar
└───────────────────────────────────────────┘

Navigation
──────────
  Tab / Shift-Tab   : switch tabs
  ↑ / ↓            : move through list
  Enter            : run action (sync selected repo, open config dialog …)
  a / A            : sync ALL repos
  r / R            : refresh repo list
  q / Q / Esc      : quit (or close dialog)
"""

from __future__ import annotations

import curses
import importlib.metadata
from pathlib import Path

from . import config as cfg
from . import git_ops
from .git_ops import RepoInfo, RepoStatus
from .workspace import Workspace, WorkspaceManager

try:
    _VERSION = importlib.metadata.version("git-wrench")
except importlib.metadata.PackageNotFoundError:
    _VERSION = "dev"

# ── colour pair indices ───────────────────────────────────────────────────────
_P_NORMAL = 0  # default
_P_HEADER = 1
_P_TAB_SEL = 2
_P_TAB_NORM = 3
_P_OK = 4
_P_ERROR = 5
_P_WARN = 6
_P_DIM = 7
_P_CURSOR = 8
_P_TITLE = 9
_P_DIALOG = 10
_P_STATUSB = 11


def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    bg = -1  # transparent background
    curses.init_pair(_P_HEADER, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(_P_TAB_SEL, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(_P_TAB_NORM, curses.COLOR_CYAN, bg)
    curses.init_pair(_P_OK, curses.COLOR_GREEN, bg)
    curses.init_pair(_P_ERROR, curses.COLOR_RED, bg)
    curses.init_pair(_P_WARN, curses.COLOR_YELLOW, bg)
    curses.init_pair(_P_DIM, curses.COLOR_WHITE, bg)
    curses.init_pair(_P_CURSOR, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(_P_TITLE, curses.COLOR_CYAN, bg)
    curses.init_pair(_P_DIALOG, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(_P_STATUSB, curses.COLOR_BLACK, curses.COLOR_WHITE)


# ── small rendering helpers ───────────────────────────────────────────────────


def _attr(pair: int, bold: bool = False, dim: bool = False) -> int:
    a = curses.color_pair(pair)
    if bold:
        a |= curses.A_BOLD
    if dim:
        a |= curses.A_DIM
    return a


def _addstr_clipped(win: curses.window, y: int, x: int, text: str, attr: int, max_w: int) -> None:
    """Write *text* starting at (y, x), clipping to *max_w* chars."""
    if max_w <= 0:
        return
    win.addstr(y, x, text[:max_w], attr)


def _fill_line(win: curses.window, y: int, attr: int) -> None:
    """Paint the entire row *y* of *win* with *attr*."""
    _, w = win.getmaxyx()
    try:
        win.addstr(y, 0, " " * w, attr)
    except curses.error:
        pass


# ── modal dialog ─────────────────────────────────────────────────────────────


def _dialog(stdscr: curses.window, title: str, lines: list[str], buttons: list[str] | None = None) -> int:
    """Show a centred modal dialog, return the index of the chosen button."""
    if buttons is None:
        buttons = ["OK"]
    h, w = stdscr.getmaxyx()
    content_width = max((len(line) for line in lines), default=0)
    dialog_w = max(content_width + 4, max(len(b) for b in buttons) * 3 + 4, len(title) + 4, 40)
    dialog_h = len(lines) + 6  # title + separator + lines + separator + buttons + border
    dialog_y = max(0, (h - dialog_h) // 2)
    dialog_x = max(0, (w - dialog_w) // 2)

    win = curses.newwin(dialog_h, dialog_w, dialog_y, dialog_x)
    win.bkgd(" ", _attr(_P_DIALOG))

    selected = 0

    while True:
        win.clear()
        win.border()

        # title
        _addstr_clipped(win, 1, 2, title, _attr(_P_DIALOG, bold=True), dialog_w - 4)

        # separator
        win.hline(2, 1, curses.ACS_HLINE, dialog_w - 2)

        # content lines
        for i, line in enumerate(lines):
            _addstr_clipped(win, 3 + i, 2, line, _attr(_P_DIALOG), dialog_w - 4)

        # button row separator
        btn_row = dialog_h - 3
        win.hline(btn_row, 1, curses.ACS_HLINE, dialog_w - 2)

        # buttons
        btn_y = dialog_h - 2
        btn_x = 2
        for i, btn in enumerate(buttons):
            label = f" {btn} "
            attr = _attr(_P_TAB_SEL, bold=True) if i == selected else _attr(_P_DIALOG)
            _addstr_clipped(win, btn_y, btn_x, label, attr, dialog_w - btn_x - 2)
            btn_x += len(label) + 2

        win.refresh()

        key = win.getch()
        if key in (curses.KEY_LEFT, ord("h")):
            selected = (selected - 1) % len(buttons)
        elif key in (curses.KEY_RIGHT, ord("l")):
            selected = (selected + 1) % len(buttons)
        elif key in (curses.KEY_ENTER, 10, 13):
            del win
            return selected
        elif key in (27, ord("q")):  # Esc or q  → cancel (last button index)
            del win
            return len(buttons) - 1


# ── input dialog (single text field) ─────────────────────────────────────────


def _input_dialog(stdscr: curses.window, title: str, prompt: str, default: str = "") -> str | None:
    """Return the entered string, or None if cancelled."""
    h, w = stdscr.getmaxyx()
    dialog_w = max(len(prompt) + 4, 50, len(title) + 4)
    dialog_h = 7
    dialog_y = max(0, (h - dialog_h) // 2)
    dialog_x = max(0, (w - dialog_w) // 2)

    win = curses.newwin(dialog_h, dialog_w, dialog_y, dialog_x)
    win.bkgd(" ", _attr(_P_DIALOG))
    curses.echo()
    curses.curs_set(1)

    value = list(default)

    try:
        while True:
            win.clear()
            win.border()
            _addstr_clipped(win, 1, 2, title, _attr(_P_DIALOG, bold=True), dialog_w - 4)
            win.hline(2, 1, curses.ACS_HLINE, dialog_w - 2)
            _addstr_clipped(win, 3, 2, prompt, _attr(_P_DIALOG), dialog_w - 4)

            field_x = 2
            field_w = dialog_w - 4
            field_str = "".join(value)
            _addstr_clipped(
                win,
                4,
                field_x,
                field_str + " " * (field_w - len(field_str)),
                _attr(_P_CURSOR),
                field_w,
            )
            win.move(4, field_x + min(len(value), field_w - 1))

            _addstr_clipped(win, 5, 2, "Enter=confirm  Esc=cancel", _attr(_P_DIM), dialog_w - 4)
            win.refresh()

            key = win.getch()
            if key in (curses.KEY_ENTER, 10, 13):
                return "".join(value).strip() or None
            elif key == 27:  # Esc
                return None
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if value:
                    value.pop()
            elif 32 <= key < 256:
                if len(value) < field_w - 1:
                    value.append(chr(key))
    finally:
        curses.noecho()
        curses.curs_set(0)


# ── Repos tab ─────────────────────────────────────────────────────────────────


class ReposPanel:
    """Displays discovered repos and allows per-repo or bulk sync."""

    def __init__(self, conf: dict) -> None:
        self.conf = conf
        self.repos: list[RepoInfo] = []
        self.cursor = 0
        self.offset = 0  # scroll offset
        self.loading = False
        self._load_repos()

    def _load_repos(self) -> None:
        self.loading = True
        roots = cfg.workspace_paths(self.conf)
        depth = int(self.conf.get("sync", {}).get("recurse_depth", 2))
        self.repos = git_ops.find_repos(roots, max_depth=depth)
        for r in self.repos:
            git_ops.refresh_status(r)
        self.loading = False
        self.cursor = min(self.cursor, max(0, len(self.repos) - 1))

    def draw(self, win: curses.window, active: bool) -> None:
        h, w = win.getmaxyx()
        win.erase()

        if self.loading:
            _addstr_clipped(win, h // 2, 2, "Loading repositories…", _attr(_P_WARN), w - 4)
            return

        if not self.repos:
            _addstr_clipped(win, 2, 2, "No repositories found.", _attr(_P_DIM), w - 4)
            _addstr_clipped(win, 3, 2, "Check your workspace paths in Config.", _attr(_P_DIM), w - 4)
            return

        # column header
        hdr = f"  {'Repository':<46} {'Branch':<16} {'↑':>3} {'↓':>3}  Status"
        _addstr_clipped(win, 0, 0, hdr, _attr(_P_TITLE, bold=True), w)

        visible = h - 2  # leave last row for scroll hint

        # adjust scroll
        if self.cursor < self.offset:
            self.offset = self.cursor
        if self.cursor >= self.offset + visible:
            self.offset = self.cursor - visible + 1

        for i, repo in enumerate(self.repos[self.offset : self.offset + visible]):
            real_idx = self.offset + i
            row = i + 1
            is_cur = active and (real_idx == self.cursor)

            status_icon, status_attr = _status_icon(repo.status)
            dirty_flag = "*" if repo.dirty else " "

            path_str = _short_path(repo.path, w - 50)
            branch_str = repo.branch[:16] if repo.branch else "?"
            ahead_s = str(repo.ahead) if repo.ahead else "-"
            behind_s = str(repo.behind) if repo.behind else "-"

            line = f"  {path_str:<46} {branch_str:<16} {ahead_s:>3} {behind_s:>3} {dirty_flag} {status_icon} {repo.message[:30]}"

            base_attr = _attr(_P_CURSOR) if is_cur else curses.A_NORMAL
            _fill_line(win, row, base_attr)
            _addstr_clipped(win, row, 0, line, base_attr, w - 1)

            # colour the status icon separately
            icon_col = 46 + 16 + 3 + 3 + 4 + 2
            if not is_cur:
                try:
                    win.addstr(row, icon_col, status_icon, status_attr)
                except curses.error:
                    pass

        # scroll indicator
        if len(self.repos) > visible:
            pct = int(self.offset / max(1, len(self.repos) - visible) * 100)
            hint = f" {self.offset + 1}-{min(self.offset + visible, len(self.repos))}/{len(self.repos)} ({pct}%)"
            _addstr_clipped(win, h - 1, w - len(hint) - 1, hint, _attr(_P_DIM), len(hint) + 1)

    def handle_key(self, key: int, stdscr: curses.window) -> str | None:
        """Return an action string or None."""
        if key == curses.KEY_UP:
            self.cursor = max(0, self.cursor - 1)
        elif key == curses.KEY_DOWN:
            self.cursor = min(len(self.repos) - 1, self.cursor + 1) if self.repos else 0
        elif key in (curses.KEY_ENTER, 10, 13):
            if self.repos:
                return "sync_one"
        elif key in (ord("a"), ord("A")):
            return "sync_all"
        elif key in (ord("r"), ord("R")):
            return "refresh"
        return None

    def sync_one(self, stdscr: curses.window) -> None:
        if not self.repos:
            return
        repo = self.repos[self.cursor]
        _dialog(stdscr, "Syncing…", [str(repo.path), "", "Pulling latest changes…"])
        sync_cfg = self.conf.get("sync", {})
        git_ops.sync_repo(
            repo,
            fetch_prune=bool(sync_cfg.get("fetch_prune", True)),
            stash=bool(sync_cfg.get("stash_before_pull", False)),
        )
        result_lines = [str(repo.path), "", repo.message[:60] or "Done."]
        _dialog(stdscr, "Sync result", result_lines)

    def sync_all(self, stdscr: curses.window) -> None:
        if not self.repos:
            return
        h, w = stdscr.getmaxyx()
        sync_cfg = self.conf.get("sync", {})

        for i, repo in enumerate(self.repos):
            # show a simple progress overlay
            prog_win = curses.newwin(5, min(60, w - 4), h // 2 - 2, max(0, (w - 60) // 2))
            prog_win.bkgd(" ", _attr(_P_DIALOG))
            prog_win.border()
            _addstr_clipped(
                prog_win,
                1,
                2,
                f"Syncing {i + 1}/{len(self.repos)}",
                _attr(_P_DIALOG, bold=True),
                56,
            )
            _addstr_clipped(prog_win, 2, 2, _short_path(repo.path, 54), _attr(_P_DIALOG), 56)
            _addstr_clipped(prog_win, 3, 2, "Press any key to abort…", _attr(_P_DIM), 56)
            prog_win.nodelay(True)
            prog_win.refresh()

            git_ops.sync_repo(
                repo,
                fetch_prune=bool(sync_cfg.get("fetch_prune", True)),
                stash=bool(sync_cfg.get("stash_before_pull", False)),
            )

            # check for abort key
            k = prog_win.getch()
            del prog_win
            if k != -1:
                break

        stdscr.touchwin()
        stdscr.refresh()


def _status_icon(s: RepoStatus) -> tuple[str, int]:
    return {
        RepoStatus.PENDING: ("…", _attr(_P_DIM)),
        RepoStatus.OK: ("✓", _attr(_P_OK, bold=True)),
        RepoStatus.CHANGED: ("~", _attr(_P_WARN, bold=True)),
        RepoStatus.CONFLICT: ("!", _attr(_P_ERROR, bold=True)),
        RepoStatus.ERROR: ("✗", _attr(_P_ERROR, bold=True)),
    }.get(s, (" ", curses.A_NORMAL))


def _short_path(p: Path, max_len: int = 46) -> str:
    s = str(p)
    home = str(Path.home())
    if s.startswith(home):
        s = "~" + s[len(home) :]
    if len(s) > max_len:
        s = "…" + s[-(max_len - 1) :]
    return s


# ── Workspaces tab ────────────────────────────────────────────────────────────


class WorkspacesPanel:
    """List, add, edit and delete workspaces via WorkspaceManager."""

    def __init__(self, mgr: WorkspaceManager) -> None:
        self.mgr = mgr
        self.cursor = 0
        self._offset = 0

    def _items(self) -> list[Workspace]:
        return self.mgr.all()

    def draw(self, win: curses.window, active: bool) -> None:
        h, w = win.getmaxyx()
        entries = self._items()
        win.erase()

        hdr = f"  {'Name':<24} {'Path'}"
        _addstr_clipped(win, 0, 0, hdr, _attr(_P_TITLE, bold=True), w)

        if not entries:
            _addstr_clipped(win, 2, 2, "No workspaces defined.", _attr(_P_DIM), w - 4)
            _addstr_clipped(win, 3, 2, "Press  n  to add one.", _attr(_P_DIM), w - 4)
            return

        visible = h - 3
        if self.cursor < self._offset:
            self._offset = self.cursor
        if self.cursor >= self._offset + visible:
            self._offset = self.cursor - visible + 1

        for i, ws in enumerate(entries[self._offset : self._offset + visible]):
            real_idx = self._offset + i
            row = i + 2
            is_cur = active and real_idx == self.cursor
            base_attr = _attr(_P_CURSOR) if is_cur else curses.A_NORMAL
            _fill_line(win, row, base_attr)
            _addstr_clipped(win, row, 0, f"  {ws.name:<24} {ws.path}", base_attr, w - 1)

        hint = "  n new   Enter/e edit   d delete"
        _addstr_clipped(win, h - 1, 0, hint, _attr(_P_DIM), w - 1)

    def handle_key(self, key: int, stdscr: curses.window) -> bool:
        """Return True if config was modified."""
        entries = self._items()
        if key == curses.KEY_UP:
            self.cursor = max(0, self.cursor - 1)
        elif key == curses.KEY_DOWN:
            self.cursor = min(len(entries) - 1, self.cursor + 1) if entries else 0
        elif key in (ord("n"), ord("N")):
            return self._add(stdscr)
        elif key in (curses.KEY_ENTER, 10, 13, ord("e"), ord("E")):
            if entries:
                return self._edit(stdscr, entries[self.cursor])
        elif key in (ord("d"), ord("D")):
            if entries:
                return self._delete(stdscr, entries[self.cursor])
        return False

    def _add(self, stdscr: curses.window) -> bool:
        name = _input_dialog(stdscr, "Add workspace", "Name:", default="")
        if not name:
            return False
        path = _input_dialog(stdscr, "Add workspace", "Path:", default=str(Path.home()))
        if not path:
            return False
        try:
            self.mgr.add(name, path)
        except ValueError as e:
            _dialog(stdscr, "Error", [str(e)])
            return False
        self.cursor = len(self._items()) - 1
        self.mgr.save()
        return True

    def _edit(self, stdscr: curses.window, ws: Workspace) -> bool:
        name = _input_dialog(stdscr, "Edit workspace", "Name:", default=ws.name)
        if name is None:
            return False
        path = _input_dialog(stdscr, "Edit workspace", "Path:", default=ws.path)
        if path is None:
            return False
        try:
            if name and name != ws.name:
                self.mgr.rename(ws.name, name)
            if path and path != ws.path:
                self.mgr.update_path(name or ws.name, path)
        except ValueError as e:
            _dialog(stdscr, "Error", [str(e)])
            return False
        self.mgr.save()
        return True

    def _delete(self, stdscr: curses.window, ws: Workspace) -> bool:
        choice = _dialog(
            stdscr,
            "Delete workspace",
            [f"Delete  '{ws.name}' ?", "", ws.path],
            ["Delete", "Cancel"],
        )
        if choice != 0:
            return False
        self.mgr.remove(ws.name)
        self.cursor = min(self.cursor, max(0, len(self._items()) - 1))
        self.mgr.save()
        return True


# ── Config tab ────────────────────────────────────────────────────────────────


class ConfigPanel:
    """Display and edit sync configuration values."""

    def __init__(self, conf: dict) -> None:
        self.conf = conf
        self._build_items()
        self.cursor = 0

    def _build_items(self) -> None:
        sync = self.conf.get("sync", {})
        self.items: list[tuple[str, str, str]] = [
            ("Recurse depth", str(sync.get("recurse_depth", 2)), "recurse_depth"),
            ("Fetch prune", str(sync.get("fetch_prune", True)), "fetch_prune"),
            ("Stash before pull", str(sync.get("stash_before_pull", False)), "stash_before_pull"),
        ]

    def draw(self, win: curses.window, active: bool) -> None:
        h, w = win.getmaxyx()
        win.erase()

        hdr = f"  {'Setting':<30} {'Value'}"
        _addstr_clipped(win, 0, 0, hdr, _attr(_P_TITLE, bold=True), w)

        for i, (label, value, _key) in enumerate(self.items):
            row = i + 2
            is_cur = active and i == self.cursor
            base_attr = _attr(_P_CURSOR) if is_cur else curses.A_NORMAL
            _fill_line(win, row, base_attr)
            line = f"  {label:<30} {value}"
            _addstr_clipped(win, row, 0, line, base_attr, w - 1)

        path_note = f"  Config file: {cfg.config_path()}"
        _addstr_clipped(win, h - 2, 0, path_note, _attr(_P_DIM), w - 1)

    def handle_key(self, key: int, stdscr: curses.window) -> bool:
        """Return True if config was modified."""
        if key == curses.KEY_UP:
            self.cursor = max(0, self.cursor - 1)
        elif key == curses.KEY_DOWN:
            self.cursor = min(len(self.items) - 1, self.cursor + 1)
        elif key in (curses.KEY_ENTER, 10, 13):
            return self._edit_item(stdscr)
        return False

    def _edit_item(self, stdscr: curses.window) -> bool:
        label, value, key = self.items[self.cursor]
        sync = self.conf.setdefault("sync", {})

        if key == "recurse_depth":
            new_val = _input_dialog(stdscr, "Edit recurse depth", "Max directory depth (1-5):", default=value)
            if new_val is not None:
                try:
                    sync["recurse_depth"] = max(1, min(5, int(new_val)))
                    cfg.save(self.conf)
                    self._build_items()
                    return True
                except ValueError:
                    pass
        elif key in ("fetch_prune", "stash_before_pull"):
            current = sync.get(key, key == "fetch_prune")
            sync[key] = not current
            cfg.save(self.conf)
            self._build_items()
            return True

        return False


# ── Help panel ────────────────────────────────────────────────────────────────

_HELP_LINES = [
    ("git-wrench", _P_TITLE),
    ("", _P_NORMAL),
    ("Keyboard shortcuts", _P_DIM),
    ("─" * 40, _P_DIM),
    ("  Tab / Shift-Tab      Switch panel tabs", _P_NORMAL),
    ("  ↑ / ↓               Move cursor in list", _P_NORMAL),
    ("", _P_NORMAL),
    ("Workspaces tab", _P_DIM),
    ("─" * 40, _P_DIM),
    ("  n                   Add new workspace", _P_NORMAL),
    ("  Enter / e           Edit selected workspace", _P_NORMAL),
    ("  d                   Delete selected workspace", _P_NORMAL),
    ("", _P_NORMAL),
    ("Repos tab", _P_DIM),
    ("─" * 40, _P_DIM),
    ("  Enter               Sync selected repo", _P_NORMAL),
    ("  a / A               Sync ALL repositories", _P_NORMAL),
    ("  r / R               Refresh repository list", _P_NORMAL),
    ("", _P_NORMAL),
    ("  q / Q / Esc         Quit", _P_NORMAL),
    ("", _P_NORMAL),
    ("CLI commands", _P_DIM),
    ("─" * 40, _P_DIM),
    ("  git-wrench sync             Pull all repos", _P_NORMAL),
    ("  git-wrench sync --path DIR  Pull repos under DIR", _P_NORMAL),
    ("  git-wrench status           Show repo overview", _P_NORMAL),
]


class HelpPanel:
    def draw(self, win: curses.window, active: bool) -> None:
        win.erase()
        for i, (line, pair) in enumerate(_HELP_LINES):
            _addstr_clipped(win, i + 1, 2, line, _attr(pair), win.getmaxyx()[1] - 4)

    def handle_key(self, key: int, _stdscr: curses.window) -> None:
        pass


# ── Main TUI loop ─────────────────────────────────────────────────────────────

_TABS = ["Workspaces", "Repos", "Config", "Help"]


def run_tui(conf: dict) -> None:
    """Entry point – run the curses application."""
    curses.wrapper(_tui_main, conf)


def _tui_main(stdscr: curses.window, conf: dict) -> None:
    _init_colors()
    curses.curs_set(0)
    curses.set_escdelay(25)
    stdscr.keypad(True)

    mgr = WorkspaceManager.load()

    workspaces_panel = WorkspacesPanel(mgr)
    repos_panel = ReposPanel(conf)
    config_panel = ConfigPanel(conf)
    help_panel = HelpPanel()
    panels = [workspaces_panel, repos_panel, config_panel, help_panel]

    active_tab = 0

    while True:
        h, w = stdscr.getmaxyx()

        # ── combined menu / title bar (row 0) ────────────────────────────────
        _fill_line(stdscr, 0, _attr(_P_TAB_NORM))
        x = 1
        for i, tab in enumerate(_TABS):
            label = f" {tab} "
            attr = _attr(_P_TAB_SEL, bold=True) if i == active_tab else _attr(_P_TAB_NORM)
            _addstr_clipped(stdscr, 0, x, label, attr, w - x - 1)
            x += len(label) + 1

        # right-aligned app name
        brand = f"git-wrench v{_VERSION}  "
        brand_x = max(x + 1, w - len(brand))
        _addstr_clipped(stdscr, 0, brand_x, brand, _attr(_P_TAB_NORM, bold=True), w - brand_x)

        # ── main area ─────────────────────────────────────────────────────────
        panel_h = max(0, h - 2)  # menu bar + status bar
        panel_w = max(0, w)
        panel_y = 1
        panel_x = 0

        # create a sub-window for the panel
        panel_win = curses.newwin(panel_h, panel_w, panel_y, panel_x)
        panels[active_tab].draw(panel_win, active=True)
        panel_win.refresh()

        # ── status bar ────────────────────────────────────────────────────────
        _fill_line(stdscr, h - 1, _attr(_P_STATUSB))
        if active_tab == 0:
            hints = "  ↑↓ navigate   n new   Enter/e edit   d delete   Tab switch   q quit"
        elif active_tab == 1:
            hints = "  ↑↓ navigate   Enter sync   a sync-all   r refresh   Tab switch   q quit"
        elif active_tab == 2:
            hints = "  ↑↓ navigate   Enter edit   Tab switch   q quit"
        else:
            hints = "  Tab switch   q quit"
        _addstr_clipped(stdscr, h - 1, 0, hints, _attr(_P_STATUSB), w)

        stdscr.refresh()

        # ── input ─────────────────────────────────────────────────────────────
        key = stdscr.getch()

        # global keys
        if key in (ord("q"), ord("Q"), 27):
            break
        elif key == ord("\t"):  # Tab
            active_tab = (active_tab + 1) % len(_TABS)
            continue
        elif key == curses.KEY_BTAB:  # Shift-Tab
            active_tab = (active_tab - 1) % len(_TABS)
            continue

        # per-panel keys
        panel = panels[active_tab]
        if active_tab == 0:
            # Workspaces — WorkspaceManager saves itself; reload repos from updated paths
            modified = panel.handle_key(key, stdscr)
            if modified:
                mgr.reload()
                repos_panel.conf = mgr._conf
                repos_panel._load_repos()
        elif active_tab == 1:
            # Repos
            action = panel.handle_key(key, stdscr)
            if action == "sync_one":
                panel.sync_one(stdscr)
                stdscr.touchwin()
            elif action == "sync_all":
                choice = _dialog(
                    stdscr,
                    "Sync all repositories",
                    [
                        f"Sync {len(panel.repos)} repos?",
                        "",
                        "This will fetch & pull all discovered repos.",
                    ],
                    ["Sync", "Cancel"],
                )
                if choice == 0:
                    panel.sync_all(stdscr)
                stdscr.touchwin()
            elif action == "refresh":
                panel._load_repos()
        elif active_tab == 2:
            # Config
            modified = panel.handle_key(key, stdscr)
            if modified:
                conf = cfg.load()
                config_panel.conf = conf
                config_panel._build_items()
        elif active_tab == 3:
            panel.handle_key(key, stdscr)
