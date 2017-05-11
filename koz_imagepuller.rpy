# Ren'Py Image Puller v1.0.0
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

        def save_png(self, filename, img, subfolder=None):
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

        def pull(self, exclude=(), only=()):
            """Runs the process of image pulling.

            :param exclude: A list of character tags that should be skipped.
            :type exclude: list(str) or tuple(str)

            :param only: A list of character tags whose images should be pulled. If this argument is not empty, all other tags, not listed here, will be skipped.
            :type only: list(str) or tuple(str)

            :returns: True if *all* images have been unpacked successfully and False otherwise (usually it happens when the game is out of memory).
            :rtype: bool
            """

            from renpy.display.image import images

            only_enabled = len(only) > 0
            for k, v in images.iteritems():
                if k[0] in exclude or only_enabled and k[0] not in only:
                    continue
                name = "_".join(k)

                try:
                    self.save_png(name, v, k[0])
                except Exception:
                    return False

            return True

        def pull_async(self, exclude=(), only=(), delay=0):
            """
            Runs the Pull() method (runs the process of image pulling) in another thread.
            This prevents the game from freezing, but it still will be less responsive until the operation is done.
            Additionally, this method gives you a way to delay the pulling for a while to let the game initialize its resources completely.
            This method tries to solve the problem with crashes described in the description of Pull() by recreating new threads unless all images will be unpacked.

            :param exclude: A list of character tags that should be skipped.
            :type exclude: list(str) or tuple(str)

            :param only: A list of character tags whose images should be pulled. If this argument is not empty, all other tags, not listed here, will be skipped.
            :type only: list(str) or tuple(str)

            :param delay: The pulling will be started after a specified number of seconds.
            :type delay: int or float
            """

            from threading import Timer

            def run():
                if not self.pull(exclude, only):
                    self.pull_async(exclude, only)

            timer = Timer(delay, run)
            timer.start()


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


label koz_imagepuller_es:
    $ day_time()
    $ persistent.sprite_time = "day"
    scene bg ext_beach_day with fade
    show dv smile swim far at left with dissolve
    show sl smile swim far at right with dissolve
    show us grin swim far at center with dissolve

    us "Привет, шалунишка! Хочешь извлечь наши спрайты?"    
    dv "И чьи же спрайты ты хочешь стянуть?"
    
    $ char_set = []
    call koz_imagepuller_es_append(char_set)

    sl "ОК! Сейчас начнётся процесс извлечения спрайтов."
    us "Кликни, чтобы продолжить... Бла-бла-бла, все дела..."

    $ koz_ImagePuller().pull_async(only=char_set)

    sl "Процесс пошёл... Как игра перестанет подтормаживать, а в папке \"Pulled images\" в директории с игрой перестанут появляться новые файлы и папки, можешь выйти отсюда через меню."
    jump koz_imagepuller_es_wait

label koz_imagepuller_es_append(char_set):
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

    call koz_imagepuller_es_append(char_set)
    return

label koz_imagepuller_es_wait:
    dv "Ну и зачем ты тыкаешь? Просто жди, пока все файлы извлекутся и игра перестанет тормозить. Затем выходи через меню."
    us "Ну почему ты просто не можешь делать то, что тебе говорят?"
    jump koz_imagepuller_es_wait
