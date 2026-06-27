"""
QuantumPlay

Librariy Service

Responsable de toute la bibliothèque multimédia.
"""


from engine.library import MediaLibrary


class LibraryService:
    """
    Service responsable de la gestion de la bibliothèque multimédia.
    """

    def __init__(self):
        self.library = MediaLibrary()

    @property
    def items(self):
        return self.library.items

    def add_files(self, paths, on_progress=None):
        return self.library.add_files(
            paths,
            on_progress=on_progress
        )

    def add_folder_async(self, folder, on_done=None):
        self.library.add_folder_async(
            folder,
            on_done=on_done
        )

    def add_history(self, track):
        self.library.add_history(track)

    def grouped_history(self):
        return self.library.grouped_history()