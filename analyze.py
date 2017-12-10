
import keras
import pandas as pd
import pynder

from config import FACEBOOK_AUTH_TOKEN, FACEBOOK_ID, RATING_THRESHOLD

session = pynder.Session(FACEBOOK_AUTH_TOKEN)

# Get matches
matches = []
names = []
ids = []
ages = []
bios = []
photos = []
instagram_photos = []
common_friend_count = []
common_likes = []
common_like_count = []
jobs = []
schools = []
messages = []
message_count = []

for i, match in enumerate(session.matches()):
    print(i)
    try:
        matches.append(match)
        names.append(match.user.name)
        ids.append(match.user.id)
        ages.append(match.user.age)
        bios.append(match.user.bio)
        photos.append(match.user.get_photos())
        instagram_photos.append(match.user.instagram_photos)
        common_likes.append(match.user.common_likes)
        jobs.append(match.user.jobs)
        schools.append(match.user.schools)
        common_friend_count.append(match.user._data['common_friend_count'])
        common_like_count.append(match.user._data['common_like_count'])
        messages.append(match.messages)
        message_count.append(len(match.messages))
    except Exception as e:
        print(f'Skipping match {i}: {e}')

instagram_photos_new = []
for user_instagram_photos in instagram_photos:
    if user_instagram_photos:
        instagram_photos_new.append(list(set([d.get('image', None) for d in user_instagram_photos])))
    else:
        instagram_photos_new.append([])
instagram_photos = instagram_photos_new

# Create DataFrame from matches
df = pd.DataFrame({
    'name': names,
    'id': ids,
    'age': ages,
    'bio': bios,
    'photos': photos,
    'instagram_photos': instagram_photos,
    'common_likes': common_likes,
    'jobs': jobs,
    'schools': schools,
    'common_friend_count': common_friend_count,
    'common_like_count': common_like_count,
    'messages': messages,
})
df.to_pickle('data/df.p')


# Download image urls
import os
import urllib.request

# Tinder photos
IMG_PATH = 'data/images/matches'
if not os.path.exists(IMG_PATH):
    os.makedirs(IMG_PATH)

for i, row in df.iterrows():
    for j, photo in enumerate(row['photos']):
        urllib.request.urlretrieve(photo, os.path.join(IMG_PATH, f'match_{str(i).zfill(4)}_{str(j).zfill(4)}.jpg'))
        if j > 30:
            break

# Instagram photos
IMG_PATH_INST = 'data/images/matches_instagram'
if not os.path.exists(IMG_PATH):
    os.makedirs(IMG_PATH)

for i, row in df.iterrows():
    for j, photo in enumerate(row['instagram_photos']):
        urllib.request.urlretrieve(photo,
                                   os.path.join(IMG_PATH_INST, f'match_{str(i).zfill(4)}_{str(j).zfill(4)}.jpg'))
        if j > 30:
            break


# Get nearby users
# TODO: make script to display images and swipe with keyboard
IMG_PATH_NEARBY = 'data/images/nearby_users'
if not os.path.exists(IMG_PATH):
    os.makedirs(IMG_PATH)

nearby = []
batch_nr = 2
for i, user in enumerate(session.nearby_users()):
    print(f'Current user: {i}')
    nearby.append(user)
    photo_filenames = []
    for j, photo in enumerate(user.get_photos()):
        photo_filename = os.path.join(IMG_PATH_NEARBY, f'nearby_'
                                                       f'batch{str(batch_nr).zfill(4)}_'
                                                       f'user{str(i+20).zfill(4)}_'
                                                       f'photo{str(j).zfill(4)}.jpg')
        urllib.request.urlretrieve(photo, photo_filename)
        photo_filenames.append(photo_filename)

    if i > 100:
        break

