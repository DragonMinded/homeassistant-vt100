from typing import Optional

from api import HomeAssistant
from vtpy import Terminal


class Action:
    pass


class ExitAction(Action):
    pass


class SettingAction(Action):
    def __init__(self, setting: str, value: Optional[str]) -> None:
        self.setting = setting
        self.value = value


class Renderer:
    def __init__(self, api: HomeAssistant, terminal: Terminal) -> None:
        self.api = api
        self.terminal = terminal
        self.entities = api.getEntities() or []
        self.lastWidth = 0
        self.lastHeight = 0

        # Move cursor to where we expect it for input.
        self.terminal.moveCursor(self.terminal.rows, 1)
        self.lastError = ""
        self.input = ""

    def refresh(self) -> None:
        self.api.refreshEntities(self.entities)

    def draw(self) -> None:
        redraw = False
        if (
            self.lastWidth != self.terminal.columns
            or self.lastHeight != self.terminal.rows
        ):
            self.lastWidth = self.terminal.columns
            self.lastHeight = self.terminal.rows
            redraw = True

        # If we need to redraw the whole screen.
        if redraw:
            # If we have input, we need to remember the cursor position.
            self.terminal.sendCommand(Terminal.SAVE_CURSOR)

            # Clear the entire screen.
            self.terminal.sendCommand(Terminal.CLEAR_SCREEN)

            # Now, draw any input that exists.
            self.terminal.moveCursor(self.terminal.rows, 1)
            self.terminal.sendCommand(Terminal.SET_NORMAL)
            self.terminal.sendCommand(Terminal.SET_REVERSE)
            self.terminal.sendText(self.input)
            if len(self.input) < self.terminal.columns:
                self.terminal.sendText(" " * (self.terminal.columns - len(self.input)))

            # Now, draw any error status.
            error = self.lastError
            self.lastError = ""
            self.displayError(error)

            # Now, render the rest of the page.
            self.terminal.sendCommand(Terminal.MOVE_CURSOR_ORIGIN)
            self.terminal.setAutoWrap()
            self.terminal.sendCommand(Terminal.SET_NORMAL)
            self.terminal.sendCommand(Terminal.SET_BOLD)
            self.terminal.sendText("Home Assistant Dashboard")
            self.terminal.sendCommand(Terminal.SET_NORMAL)
            self.terminal.clearAutoWrap()

            # Move cursor to input that we previously typed.
            self.terminal.sendCommand(Terminal.RESTORE_CURSOR)

    def clearInput(self) -> None:
        # Clear error display.
        self.clearError()

        self.terminal.moveCursor(self.terminal.rows, 1)
        self.terminal.sendCommand(Terminal.SAVE_CURSOR)
        self.terminal.sendCommand(Terminal.SET_NORMAL)
        self.terminal.sendCommand(Terminal.SET_REVERSE)
        self.terminal.sendText(" " * self.terminal.columns)
        self.terminal.sendCommand(Terminal.RESTORE_CURSOR)

        # Clear command.
        self.input = ""

    def clearError(self) -> None:
        self.displayError("")

    def displayError(self, error: str) -> None:
        if error == self.lastError:
            return

        self.terminal.sendCommand(Terminal.SAVE_CURSOR)
        self.terminal.moveCursor(self.terminal.rows - 1, 1)
        self.terminal.sendCommand(Terminal.CLEAR_LINE)
        self.terminal.sendCommand(Terminal.SET_NORMAL)
        self.terminal.sendCommand(Terminal.SET_BOLD)
        self.terminal.sendText(error)
        self.terminal.sendCommand(Terminal.SET_NORMAL)
        self.terminal.sendCommand(Terminal.RESTORE_CURSOR)
        self.lastError = error

    def processInput(self, inputVal: bytes) -> Optional[Action]:
        row, col = self.terminal.fetchCursor()
        if inputVal == Terminal.LEFT:
            if col > 1:
                col -= 1
                self.terminal.moveCursor(row, col)
        elif inputVal == Terminal.RIGHT:
            if col < (len(self.input) + 1):
                col += 1
                self.terminal.moveCursor(row, col)
        elif inputVal == Terminal.UP:
            # TODO: Move to previous element on screen.
            pass
        elif inputVal == Terminal.DOWN:
            # TODO: Move to next element on screen.
            pass
        elif inputVal in {Terminal.BACKSPACE, Terminal.DELETE}:
            if self.input:
                # Just subtract from input.
                if col == len(self.input) + 1:
                    # Erasing at the end of the line.
                    self.input = self.input[:-1]

                    col -= 1
                    self.terminal.moveCursor(row, col)
                    self.terminal.sendCommand(Terminal.SET_NORMAL)
                    self.terminal.sendCommand(Terminal.SET_REVERSE)
                    self.terminal.sendText(" ")
                    self.terminal.moveCursor(row, col)
                elif col == 1:
                    # Erasing at the beginning, do nothing.
                    pass
                elif col == 2:
                    # Erasing at the beginning of the line.
                    self.input = self.input[1:]

                    col -= 1
                    self.terminal.moveCursor(row, col)
                    self.terminal.sendCommand(Terminal.SET_NORMAL)
                    self.terminal.sendCommand(Terminal.SET_REVERSE)
                    self.terminal.sendText(self.input)
                    self.terminal.sendText(" ")
                    self.terminal.moveCursor(row, col)
                else:
                    # Erasing in the middle of the line.
                    spot = col - 2
                    self.input = self.input[:spot] + self.input[(spot + 1) :]

                    col -= 1
                    self.terminal.moveCursor(row, col)
                    self.terminal.sendCommand(Terminal.SET_NORMAL)
                    self.terminal.sendCommand(Terminal.SET_REVERSE)
                    self.terminal.sendText(self.input[spot:])
                    self.terminal.sendText(" ")
                    self.terminal.moveCursor(row, col)
        elif inputVal == b"\r":
            # Ignore this.
            pass
        elif inputVal == b"\n":
            # Execute command.
            actual = self.input.strip()
            if not actual:
                return None

            if actual == "exit":
                return ExitAction()
            elif actual == "set" or actual.startswith("set "):
                if " " not in actual:
                    self.displayError("No setting requested!")
                else:
                    _, setting = actual.split(" ", 1)
                    setting = setting.strip()

                    if "=" in setting:
                        setting, value = setting.split("=", 1)
                        setting = setting.strip()
                        value = value.strip()
                    else:
                        setting = setting.strip()
                        value = None

                    return SettingAction(setting, value)
            else:
                self.displayError(f"Unrecognized command {actual}")
        else:
            if len(self.input) < (self.terminal.columns - 1):
                # If we got some unprintable character, ignore it.
                inputVal = bytes(v for v in inputVal if v >= 0x20)
                if inputVal:
                    # Just add to input.
                    char = inputVal.decode("ascii")

                    if col == len(self.input) + 1:
                        # Just appending to the input.
                        self.input += char
                        self.terminal.sendCommand(Terminal.SET_NORMAL)
                        self.terminal.sendCommand(Terminal.SET_REVERSE)
                        self.terminal.sendText(char)
                        self.terminal.moveCursor(row, col + 1)
                    else:
                        # Adding to mid-input.
                        spot = col - 1
                        self.input = self.input[:spot] + char + self.input[spot:]

                        self.terminal.sendCommand(Terminal.SET_NORMAL)
                        self.terminal.sendCommand(Terminal.SET_REVERSE)
                        self.terminal.sendText(self.input[spot:])
                        self.terminal.moveCursor(row, col + 1)

        # Nothing happening here!
        return None
