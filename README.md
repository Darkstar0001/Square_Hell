# Canvas Hell
A simple 2D game run in the tkinter Canvas, in the vein of the "World's Hardest Game". Includes a custom level creator.

**Level Player:**  
Controls can be bound to different keys with "Customize controls"  
Default controls: WASD - move , space - start/pause , Left CTRL - Toggles slow mode (for precise movement)  
Light green tiles are checkpoints, dark green are goal tiles, smooth gold circles are coins. Collect all coins and reach the goal to win.  
Circles with uneven outlines are traps.  
Manually load a level to play using "Load Level"  

**Level Creator:**  
Create New - Create a new level from scratch  
Preload level from file - Load an existing level from a file into the editor  
Left mouse button (click/hold) - Place object(s)  
Right mouse button (click/hold) - Erase object(s)  
Trap movement offset range is -3 to 3 (left to right, top to bottom)  
Saves to "My Saved Levels.csv"
