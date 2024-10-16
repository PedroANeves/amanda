import logging
import os
import re
import sys
import tkinter as tk
from collections import namedtuple
from datetime import timedelta
from pathlib import Path
from tkinter import filedialog

from docx import Document  # type: ignore

from src.__version__ import VERSION

LOGGER = logging.getLogger(f"amanda-{VERSION}")
logging.basicConfig(filename=f"amanda-{VERSION}.log", level=logging.INFO)


EN_DASH = "\u2013"


def get_markers(filename: str, video_folder: str) -> list[str]:

    rows = extract_rows(filename)
    LOGGER.info("%s rows found", len(rows))
    LOGGER.info(rows)

    timestamps = extract_timestamps(rows)
    LOGGER.info("%s timestamps found", len(timestamps))
    LOGGER.info(timestamps)

    videos = find_file(video_folder)
    LOGGER.info("%s videos found", len(videos))
    LOGGER.info(videos)

    built_lines = build_lines(timestamps, videos)
    return built_lines


Row = namedtuple("Row", ["first", "last"])


def extract_rows(filename: str | type[Document]) -> list[Row]:
    """Usage: lines = extract_rows('document.docx')

    # document.docx
    .--------------------------------------+----------------------------------.
    |Remember when the cool thing happened?|V1 00:01:15 – Cool thing happened.|
    `--------------------------------------+----------------------------------`

    lines == [
        (
            "Remember when the cool thing happened?",
            "V1 00:01:15 – Cool thing happened.",
        ),
    ]
    """
    document = Document(filename)
    table = document.tables[0]
    lines = [Row(row.cells[0].text, row.cells[1].text) for row in table.rows]
    return lines


def extract_timestamps(lines: list[Row]) -> list[tuple[str, str]]:
    return [
        timestamp
        for line in lines
        if _has_timestamp(line.last)
        for timestamp in _extract_name_and_timestamp(line.last)
    ]


def find_file(this_dir: str) -> dict[str, str]:
    all_files = list(os.scandir(this_dir))
    LOGGER.info("%s files total", len(all_files))
    LOGGER.info(all_files)
    lines = {
        _get_prefix(file): file.path
        for file in all_files
        if _file_has_prefix(file)
    }
    return lines


def build_lines(timestamps, videos):
    return [
        (
            videos.get(prefix, f"NOT_FOUND_{prefix}"),
            time_start,
            _add_time_delta(time_start, 10),
        )
        for prefix, time_start in timestamps
    ]


IMAGE_FMT = r"(?P<prefix>[JV]\d+) ?(?P<timestamp>\d{2}:\d{2}:\d{2})?"
image_pattern = re.compile(IMAGE_FMT)


def _extract_name_and_timestamp(from_line: str) -> list[tuple[str, str]]:
    matches = image_pattern.finditer(from_line)
    if not matches:
        raise ValueError(matches)

    return [
        (
            match.groupdict()["prefix"],
            match.groupdict().get("timestamp") or "00:00:00",
        )
        for match in matches
    ]


def _has_timestamp(line: str) -> bool:
    return bool(image_pattern.match(line))


PREFIX = r"^(?P<prefix>[VJ]\d+).*"
pattern = re.compile(PREFIX)


def _get_prefix(file: os.DirEntry) -> str:
    m = pattern.match(file.name)
    if m is None:
        raise ValueError()
    return m.groupdict()["prefix"]


def _file_has_prefix(file: os.DirEntry) -> bool:
    return file.is_file() and pattern.match(file.name) is not None


def _add_time_delta(start: str, delta: int = 10) -> str:
    hs, mins, s = map(int, start.split(":", maxsplit=2))
    start_stamp = timedelta(hours=hs, minutes=mins, seconds=s)
    end = start_stamp + timedelta(seconds=delta)

    hours, _remains = divmod(int(end.total_seconds()), 60 * 60)
    minutes, seconds = divmod(_remains, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def save_csv(data: list, filename: Path) -> None:
    with open(filename, mode="w", encoding="utf-8") as f:
        lines = format_lines(data)
        for line in lines:
            f.write(line)


def tk_gui(marker_strategy, title):
    bg_color = "#2E2E2E"
    fg_color = "white"

    root = tk.Tk()
    root.title(title)
    root.config(bg=bg_color)

    # video folder
    video_folder_frame = tk.Frame(
        root,
        bg=bg_color,
    )
    video_folder_frame.pack(padx=10, pady=10)

    video_folder_label = tk.Label(
        video_folder_frame,
        text=os.getcwd(),
        wraplength=400,
        anchor="w",
        justify="left",
    )
    video_folder_label.grid(row=0, column=0, sticky="w", padx=5)

    def _ui_pick_folder():
        folderpath = filedialog.askdirectory()

        if not folderpath:  # hit 'cancel' or closed dialog
            return

        video_folder_label.config(text=folderpath)

    # pick video folder
    pick_folder_button = tk.Button(
        video_folder_frame,
        text="Choose Videos folder",
        command=_ui_pick_folder,
        bg=bg_color,
        fg=fg_color,
    )
    pick_folder_button.grid(row=0, column=1, sticky="w", padx=5)

    # doc path
    doc_path_frame = tk.Frame(
        root,
        bg=bg_color,
    )
    doc_path_frame.pack(padx=10, pady=10)

    doc_path_label = tk.Label(
        doc_path_frame,
        text="no file",
        wraplength=400,
        anchor="w",
        justify="left",
    )
    doc_path_label.grid(row=0, column=0, sticky="w", padx=5)

    def _ui_pick_file():
        filename = filedialog.askopenfilename(
            filetypes=(("docx", "*.docx"),),
        )

        if not filename:  # hit 'cancel' or closed dialog
            return

        lines = marker_strategy(filename, video_folder_label.cget("text"))
        formated_lines = format_lines(lines)
        file_contents = "".join(formated_lines)
        text_display.delete(1.0, tk.END)
        text_display.insert(tk.END, file_contents)

    # pick file button
    pick_file_button = tk.Button(
        doc_path_frame,
        text="Load a .docx",
        command=_ui_pick_file,
        bg=bg_color,
        fg=fg_color,
    )
    pick_file_button.grid(row=0, column=1, sticky="w", padx=5)

    # display
    text_display = tk.Text(
        root,
        wrap=tk.WORD,
        bg=bg_color,
        fg=fg_color,
        insertbackground=fg_color,
    )
    text_display.pack(expand=True, fill=tk.BOTH)

    def _ui_copy_all():
        all_text = text_display.get(1.0, tk.END)
        root.clipboard_clear()
        root.clipboard_append(all_text)
        root.update()

    # copy button
    copy_button = tk.Button(
        root,
        text="Copy All",
        command=_ui_copy_all,
        bg=bg_color,
        fg=fg_color,
    )
    copy_button.pack(pady=10)

    def _ui_save_csv():
        f = filedialog.asksaveasfile(
            mode="w",
            defaultextension=".csv",
            initialfile=f"amanda-{VERSION}.csv",
            filetypes=(("csv", "*.csv"),),
        )

        if not f:  # user hit 'cancel' or closed dialog
            return

        text2save = text_display.get(1.0, tk.END)
        f.write(text2save)
        f.close()

    # save button
    save_button = tk.Button(
        root,
        text="Save CSV File",
        command=_ui_save_csv,
        bg=bg_color,
        fg=fg_color,
    )
    save_button.pack(pady=10)

    root.mainloop()


def format_lines(data: list[tuple[str, str, str]]) -> list[str]:
    return [
        f"{_normalize_path(line[0])},{line[1]},{line[2]}\n" for line in data
    ]


def format_lines_with_header(data: list[tuple[str, str, str]]) -> list[str]:
    return ["filepath,start,end\n"] + format_lines(data)


def _normalize_path(raw_path: str) -> str:
    # TODO change bulshit fix
    if sys.platform == "win32":
        return raw_path.replace("/", "\\")

    return raw_path.replace("\\", "/")


def main():

    tk_gui(marker_strategy=get_markers, title=f"Amanda Software - {VERSION}")

    return 0


if __name__ == "__main__":
    main()
