Ren'Py Image Puller v1.1.0
==========================

Scans all defined images and unpack them to the disk.  

(c) Leonid Kozarin <kozalo@nekochan.ru> [http://kozalo.ru], 2017.  
License: MIT.  


How to use it with Everlasting Summer
-------------------------------------

1. Put this file into your `/game/` directory.
2. Run the game.
3. Go to the mod selector in the settings.
4. Run the **Image Puller** mod.
5. Click until you reaches a menu.
6. Select characters you want and click _"Закончить выбор"_.
# 7. Select sets for the times of day you want and click "Закончить выбор".
# 8. Select a set of sprites depending on the distance between the characters and the player.
# 9. Wait...
# 10. Click on the button named "Выйти".
# 11. See /Pulled images/ directory.

What about other Ren'Py-based games?
------------------------------------

Follow the steps 1 and 2 from the instruction above. But you have to write some code yourself between them.  
Class _koz_ImagePuller_ is pretty universal (at least I hope). But it depends on you to initialize it properly for a certain game.  

I see two ways:  
- You may call the `pull()` or `pull_async()` method somewhere in the code of the game manually. This is a more reliable way.  
  `$ koz_ImagePuller().pull()`  
  or  
  `$ koz_ImagePuller().pull_async()`  
- You may try to delay the execution of the `pull_async()` method within an initialization block.  
  This way is less reliable and may not work, but easier.  
  `$ koz_ImagePuller().pull_async(delay=10)`  

If you want to pull images for only certain characters, pass a list of tags as the `only` argument.  
Another way to constrain the pulling is to use the `exclude` argument, which also gets a list of tags which must be skipped.  
There are other filters such as `has_components`, `exclude_components`, and `container_ids` as well.  
The first two ones are responsible for filtering over standard Ren'Py image modifiers.  
The last parameter lets you constrain pulling from containers up to determined list of indexes.  
