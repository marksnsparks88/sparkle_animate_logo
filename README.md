# sparkle_animate_logo

Creates an Image sequence to animate a logo.

Images can then be compiled using ffmpeg

options;

mask = logo to use
imgs = folder to store the sequence
retry = times to retry when randomly positioning nodes
spacing = minimum space between nodes
connections = numer of connection between nodes
energy = energy of the nodes
min_energy = minimum activation energy of nodes
speed = speed of spark movement
deplete_rate = depletion rate
sprk_rad_in = spark color gradient center size
sprk_rad_out = spark color gradient circumfrance size
sprk_grads = fine tune spark gradiance as a list of tuples

ffmpeg example;

$cd sequence0

$ffmpeg -framerate 23.98 -pattern_type glob -i "*.png" -vcodec h264 -r 23.98 ../example.mp4
