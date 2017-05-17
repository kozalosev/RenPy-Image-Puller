# Ren'Py Image Puller v1.1.0
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
# 7. Select sets for the times of day you want and click "Закончить выбор".
# 8. Select a set of sprites depending on the distance between the characters and the player.
# 9. Wait...
# 10. Click on the button named "Выйти".
# 11. See /Pulled images/ directory.

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

        def __init__(self, dir_name="Pulled images", trim=True):
            """Constructor.
            :param dir_name: The name of a directory you want to save images into.
            :type dir_name: str

            :param trim: Should the puller trim transparent areas of images? By default, it's True.
            :type trim: bool
            """

            import os

            path = os.path.join(config.basedir, dir_name)
            self.ensure_path_exists(path)
            self.output_dir = path

            self.trim = trim
            self.stop_flag = False

        @staticmethod
        def ensure_path_exists(path):
            """
            This function is a backport for Python 2 and equivalent to `os.makedirs(path, exist_ok=True)` in Python 3.

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

            :param container_ids: Should the puller extracts all images from containers or only some of them? By default, it extracts everything,
                                  but you can change this behavior and set indexes manually. If an index is greater than the count of images,
                                  it will be ignored. Negative values will be the cause of the assertion error.
            :type container_ids: list(int) or tuple(int)
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
                            new_filename = "%s_%i" % (filename, id + 1)
                            image = dynamic_displayable.args[0][id][1]
                            self.save_png(new_filename, image, subfolder)
                        else:
                            koz_imagepuller_log("Wrong image ID! %i is not in %s." % (id, dynamic_displayable))
                else:
                    for i, (condition, image) in enumerate(dynamic_displayable.args[0]):
                        new_filename = "%s_%i" % (filename, i + 1)
                        self.save_png(new_filename, image, subfolder)
                return
            elif not isinstance(img, ImageBase):
                koz_imagepuller_log("Unknown type of image! (%s, %s)" % (filename, type(filename)))
                return

            # pygame.image.save(surf, path)
            # The standard PyGame function refused to process Russian paths correctly.
            # Because of that, I had to write my own implementation relying on examples from Ren'Py source code and its `take_screenshot()` method of the Interface class.

            surf = img.load()
            # Trims a transparent background.
            if self.trim:
                rect = surf.get_bounding_rect()
                surf = surf.subsurface(rect)

            sio = cStringIO.StringIO()
            save_png(surf, sio)
            content = sio.getvalue()
            sio.close()

            with open(path, "wb") as f:
                f.write(content)

        def pull(self, exclude=(), only=(), has_components=(), exclude_components=(), container_ids=(), progress_callback=None):
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

            :param progress_callback: This function will be called after each image being extracted. It must take 3 arguments: progress (number in the range [0; 1]),
                                      the index of the last extracted image, and the total number of images (images in a container are considered as one image).
            :type progress_callback: callable

            :returns: True if *all* images have been unpacked successfully and False otherwise (usually it happens when the game is out of memory).
            :rtype: bool
            """

            params = (exclude, only, has_components, exclude_components)
            if not self._iterator or not self._iterator.is_valid(*params):
                log_params = list(params)
                log_params.append(container_ids)
                koz_imagepuller_log("Creating a new iterator with the following parameters:", *log_params)

                self._iterator = self.CachedIterator(*params)

            k, v = self._iterator.get()
            while k is not None:
                if self.stop_flag:
                    return False

                name = "_".join(k)
                try:
                    self.save_png(name, v, k[0], container_ids)
                except Exception as err:
                    koz_imagepuller_log(err)
                    return False

                if progress_callback:
                    progress_callback(self._iterator.progress, self._iterator.i, self._iterator.total)

                k, v = self._iterator.get()

            if progress_callback:
                progress_callback(self._iterator.progress, self._iterator.i, self._iterator.total)
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
                try:
                    pulling_result = self.pull(**kwargs)
                except Exception as err:
                    koz_imagepuller_log(err)
                    return

                if not pulling_result and not self.stop_flag:
                    koz_imagepuller_log("The working thread is down! Recreating...")
                    self.pull_async(**kwargs)

            timer = Timer(delay, run)
            timer.daemon = True
            timer.start()

        def stop(self):
            """Sets the stop flag to True."""
            self.stop_flag = True


        class CachedIterator:
            """Used to continue the pulling, when it fails, from an image following the failed one."""

            def __init__(self, exclude=(), only=(), has_components=(), exclude_components=()):
                """Constructor. See the docstring of the `pull` method to know about the arguments."""

                self._exclude = exclude
                self._only = only
                self._has_components = has_components
                self._exclude_components = exclude_components

                self._i = 0
                self.reload_iterator()

            def is_valid(self, exclude=(), only=(), has_components=(), exclude_components=()):
                """
                :returns: True if the iterator is consistent with the arguments, and False otherwise.
                :rtype: bool
                """
                return not (self._exclude != exclude or self._only != only or self._has_components != has_components or self._exclude_components != exclude_components)

            def reload_iterator(self):
                """Reloads the iterator and moves its cursor to the previous position.
                I don't know why the iterator reaches its end faster than the moment when all images will be fetched.
                """

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
                import itertools

                filtered_images = {k:v for k, v in images.iteritems() if img_filter(k)}
                self._iterator = filtered_images.iteritems()
                self._iterator = itertools.islice(self._iterator, self._i, None)
                self._total = len(filtered_images)

            def get(self):
                """
                :returns: A tuple of the tuple of name components, and the image.
                :rtype: tuple
                """
                try:
                    item = self._iterator.next()
                except StopIteration:
                    if self._i < self._total:
                        koz_imagepuller_log("The iterator has reached its end, but we have more items. Reloading it...")
                        self.reload_iterator()
                        return self.get()
                    else:
                        return None, None

                self._i += 1
                return item

            @property
            def i(self):
                """Property.
                :returns: The index of current position of the iterator.
                :rtype: int
                """
                return self._i

            @property
            def total(self):
                """Property.
                :returns: A total number of images.
                :rtype: int
                """
                return self._total

            @property
            def progress(self):
                """Property.
                :returns: A float-point number between 0 and 1 representing the fraction of work performed.
                :rtype: float
                """
                return float(self._i) / self._total if self._total > 0 else 1


    def koz_imagepuller_log(*args):
        """Writes a message to the log file.
        :param args: Any objects that can be cast to strings. For exceptions a full traceback will be written.
        """

        from datetime import datetime
        import inspect
        
        datestr = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _, _, _, funcname, _, _ = inspect.stack()[1]
        infostr = "%s (%s)" % (datestr, funcname)
        length = len(infostr)

        with open("koz_imagepuller.log", 'a') as f:
            f.write("\n%s\n" % ('-' * length))
            f.write(infostr)
            f.write("\n%s\n" % ('-' * length))

            for obj in args:
                if isinstance(obj, Exception):
                    import traceback
                    traceback.print_exc(file=f)
                else:
                    f.write(str(obj) + '\n')


    # For Everlasting Summer I provide a convenient way to start the pulling via the standard mod selector.
    if config.name == "Everlasting Summer" and "mods" in vars() and type(mods) is dict:
        mods["koz_imagepuller_es"] = "Image Puller"

        GLOBAL_KOZ_IMAGEPULLER_PROGRESS = 0
        GLOBAL_KOZ_IMAGEPULLER_PROGRESSBAR_VALUE = 0
        GLOBAL_KOZ_IMAGEPULLER_PROGRESSBAR_MAX = 0

        def koz_imagepuller_progress_update(progress, i, total):
            """Manages the global variables which values are reflected on the progress bar."""

            global GLOBAL_KOZ_IMAGEPULLER_PROGRESS, GLOBAL_KOZ_IMAGEPULLER_PROGRESSBAR_VALUE, GLOBAL_KOZ_IMAGEPULLER_PROGRESSBAR_MAX
            GLOBAL_KOZ_IMAGEPULLER_PROGRESS = progress
            GLOBAL_KOZ_IMAGEPULLER_PROGRESSBAR_VALUE = i
            GLOBAL_KOZ_IMAGEPULLER_PROGRESSBAR_MAX = total

            renpy.restart_interaction()

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


# A part of my implementation of LolBot's idea about a progress bar. Uses some hints given by him.
screen koz_imagepuller_es_progress_bar:
    window background "#000000BF":
        vbox align(0.5, 0.5):
            if GLOBAL_KOZ_IMAGEPULLER_PROGRESS < 1:
                label "Пожалуйста, подождите..." xalign 0.5
            else:
                label "Готово!" xalign 0.5
            hbox xminimum 0.5 xmaximum 0.5:
                bar value GLOBAL_KOZ_IMAGEPULLER_PROGRESS range 1
            label "%d/%d" % (GLOBAL_KOZ_IMAGEPULLER_PROGRESSBAR_VALUE, GLOBAL_KOZ_IMAGEPULLER_PROGRESSBAR_MAX) xalign 0.5
            null height 20
            if GLOBAL_KOZ_IMAGEPULLER_PROGRESS >= 1:
                textbutton "Выход" action Jump("koz_imagepuller_es_done") xalign 0.5
            else:
                textbutton "Прервать" action Jump("koz_imagepuller_es_stop") xalign 0.5


# Entry point
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

    sl "Спрайты будут рассортированы по папкам внутри директории \"Pulled images\", находящейся в каталоге с игрой."
    us "Кликни, чтобы продолжить... Бла-бла-бла, все дела..."

    # Prevents additional runs of the pulling with possible wrong options.
    $ renpy.block_rollback()

    $ GLOBALS_KOZ_IMAGEPULLER_INSTANCE = koz_ImagePuller()
    $ GLOBALS_KOZ_IMAGEPULLER_INSTANCE.pull_async(only=char_set,
                                                  has_components=include_distances_set,
                                                  exclude_components=exclude_distances_set,
                                                  container_ids=daytime_set,
                                                  progress_callback=koz_imagepuller_progress_update)
    show screen koz_imagepuller_es_progress_bar
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
    return

# A loop, that will be executing unless either the work will be done, or the user asks to terminate the pulling.
# Blocks interaction for the user.
label koz_imagepuller_es_wait:
    $ ui.interact()
    jump koz_imagepuller_es_wait

# Called if the user asked to terminate the pulling.
label koz_imagepuller_es_stop:
    $ GLOBALS_KOZ_IMAGEPULLER_INSTANCE.stop()
    jump koz_imagepuller_es_done

# Exit point
label koz_imagepuller_es_done:
    hide screen koz_imagepuller_es_progress_bar
    return
