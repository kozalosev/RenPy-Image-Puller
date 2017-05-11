﻿# Ren'Py Image Puller v1.0.0
# Scans all defined images and unpack them to the disk.
# (c) Leonid Kozarin <kozalo@nekochan.ru> [http://kozalo.ru], 2017
# License: MIT

# =======================================
# HOW TO USE IT WITH "EVERLASTING SUMMER"
# =======================================
# 1. Put this file into your /game/ directory.
# 2. Run the game.
# 3. Go to the mod selector in the settings.
# 4. Run the "Image Puller" mod.
# 5. Click until you reaches a menu.
# 6. Select characters you want and click "Закончить выбор".
# 7. Wait unless the game becomes responsive again.
# 8. See /Pulled images/ directory.
# 9. Exit via the context menu.

# ===================================
# WHAT ABOUT OTHER RENPY-BASED GAMES?
# ===================================
# Follow the steps 1 and 2 from the instruction above. But you have to write some code yourself between them.
# Class koz_ImagePuller is pretty universal (at least I hope). But it depends on you to initialize it properly for a certain game.
# I've prepared some examples at the end of the init block below. See them for more information.


init python:
    class koz_ImagePuller:
        """This is the main class that encapsulates all logic related to resource fetching and writing to the disk."""

        # See the CachedIterator class.
        _iterator = None

        def __init__(self, dir_name="Pulled images"):
            """Constructor.
            :param dir_name: The name of a directory you want to save images into.
            :type dir_name: str
            """

            import os

            path = os.path.join(config.basedir, dir_name)
            self.ensure_path_exists(path)
            self.output_dir = path

        @staticmethod
        def ensure_path_exists(path):
            """
            This function is a backport for Python 2 and equivalent to `os.makedirs(path, exist_ok=True)` in Python 3.
            Was taken from: http://stackoverflow.com/a/600612

            :param path: A path to some directory.
            :type path: str
            """

            import os

            if os.path.isdir(path):
                return
            os.makedirs(path)

        def save_png(self, filename, img, subfolder=None, container_ids=()):
            """
            This is the main operating method that fetches one image and write it to the disk.
            If the image is actually a container (in case of ConditionSwitch, for example), it calls self recursevely to save all internal images.

            :param filename: The image will be saved as a file with a supplied name.
            :type filename: str

            :param img: A Ren'Py image. All descendants of ImageBase and Position may be passed here. Other types will be ignored.
            :type img: ImageBase or Position

            :param subfolder: The name of a folder in which the image will be saved.
            :type subfolder: str
            """

            from renpy.display.module import save_png
            from renpy.display.im import ImageBase
            from renpy.display.layout import Position
            import cStringIO
            import os

            if subfolder:
                subfolder_path = os.path.join(self.output_dir, subfolder)
                self.ensure_path_exists(subfolder_path)
                path = os.path.join(subfolder_path, filename + ".png")
            else:
                path = os.path.join(self.output_dir, filename + ".png")

            # If the file already exists, we won't overwrite it.
            if os.path.isfile(path):
                return
            
            if isinstance(img, Position):
                dynamic_displayable = img.child
                # I want to thank LolBot (https://github.com/lolbot-iichan) for image filters in Everlasting Summer that I used as an example.
                if container_ids:
                    for id in container_ids:
                        assert id >= 0, "Negative value in container_ids! (%i)" % id
                        if id < len(dynamic_displayable.args[0]):
                            new_filename = "%s_%i" % (filename, id)
                            image = dynamic_displayable.args[0][id][1]
                            self.save_png(new_filename, image, subfolder)
                else:
                    for i, (condition, image) in enumerate(dynamic_displayable.args[0]):
                        new_filename = "%s_%i" % (filename, i+1)
                        self.save_png(new_filename, image, subfolder)
                return
            elif not isinstance(img, ImageBase):
                return

            # pygame.image.save(surf, path)
            # The standard PyGame function refused to process Russian paths correctly.
            # Because of that, I had to write my own implementation relying on examples from Ren'Py source code and its `take_screenshot()` method of the Interface class.

            surf = img.load()
            sio = cStringIO.StringIO()
            save_png(surf, sio)
            content = sio.getvalue()
            sio.close()

            with open(path, "wb") as f:
                f.write(content)

        def pull(self, exclude=(), only=(), has_components=(), exclude_components=(), container_ids=()):
            """Runs the process of image pulling.

            :param exclude: A list of character tags that should be skipped.
            :type exclude: list(str) or tuple(str)

            :param only: A list of character tags whose images should be pulled. If this argument is not empty, all other tags, not listed here, will be skipped.
            :type only: list(str) or tuple(str)

            :param has_components: A list of parameters (clothes, emotion) that the image must have.
            :type has_components: list(str) or tuple(str)

            :param exclude_components: A list of parameters (clothes, emotion) that the image must NOT have.
            :type exclude_components: list(str) or tuple(str)

            :param container_ids: If the image is actually a container, the puller extracts all images from them by default. You can set indexes manually.
                                  If an index is greater than the count of images, it will be ignored. Negative values will be the cause of the assertion error.
            :type container_ids: list(int) or tuple(int)

            :returns: True if *all* images have been unpacked successfully and False otherwise (usually it happens when the game is out of memory).
            :rtype: bool
            """

            params = (exclude, only, has_components, exclude_components)
            if not self._iterator or not self._iterator.is_valid(*params):
                self._iterator = self.CachedIterator(*params)

            for k, v in self._iterator.get():
                name = "_".join(k)
                try:
                    self.save_png(name, v, k[0], container_ids)
                except Exception as err:
                    self.__log(err)
                    return False

            return True

        def pull_async(self, delay=0, **kwargs):
            """
            Runs the Pull() method (runs the process of image pulling) in another thread.
            This prevents the game from freezing, but it still will be less responsive until the operation is done.
            Additionally, this method gives you a way to delay the pulling for a while to let the game initialize its resources completely.
            This method tries to solve the problem with crashes described in the description of Pull() by recreating new threads unless all images will be unpacked.

            :param delay: The pulling will be started after a specified number of seconds.
            :type delay: int or float

            Also, it takes all keyword arguments that a non-asynchronous version does.
            """

            from threading import Timer

            def run():
                if not self.pull(**kwargs):
                    self.pull_async(**kwargs)

            timer = Timer(delay, run)
            timer.start()

        @staticmethod
        def __log(obj):
            """Writes a message to the log file.
            :param obj: Any object that can be cast to a string. If it's an exception, a full traceback will be written.
            """

            with open("koz_imagepuller-errors.log", 'a') as f:
                if isinstance(obj, Exception):
                    import traceback
                    traceback.print_exc(file=f)
                else:
                    f.write(str(obj))


        class CachedIterator:
            """Used to continue the pulling, when it fails, from an image following the failed one."""

            def __init__(self, exclude=(), only=(), has_components=(), exclude_components=()):
                """Constructor. See the docstring of the `pull` method to know about the arguments."""

                self._exclude = exclude
                self._only = only
                self._has_components = has_components
                self._exclude_components = exclude_components

                def img_filter(k):
                    """
                    :param k: The list of name components of an image.
                    :type k: tuple(str)
                    """

                    if k[0] in self._exclude or self._only and k[0] not in self._only:
                        return False
                    for component in self._has_components:
                        if component not in k:
                            return False
                    for component in self._exclude_components:
                        if component in k:
                            return False

                    return True

                from renpy.display.image import images

                filtered_images = {k:v for k,v in images.iteritems() if img_filter(k)}
                self._iterator = filtered_images.iteritems()

            def is_valid(self, exclude=(), only=(), has_components=(), exclude_components=()):
                """
                :returns: True if the iterator is consistent with the arguments, and False otherwise.
                :rtype: bool
                """
                return not (self._exclude != exclude or self._only != only or self._has_components != has_components or self._exclude_components != exclude_components)

            def get(self):
                """
                :returns: The actual iterator.
                :rtype: dictionary-itemiterator
                """
                return self._iterator


    # For Everlasting Summer I provide a convenient way to start the pulling via the standard mod selector.
    if config.name == "Everlasting Summer" and "mods" in vars() and type(mods) is dict:
        mods["koz_imagepuller_es"] = "Image Puller"

    # For other games I see two ways:
    # - You may call the `pull()` or `pull_async()` method somewhere in the code of the game manually. This is a more reliable way.
    #   $ koz_ImagePuller().pull()
    #   or
    #   $ koz_ImagePuller().pull_async()
    # - You may try to delay the execution of the `pull_async()` method within an initialization block.
    #   This way is less reliable and may not work, but easier: just uncomment the line below and adjust the delay value.
    #   $ koz_ImagePuller().pull_async(delay=10)
    # If you want to pull images for only certain characters, pass a list of tags as the `only` argument.
    # Another way to constrain the pulling is to use the `exclude` argument, which also gets a list of tags which must be skipped.
    # There are other filters such as `has_components`, `exclude_components`, and `container_ids` as well.
    # The first two ones are responsible for filtering over standard Ren'Py image modifiers.
    # The last parameter lets you constrain pulling from containers up to determined list of indexes.


label koz_imagepuller_es:
    $ day_time()
    $ persistent.sprite_time = "day"
    scene bg ext_beach_day with fade
    show dv smile swim far at left with dissolve
    show sl smile swim far at right with dissolve
    show us grin swim far at center with dissolve

    us "Привет, шалунишка! Хочешь извлечь наши спрайты?"    
    dv "И чьи же спрайты ты хочешь стянуть?"
    
    $ char_set, daytime_set = [], []
    $ include_distances_set, exclude_distances_set = [], []
    call koz_imagepuller_es_append_char(char_set)
    call koz_imagepuller_es_append_daytime(daytime_set)
    call koz_imagepuller_es_select_distance(include_distances_set, exclude_distances_set)

    sl "ОК! Сейчас начнётся процесс извлечения спрайтов."
    us "Кликни, чтобы продолжить... Бла-бла-бла, все дела..."

    $ koz_ImagePuller().pull_async(only=char_set, has_components=include_distances_set, exclude_components=exclude_distances_set, container_ids=daytime_set)

    sl "Процесс пошёл... Как игра перестанет подтормаживать, а в папке \"Pulled images\" в директории с игрой перестанут появляться новые файлы и папки, можешь выйти отсюда через меню."
    jump koz_imagepuller_es_wait

label koz_imagepuller_es_append_char(char_set):
    python:
        def koz_mark_char(code):
            if code not in char_set:
                char_set.append(code)

    menu:
        "Алисы":
            $ koz_mark_char("dv")
        "Слави":
            $ koz_mark_char("sl")
        "Ульянки":
            $ koz_mark_char("us")
        "Юли":
            $ koz_mark_char("uv")
        "Мику":
            $ koz_mark_char("mi")
        "Лены":
            $ koz_mark_char("un")
        "Жени":
            $ koz_mark_char("mz")
        "Ольги Дмитриевны":
            $ koz_mark_char("mt")
        "Виолы":
            $ koz_mark_char("cs")
        "Электроника":
            $ koz_mark_char("el")
        "Шурика":
            $ koz_mark_char("sh")
        "Закончить выбор":
            return

    call koz_imagepuller_es_append_char(char_set)
    return

label koz_imagepuller_es_append_daytime(daytime_set):
    python:
        def koz_add_daytime(id):
            if id not in daytime_set:
                daytime_set.append(id)

    menu:
        "Время суток"

        "Закат":
            $ koz_add_daytime(0)
        "Ночь":
            $ koz_add_daytime(1)
        "День":
            $ koz_add_daytime(2)
        "Закончить выбор":
            return

    call koz_imagepuller_es_append_daytime(daytime_set)
    return

label koz_imagepuller_es_select_distance(include_distances_set, exclude_distances_set):
    $ exclude_distances_set.append("body")
    menu:
        "Все":
            pass
        "Обычные":
            $ exclude_distances_set.append("close")
            $ exclude_distances_set.append("far")
        "Крупным планом":
            $ include_distances_set.append("close")
        "В отдалении":
            $ include_distances_set.append("far")
        "Обнажённые":
            $ exclude_distances_set.remove("body")
            $ include_distances_set.append("body")
    return

label koz_imagepuller_es_wait:
    dv "Ну и зачем ты тыкаешь? Просто жди, пока все файлы извлекутся и игра перестанет тормозить. Затем выходи через меню."
    us "Ну почему ты просто не можешь делать то, что тебе говорят?"
    jump koz_imagepuller_es_wait
