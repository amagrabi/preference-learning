
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import shutil
import time
import pandas as pd
import pynder
import urllib.request

from pynput import keyboard
from pylab import rcParams

from config import FACEBOOK_AUTH_TOKEN, FACEBOOK_ID, RATING_THRESHOLD

DF_PATH = 'data/df_swipes.p'

IMG_PATH_LIKES = 'data/images/likes'
IMG_PATH_DISLIKES = 'data/images/dislikes'
IMG_PATH_NEARBY = 'data/images/nearby'

# Create image directories
IMG_PATHS = [IMG_PATH_LIKES, IMG_PATH_DISLIKES, IMG_PATH_NEARBY]
for path in IMG_PATHS:
    if not os.path.exists(path):
        os.makedirs(path)


class ExceptionUserLiked(Exception):
    pass


class ExceptionUserDisliked(Exception):
    pass


class ExceptionStop(Exception):
    pass


def on_release(key):
    if key == keyboard.Key.cmd_l:
        raise ExceptionUserDisliked(key)
    if key == keyboard.Key.cmd_r:
        raise ExceptionUserLiked(key)
    if key == keyboard.Key.shift:
        raise ExceptionStop(key)
    else:
        print(f'Pressed undefined key: {key}')


def show_images(filenames, user=None, session=None, pause=3.0,
                figure_width=10, figure_height=5, figure_pos_x=500, figure_pos_y=0):
    # plt.style.use('dark_background')
    rcParams['figure.figsize'] = figure_width, figure_height
    fig = plt.figure()
    thismanager = plt.get_current_fig_manager()
    thismanager.window.wm_geometry(f'+{figure_pos_x}+{figure_pos_y}')
    for j, photo in enumerate(filenames):
        a = fig.add_subplot(1, len(filenames), j + 1)
        a.axis('off')
        a.set_facecolor('black')
        img = mpimg.imread(filenames[j])
        plt.imshow(img)
    title = ''
    if user:
        title += f' Name: {user.name},   '
        title += f' Age: {user.age} \n'
        title += f' Bio: {user.bio} \n'
    if session:
        title += f' Likes remaining: {session.likes_remaining}'
    plt.suptitle(title)
    plt.draw()
    # Not sure why this pause is necessary/why the figure doesn't close directly after the pause
    plt.pause(pause)
    plt.close(fig)


def add_data_to_df(df, path, user, liked):
    new_data = pd.DataFrame({
        'name': user.name,
        'id': user.id,
        'liked': liked,
        'age': user.age,
        'bio': user.bio,
        'photos': [list(user.get_photos())],
        'photos_instagram': [user.instagram_photos],
        'common_likes': [user.common_likes],
        'common_like_count': len(user.common_likes),
        'common_interests': [user._data.get('common_interests', [])],
        'common_interests_count': len(user._data.get('common_interests', [])),
        'common_friends': [user._data.get('common_friends', [])],
        'common_friend_count': len(user._data.get('common_friends', [])),
        'connection_count': [user.common_connections],
        'jobs': [user.jobs],
        'schools': [user.schools],
        'distance_km': user.distance_km,
        'distance_mi': user.distance_mi,
        'ping_time': user._data['ping_time'],
        'teasers': [user._data['teasers']],
        'gender': user.gender,
        'birth_date': user.birth_date,
        'instagram_name': user.instagram_username,
        'content_hash': user._data.get('content_hash', None)
    })
    df = df.append(new_data, ignore_index=True)
    df.to_pickle(path)
    return df


if __name__ == "__main__":

    reset = True
    if reset:
        if os.path.exists(IMG_PATH_LIKES):
            shutil.rmtree(IMG_PATH_LIKES)
            os.makedirs(IMG_PATH_LIKES)
        if os.path.exists(IMG_PATH_DISLIKES):
            shutil.rmtree(IMG_PATH_DISLIKES)
            os.makedirs(IMG_PATH_DISLIKES)
        if os.path.exists(IMG_PATH_NEARBY):
            shutil.rmtree(IMG_PATH_NEARBY)
            os.makedirs(IMG_PATH_NEARBY)
        if os.path.exists(DF_PATH):
            os.remove(DF_PATH)

    # Load DataFrame
    if os.path.exists(DF_PATH):
        df = pd.read_pickle(DF_PATH)
    else:
        # columns = [
        #     'name', 'id', 'liked', 'age', 'bio', 'photos', 'photos_instagram',
        #     'common_likes', 'common_like_count', 'common_friends_count', 'common_friends_count',
        #     'jobs', 'schools', 'distance_km', 'distance_mi',
        #     'ping_time', 'teasers', 'gender', 'birth_date'
        # ]
        df = pd.DataFrame()

    session = pynder.Session(FACEBOOK_AUTH_TOKEN)

    # Get nearby users
    liked = False
    abort = False

    while True:

        print(f'Starting session...')
        print(f'Likes remaining: {session.likes_remaining}')
        print(f'Super likes remaining: {session.super_likes_remaining}')

        for i, user in enumerate(session.nearby_users(limit=1)):

            # print(f'User {i}: {user.name}')

            # Download user photos to nearby folder
            photo_filenames = []
            for j, photo in enumerate(user.photos):
                photo_filename = os.path.join(IMG_PATH_NEARBY, f'{user.id}_{str(j).zfill(4)}.jpg')
                urllib.request.urlretrieve(photo, photo_filename)
                photo_filenames.append(photo_filename)

            # Show images
            show_images(photo_filenames, user=user, session=session, pause=0.1)

            # Wait for response
            with keyboard.Listener(on_release=on_release) as listener:

                try:
                    listener.join()

                except ExceptionUserDisliked as e:
                    liked = False
                    df = add_data_to_df(df=df, path=DF_PATH, user=user, liked=liked)
                    for photo in photo_filenames:
                        shutil.copyfile(photo, os.path.join(IMG_PATH_DISLIKES, os.path.basename(photo)))
                    # user.dislike()
                    resp = session._api.dislike(user.id)
                    print(f'{user.name} was disliked')

                except ExceptionUserLiked as e:
                    liked = True
                    df = add_data_to_df(df=df, path=DF_PATH, user=user, liked=liked)
                    for photo in photo_filenames:
                        shutil.copyfile(photo, os.path.join(IMG_PATH_LIKES, os.path.basename(photo)))
                    # user.like()
                    resp = session._api.like(user.id)
                    print(f'{user.name} was LIKED: {resp}')

                except ExceptionStop as e:
                    print('Aborting')
                    abort = True
                    break

        if abort:
            break

        time.sleep(1)