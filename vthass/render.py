from typing import Dict, List, Optional, Tuple

from vtpy import Terminal

from .api import HomeAssistant, Entity, SwitchEntity, SensorEntity
from .config import Page


class Action:
    pass


class ExitAction(Action):
    pass


class SettingAction(Action):
    def __init__(self, setting: str, value: Optional[str]) -> None:
        self.setting = setting
        self.value = value


class Object:
    def __init__(self, entity: Entity, overridden_name: Optional[str]) -> None:
        self.entity: Entity = entity
        self.__overridden_name: Optional[str] = overridden_name
        self.__dirty = True

    @property
    def name(self) -> str:
        return self.__overridden_name or self.entity.entity_id

    @property
    def full(self) -> bool:
        return False

    @property
    def dirty(self) -> bool:
        return self.__dirty

    @dirty.setter
    def dirty(self, newval: bool) -> None:
        self.__dirty = newval

    @property
    def selectable(self) -> bool:
        return False

    @property
    def selected(self) -> bool:
        return False

    @selected.setter
    def selected(self, newval: bool) -> None:
        pass

    def toggle(self) -> None:
        pass

    def render(self, terminal: Terminal, width: int) -> None:
        text = f"UNSUPPORTED ENTITY {self.entity.entity_id}"
        text = text[:width]

        terminal.sendText(text)

    def calculate(self, terminal: Terminal, width: int) -> int:
        return 1


class HelpObject(Object):
    def __init__(self) -> None:
        self.lines = [
            "The following commands are available to use at any time:",
            "",
            "    prev",
            "        Display the previous tab.",
            "",
            "    next",
            "        Display the next tab.",
            "",
            "    toggle [SWITCH]",
            "        Toggle a displayed switch by name.",
            "",
            "    help",
            "        Display this help screen.",
            "",
            "    exit",
            "        Exit out of the dashboard interface.",
        ]

    @property
    def name(self) -> str:
        return "help_virtual_object"

    @property
    def full(self) -> bool:
        return True

    def render(self, terminal: Terminal, width: int) -> None:
        row, col = terminal.fetchCursor()
        for line in self.lines:
            text = line[:width]

            terminal.moveCursor(row, col)
            terminal.sendText(text)
            row += 1

    def calculate(self, terminal: Terminal, width: int) -> int:
        return len(self.lines)


class HorizontalRuleObject(Object):
    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        return "hr_virtual_object"

    @property
    def full(self) -> bool:
        return True

    def render(self, terminal: Terminal, width: int) -> None:
        terminal.sendText("\u2500" * width)

    def calculate(self, terminal: Terminal, width: int) -> int:
        return 1


class LabelObject(Object):
    def __init__(self, caption: str) -> None:
        self.caption = caption

    @property
    def name(self) -> str:
        return "label_virtual_object"

    @property
    def full(self) -> bool:
        return True

    def render(self, terminal: Terminal, width: int) -> None:
        terminal.sendText(self.caption[:width])

    def calculate(self, terminal: Terminal, width: int) -> int:
        return 1


class TemplateObject(Object):
    def __init__(self, template: str) -> None:
        self.template = template

    @property
    def name(self) -> str:
        return "template_virtual_object"

    @property
    def full(self) -> bool:
        return False

    def render(self, terminal: Terminal, width: int) -> None:
        # TODO: Actually substitute template values for remote API calls.
        template = self.template
        terminal.sendText(template[:width])

    def calculate(self, terminal: Terminal, width: int) -> int:
        return 1


class SwitchObject(Object):
    def __init__(self, entity: SwitchEntity, overridden_name: Optional[str]) -> None:
        self.entity: SwitchEntity = entity
        self.__overridden_name: Optional[str] = overridden_name
        self.__selected: bool = False
        self.__dirty: bool = True
        self.__lastName: str = entity.name
        self.__lastState: Optional[bool] = entity.state

    @property
    def name(self) -> str:
        return self.__overridden_name or self.entity.name

    @property
    def full(self) -> bool:
        return False

    @property
    def dirty(self) -> bool:
        return (
            self.__dirty
            or self.__lastName != self.name
            or self.__lastState != self.entity.state
        )

    @dirty.setter
    def dirty(self, newval: bool) -> None:
        self.__dirty = newval
        self.__lastName = self.name
        self.__lastState = self.entity.state

    @property
    def selectable(self) -> bool:
        return True

    @property
    def selected(self) -> bool:
        return self.__selected

    @selected.setter
    def selected(self, newval: bool) -> None:
        if newval != self.__selected:
            self.__dirty = True
        self.__selected = newval

    def toggle(self) -> None:
        self.entity.state = not self.entity.state

    def render(self, terminal: Terminal, width: int) -> None:
        state = (
            "UNK"
            if self.entity.state is None
            else ("ON " if self.entity.state else "OFF")
        )

        terminal.sendCommand(Terminal.SET_NORMAL)
        terminal.sendCommand(Terminal.SET_BOLD)
        terminal.sendText(f" {state} ")
        terminal.sendCommand(Terminal.SET_NORMAL)

        width -= 5
        if width <= 0:
            return

        selopen = "[" if self.__selected else " "
        selclose = "]" if self.__selected else " "

        text = (f"{selopen}{self.name}{selclose}")[:width]
        terminal.sendText(text)

    def calculate(self, terminal: Terminal, width: int) -> int:
        return 1


class SensorObject(Object):
    def __init__(self, entity: SensorEntity, overridden_name: Optional[str], overridden_units: Optional[str]) -> None:
        self.entity: SensorEntity = entity
        self.__overridden_name: Optional[str] = overridden_name
        self.__overridden_units: Optional[str] = overridden_units
        self.__dirty: bool = True
        self.__lastName: str = entity.name
        self.__lastState: Optional[str] = entity.state
        self.__lastUnits: Optional[str] = entity.units

    @property
    def name(self) -> str:
        return self.__overridden_name or self.entity.name

    @property
    def units(self) -> Optional[str]:
        return self.__overridden_units or self.entity.units

    @property
    def full(self) -> bool:
        return False

    @property
    def dirty(self) -> bool:
        return (
            self.__dirty
            or self.__lastName != self.name
            or self.__lastState != self.entity.state
            or self.__lastUnits != self.units
        )

    @dirty.setter
    def dirty(self, newval: bool) -> None:
        self.__dirty = newval
        self.__lastName = self.name
        self.__lastState = self.entity.state
        self.__lastUnits = self.units

    def render(self, terminal: Terminal, width: int) -> None:
        row, col = terminal.fetchCursor()

        state = "UNK" if self.entity.state is None else self.entity.state
        state += f" {self.units}" if self.units else ""
        name = f" {self.name} "

        terminal.sendCommand(Terminal.SET_NORMAL)
        terminal.sendText(name[:width])

        if len(name) + len(state) > width:
            row += 1
            terminal.moveCursor(row, col)
        else:
            width -= len(name)

        terminal.sendCommand(Terminal.SET_BOLD)
        terminal.sendText(f" {state} "[:width])
        terminal.sendCommand(Terminal.SET_NORMAL)

    def calculate(self, terminal: Terminal, width: int) -> int:
        state = "UNK" if self.entity.state is None else self.entity.state
        state += f" {self.units}" if self.units else ""
        name = f" {self.name} "

        if len(name) + len(state) > width:
            return 2
        else:
            return 1


class Renderer:
    def __init__(
        self,
        name: str,
        pages: List[Page],
        show_help_tab: bool,
        api: HomeAssistant,
        terminal: Terminal,
    ) -> None:
        self.name = name
        self.api = api
        self.terminal = terminal
        self.entities = api.getEntities() or []
        self.help_enabled = show_help_tab
        self.lastWidth = 0
        self.lastHeight = 0

        # Move cursor to where we expect it for input.
        self.terminal.moveCursor(self.terminal.rows, 1)
        self.lastError = ""
        self.input = ""
        self.cursorPos = 1

        # Set up tabs.
        self.pages = pages[:]
        self.currentPage = 0

        # Set up tracking entities for each type of home assistant entity.
        self.objects: List[List[Object]] = []
        keyed_entities: Dict[str, Entity] = {e.entity_id: e for e in self.entities}

        for page in pages:
            objlist: List[Object] = []
            for entity in page.entities:
                if entity.entity_id == "<hr>":
                    objlist.append(HorizontalRuleObject())
                elif entity.entity_id == "<label>":
                    objlist.append(LabelObject(entity.name or ""))
                elif entity.entity_id == "<template>":
                    objlist.append(TemplateObject(entity.name or ""))
                elif entity.entity_id in keyed_entities:
                    backing_entity = keyed_entities[entity.entity_id]
                    if isinstance(backing_entity, SwitchEntity):
                        objlist.append(SwitchObject(backing_entity, overridden_name=entity.name))
                    elif isinstance(backing_entity, SensorEntity):
                        objlist.append(SensorObject(backing_entity, overridden_name=entity.name, overridden_units=entity.units))
                    else:
                        objlist.append(Object(backing_entity, overridden_name=entity.name))

            for o in objlist:
                if o.selectable:
                    o.selected = True
                    break

            self.objects.append(objlist)

        if self.help_enabled:
            self.pages.append(Page("Help", []))
            self.objects.append([HelpObject()])

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
            self.terminal.sendCommand(Terminal.SET_NORMAL)
            self.terminal.sendCommand(Terminal.SET_BOLD)
            self.terminal.sendText(self.name)
            self.terminal.sendCommand(Terminal.SET_NORMAL)

            self.terminal.moveCursor(2, 1)
            self.terminal.sendText("\u2500" * self.terminal.columns)
            self.terminal.moveCursor(4, 1)
            self.terminal.sendText("\u2500" * self.terminal.columns)

            self.__renderTabs()

            # Move cursor to input that we previously typed.
            self.terminal.sendCommand(Terminal.RESTORE_CURSOR)
        else:
            # If we have input, we need to remember the cursor position.
            self.terminal.sendCommand(Terminal.SAVE_CURSOR)
            self.__renderPage(False)
            self.terminal.sendCommand(Terminal.RESTORE_CURSOR)

    def __renderTabs(self) -> None:
        self.terminal.moveCursor(3, 1)

        # First, render the tab heading.
        spaced = False
        for index, page in enumerate(self.pages):
            self.terminal.sendCommand(Terminal.SET_NORMAL)

            if spaced:
                self.terminal.sendText(" ")
            spaced = True

            self.terminal.sendCommand(Terminal.SET_REVERSE)
            if index == self.currentPage:
                self.terminal.sendCommand(Terminal.SET_BOLD)

            self.terminal.sendText(f" {page.name} ")

        # Now, render the entries themselves, treating them all as dirty.
        self.__renderPage(True)

    def __renderPage(self, allDirty: bool) -> None:
        cols = 2 if self.terminal.columns == 80 else 3
        curCol = cols - 1
        curRow = 4
        maxDrawnRow = 4

        maxHeight = 1
        width = self.terminal.columns // cols

        self.terminal.sendCommand(Terminal.SET_NORMAL)

        # TODO: Technically, since we support updating names, an object could go from a single
        # line to multiple lines, or the other way around. If this happens, we should really blank
        # the rest of the objecs after it as if everything was dirty. However, I haven't run into
        # this bug so I'm leaving it broken.

        for obj in self.objects[self.currentPage]:
            # Calculate width/height of this object.
            actualWidth = self.terminal.columns if obj.full else width

            # Calculate position for this object.
            curCol += 1
            if curCol >= cols:
                curCol = 0
                curRow += maxHeight
                maxHeight = 0
                if allDirty:
                    # TODO: Technically this is somewhat broken, because we need to clear ALL
                    # of the lines that the tallest component in any column occupies, but we
                    # don't currently run into this bug so I'm leaving it as future work.
                    for clearRow in range(
                        curRow, curRow + obj.calculate(self.terminal, actualWidth)
                    ):
                        self.terminal.moveCursor(clearRow, 1)
                        self.terminal.sendCommand(Terminal.CLEAR_LINE)

            if curCol != 0 and obj.full:
                curCol = 0
                curRow += maxHeight
                maxHeight = 0
                if allDirty:
                    for clearRow in range(
                        curRow, curRow + obj.calculate(self.terminal, actualWidth)
                    ):
                        self.terminal.moveCursor(clearRow, 1)
                        self.terminal.sendCommand(Terminal.CLEAR_LINE)

            # Calculate location of this object.
            row = curRow
            col = (width * curCol) + 1

            maxHeight = max(obj.calculate(self.terminal, actualWidth), maxHeight)
            if allDirty or obj.dirty:
                self.terminal.moveCursor(row, col)
                obj.render(self.terminal, actualWidth)
                obj.dirty = False

                maxDrawnRow = max(maxDrawnRow, curRow + (maxHeight - 1))

            # Move to the end of the column if this was a full width object.
            if obj.full:
                curCol = cols - 1

        if allDirty:
            # Need to wipe each row.
            for row in range(maxDrawnRow + 1, self.terminal.rows - 2):
                self.terminal.moveCursor(row, 1)
                self.terminal.sendCommand(Terminal.CLEAR_LINE)

    def __selection(self) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        prevobj = -1
        curobj = -1
        nextobj = -1

        lastSeen = -1
        for index, obj in enumerate(self.objects[self.currentPage]):
            if obj.selectable:
                if obj.selected:
                    # This is the currently selected object!
                    curobj = index
                    prevobj = lastSeen
                else:
                    if curobj == -1:
                        # If we haven't found the selected item, this could be the item before it.
                        lastSeen = index
                    elif nextobj == -1:
                        # If we have found the selected item, the next item is the one we tab to next.
                        nextobj = index

        return (
            None if prevobj == -1 else prevobj,
            None if curobj == -1 else curobj,
            None if nextobj == -1 else nextobj,
        )

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
        self.cursorPos = 1

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
        row, _ = self.terminal.fetchCursor()

        if inputVal == Terminal.LEFT:
            if self.cursorPos > 1:
                self.cursorPos -= 1
                self.terminal.moveCursor(row, self.cursorPos)
        elif inputVal == Terminal.RIGHT:
            if self.cursorPos < (len(self.input) + 1):
                self.cursorPos += 1
                self.terminal.moveCursor(row, self.cursorPos)
        elif inputVal == Terminal.UP:
            prevobj, curobj, nextobj = self.__selection()
            if prevobj is not None:
                if curobj is not None:
                    self.objects[self.currentPage][curobj].selected = False
                self.objects[self.currentPage][prevobj].selected = True
        elif inputVal == Terminal.DOWN:
            prevobj, curobj, nextobj = self.__selection()
            if nextobj is not None:
                if curobj is not None:
                    self.objects[self.currentPage][curobj].selected = False
                self.objects[self.currentPage][nextobj].selected = True
        elif inputVal in {Terminal.BACKSPACE, Terminal.DELETE}:
            if self.input:
                # Just subtract from input.
                if self.cursorPos == len(self.input) + 1:
                    # Erasing at the end of the line.
                    self.input = self.input[:-1]

                    self.cursorPos -= 1
                    self.terminal.moveCursor(row, self.cursorPos)
                    self.terminal.sendCommand(Terminal.SET_NORMAL)
                    self.terminal.sendCommand(Terminal.SET_REVERSE)
                    self.terminal.sendText(" ")
                    self.terminal.moveCursor(row, self.cursorPos)
                elif self.cursorPos == 1:
                    # Erasing at the beginning, do nothing.
                    pass
                elif self.cursorPos == 2:
                    # Erasing at the beginning of the line.
                    self.input = self.input[1:]

                    self.cursorPos -= 1
                    self.terminal.moveCursor(row, self.cursorPos)
                    self.terminal.sendCommand(Terminal.SET_NORMAL)
                    self.terminal.sendCommand(Terminal.SET_REVERSE)
                    self.terminal.sendText(self.input)
                    self.terminal.sendText(" ")
                    self.terminal.moveCursor(row, self.cursorPos)
                else:
                    # Erasing in the middle of the line.
                    spot = self.cursorPos - 2
                    self.input = self.input[:spot] + self.input[(spot + 1) :]

                    self.cursorPos -= 1
                    self.terminal.moveCursor(row, self.cursorPos)
                    self.terminal.sendCommand(Terminal.SET_NORMAL)
                    self.terminal.sendCommand(Terminal.SET_REVERSE)
                    self.terminal.sendText(self.input[spot:])
                    self.terminal.sendText(" ")
                    self.terminal.moveCursor(row, self.cursorPos)
        elif inputVal == b">":
            if self.currentPage < (len(self.pages) - 1):
                self.currentPage += 1

                self.terminal.sendCommand(Terminal.SAVE_CURSOR)
                self.__renderTabs()
                self.terminal.sendCommand(Terminal.RESTORE_CURSOR)
        elif inputVal == b"<":
            if self.currentPage > 0:
                self.currentPage -= 1

                self.terminal.sendCommand(Terminal.SAVE_CURSOR)
                self.__renderTabs()
                self.terminal.sendCommand(Terminal.RESTORE_CURSOR)
        elif inputVal == b"\r":
            # Ignore this.
            pass
        elif inputVal == b"\n":
            # Execute command.
            actual = self.input.strip()
            if not actual:
                # This could be a selection request
                _, cur, _ = self.__selection()
                if cur is not None:
                    self.objects[self.currentPage][cur].toggle()

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
            elif actual == "toggle" or actual.startswith("toggle "):
                if " " not in actual:
                    self.displayError("No switch specified!")
                else:
                    _, setting = actual.split(" ", 1)
                    setting = setting.strip().lower()

                    # See if we can find by exact match
                    for obj in self.objects[self.currentPage]:
                        if not obj.selectable:
                            continue

                        if obj.name.lower() == setting:
                            obj.toggle()
                            self.clearError()
                            self.clearInput()
                            break
                    else:
                        # We didn't, see if we can filter down to a single item by substring.
                        objs = [
                            o
                            for o in self.objects[self.currentPage]
                            if (o.selectable and (setting in o.name.lower()))
                        ]
                        if len(objs) == 1:
                            objs[0].toggle()
                            self.clearError()
                            self.clearInput()
                        else:
                            self.displayError("Unrecognized switch!")
                return None
            elif actual in {"n", "next"}:
                if self.currentPage < (len(self.pages) - 1):
                    self.currentPage += 1

                    self.terminal.sendCommand(Terminal.SAVE_CURSOR)
                    self.__renderTabs()
                    self.terminal.sendCommand(Terminal.RESTORE_CURSOR)

                self.clearInput()

                return None
            elif actual in {"p", "prev", "previous"}:
                if self.currentPage > 0:
                    self.currentPage -= 1

                    self.terminal.sendCommand(Terminal.SAVE_CURSOR)
                    self.__renderTabs()
                    self.terminal.sendCommand(Terminal.RESTORE_CURSOR)

                self.clearInput()

                return None
            elif actual == "help" and self.help_enabled:
                if self.currentPage != (len(self.pages) - 1):
                    self.currentPage = len(self.pages) - 1

                    self.terminal.sendCommand(Terminal.SAVE_CURSOR)
                    self.__renderTabs()
                    self.terminal.sendCommand(Terminal.RESTORE_CURSOR)

                self.clearInput()
            else:
                self.displayError(f"Unrecognized command {actual}")
        else:
            if len(self.input) < (self.terminal.columns - 1):
                # If we got some unprintable character, ignore it.
                inputVal = bytes(v for v in inputVal if v >= 0x20)
                if inputVal:
                    # Just add to input.
                    char = inputVal.decode("ascii")

                    if self.cursorPos == len(self.input) + 1:
                        # Just appending to the input.
                        self.input += char
                        self.terminal.sendCommand(Terminal.SET_NORMAL)
                        self.terminal.sendCommand(Terminal.SET_REVERSE)
                        self.terminal.sendText(char)
                        self.terminal.moveCursor(row, self.cursorPos + 1)
                        self.cursorPos += 1
                    else:
                        # Adding to mid-input.
                        spot = self.cursorPos - 1
                        self.input = self.input[:spot] + char + self.input[spot:]

                        self.terminal.sendCommand(Terminal.SET_NORMAL)
                        self.terminal.sendCommand(Terminal.SET_REVERSE)
                        self.terminal.sendText(self.input[spot:])
                        self.terminal.moveCursor(row, self.cursorPos + 1)
                        self.cursorPos += 1

        # Nothing happening here!
        return None
