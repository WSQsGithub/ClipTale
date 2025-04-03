from pathlib import Path
from typing import Any, Optional

from src.cliptale.cliplabeler import ClipLabeler


class LabelerPipeline:
    def __init__(self, work_dir: Path, rename_template: Optional[str] = None):
        self.work_dir = work_dir
        self.file_paths: list[Path] = []
        self.rename_template = rename_template
        self.results = dict[str, Any]  # Placeholder for results

        _ = self.read_directory()

    def read_directory(self) -> list[Path]:
        """
        Read all the video files in the given directory.

        Args:
            work_dir (Path): The directory containing files to process.
        """
        file_paths = []
        for file_path in self.work_dir.iterdir():
            if file_path.is_file():
                file_paths.append(file_path)
        self.file_paths = file_paths

        return file_paths

    async def run(self) -> None:
        # read all files in the work_dir
        for file_path in self.file_paths:
            clip_labeler = ClipLabeler(file_path)
            if self.rename_template:
                clip_labeler.add_template(self.rename_template)
            clip_labeler.read_video()
            clip_labeler.extract_audio()
            clip_labeler.generate_label()
            clip_labeler.save_label()
        # Placeholder for any additional pipeline logic
        # e.g. cleanup, logging, etc.
        return

    def __str__(self) -> str:
        return f"LabelerPipeline(work_dir={self.work_dir}, rename_template={self.rename_template})"


async def run_labeler_pipeline(work_dir: Path, rename_template: Optional[str] = None) -> None:
    """
    Run the LabelerPipeline asynchronously.

    Args:
        work_dir (Path): The directory containing files to process.
        rename_template (Optional[str]): The template for renaming files.
    """
    pipeline = LabelerPipeline(work_dir, rename_template)
    await pipeline.run()
