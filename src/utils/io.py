import os


def get_song_name(path: str):
    name = path.split("/")[-1]
    name = name.split(".")[0]
    return name


def mkdir_if_not_exist(path: str, subdirs=None):
    if path.endswith("/"):
        path = path[:-1]
    if not os.path.exists(path):
        os.mkdir(path)
    if not subdirs is None:
        assert isinstance(subdirs, list)
        for subdir in subdirs:
            if not os.path.exists(f"{path}/{subdir}"):
                os.mkdir(f"{path}/{subdir}")