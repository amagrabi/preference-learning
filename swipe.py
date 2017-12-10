
import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import shutil
import sys
import time
import pandas as pd
import pynder
import urllib.request

from pynput import keyboard
from pylab import rcParams

from config import FACEBOOK_AUTH_TOKEN, FACEBOOK_ID, RATING_THRESHOLD

# Iterable needed to store ratings from keypresses
RATINGS = []

# Directory structure
DF_PATH = 'data/df_swipes.p'
IMG_PATH_LIKES = 'data/images/likes'
IMG_PATH_DISLIKES = 'data/images/dislikes'
IMG_PATH_NEARBY = 'data/images/nearby'

# Create image directories
IMG_PATHS = [IMG_PATH_LIKES, IMG_PATH_DISLIKES, IMG_PATH_NEARBY]
for path in IMG_PATHS:
    if not os.path.exists(path):
        os.makedirs(path)


def rate_photos(event):
    sys.stdout.flush()
    rating_set = [str(i) for i in list(range(1,10))]
    rating_set.append('escape')
    if event.key in rating_set:
        RATINGS.append(event.key)
        plt.close(fig)


def show_images(filenames, fig, user=None, session=None, pause=0.0,
                figure_pos_x=500, figure_pos_y=0):
    # plt.style.use('dark_background')
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
        title += f'Name: {user.name}, \n'
        title += f'Age: {user.age} \n'
        title += f'Distance: {user.distance_km} \n'
        fig.text(0.01, 0.1, f'Bio: {user.bio}', bbox={'facecolor': 'white', 'alpha': 1, 'edgecolor': 'none', 'pad': 1})
    if session:
        title += f' Likes remaining: {session.likes_remaining}'
    plt.suptitle(title)
    fig.canvas.mpl_connect('key_release_event', rate_photos)
    plt.show()
    if pause:
        time.sleep(pause)


def add_data_to_df(df, path, user, liked, rating):
    new_data = pd.DataFrame({
        'name': user.name,
        'id': user.id,
        'liked': liked,
        'rating': rating,
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
        'content_hash': user._data.get('content_hash', None),
        'datetime': datetime.datetime.isoformat(datetime.datetime.now())
    })
    df = df.append(new_data, ignore_index=True)
    df.to_pickle(path)
    return df


if __name__ == "__main__":

    reset = False
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
            rcParams['figure.figsize'] = 10, 5
            fig = plt.figure()
            show_images(photo_filenames, fig, user=user, session=session, pause=0.0)

            # Process rating
            rating = RATINGS.pop()
            if rating == 'escape':
                abort = True
                break
            elif int(rating) < RATING_THRESHOLD:
                liked = False
                df = add_data_to_df(df=df, path=DF_PATH, user=user, liked=liked, rating=int(rating))
                for photo in photo_filenames:
                    filepath, file_extension = os.path.splitext(photo)
                    new_filename = os.path.basename(filepath) + f'_{str(rating).zfill(2)}' + file_extension
                    new_filepath = os.path.join(IMG_PATH_DISLIKES, new_filename)
                    shutil.copyfile(photo, new_filepath)
                # user.dislike()
                resp = session._api.dislike(user.id)
                print(f'{user.name} was disliked ({int(rating)})')
            else:
                liked = True
                df = add_data_to_df(df=df, path=DF_PATH, user=user, liked=liked, rating=int(rating))
                for photo in photo_filenames:
                    filepath, file_extension = os.path.splitext(photo)
                    new_filename = os.path.basename(filepath) + f'_{str(rating).zfill(2)}' + file_extension
                    new_filepath = os.path.join(IMG_PATH_LIKES, new_filename)
                    shutil.copyfile(photo, new_filepath)
                # user.like()
                resp = session._api.like(user.id)
                print(f'{user.name} was LIKED ({int(rating)})')
                print(f'{resp}')

        if abort:
            break

        time.sleep(0)