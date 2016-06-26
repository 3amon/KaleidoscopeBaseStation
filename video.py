from config import config
from omxplayer import OMXPlayer
import gevent
"""This is a video player strategy object that will play specific videos
when a certain number of puzzles are completed. It will always choose
the video with the highest threshold that a user is able to view.
This strategy will not attempt to show a user a video they have not seen."""

def choose_video(player):
    puzzle_count = player.get_puzzle_count()
    print "Puzzle Count:", puzzle_count
    threshold = -1
    user_video = None

    # Note: We are assuming there is video with threshold 0 somewhere
    # and that each video will have a unique threshold
    for video in config["videos"]:
        if video["threshold"] <= puzzle_count and video["threshold"] > threshold:
            threshold = video["threshold"]
            user_video = video

    return user_video

def play_video(path):
    player = OMXPlayer(path)
    player.play()
    # Wait for the player to start
    while not player.is_playing():
        gevent.sleep(1)

    # Wait for the movie to end
    while player.is_playing():
        gevent.sleep(1)

    player.quit()