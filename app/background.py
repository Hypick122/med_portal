import os
import time

import requests
import vk_api
from PIL import Image
from pony.orm import commit, db_session

from app import scheduler
from models import Tasks, Users
from .utils import captcha_handler


@scheduler.task('interval', seconds=30, coalesce=False, max_instances=1)
@db_session(optimistic=False)
def check_tasks():
    for record in Tasks.select():
        params = record.params
        changes = record.changes
        if not changes["create"]["performed"] and int(time.time()) > changes["create"]["date"]:
            changes["create"]["performed"] = True
            commit()
            time.sleep(0.1)

            try:
                g_user = Users.get(id=record.user_id)
                vk_session = vk_api.VkApi(token=g_user.token, captcha_handler=lambda captcha: captcha_handler(captcha, g_user.captcha_key))
                api = vk_session.get_api()
                api.users.get()
            except Exception as e:
                message = "Ошибка пользователя - токен недействительный" if isinstance(e, vk_api.exceptions.ApiError) and e.code == 5 else f"Ошибка пользователя - {e}"
                params["logs"].append(message)
                changes["fatal"] = True

            if params["type"] == "ad":
                for group in params["to_groups"].keys():
                    try:
                        for link in params["links"]:
                            post = api.wall.repost(group_id=int(group), object=link, message=params["text"])
                            params["posts"].append(f"-{group}_{post['post_id']}")
                            time.sleep(1)
                    except vk_api.exceptions.ApiError as e:
                        if e.code == 15:
                            params["logs"].append(f"Создание поста в {group} - доступ запрещен: невозможно опубликовать")
                    except Exception as e:
                        params["logs"].append(f"Создание поста в {group} - {e}")
            else:
                attachs = []
                if params["attachments"]:
                    attachs.extend(params["attachments"])

                path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'uploads/')
                for file in params["files"]:
                    file = path + file
                    try:
                        image = Image.open(file)

                        upload_url = api.photos.getWallUploadServer()['upload_url']
                        pfile = requests.post(upload_url, files={'photo': open(file, 'rb')}).json()
                        photo = api.photos.saveWallPhoto(server=pfile['server'], photo=pfile['photo'], hash=pfile['hash'])[0]
                        time.sleep(0.5)

                        attachs.append(f"photo{photo['owner_id']}_{photo['id']}")
                    except:
                        upload_url = api.docs.getWallUploadServer()['upload_url']
                        pfile = requests.post(upload_url, files={'file': open(file, 'rb')}).json()
                        doc = api.docs.save(file=pfile['file'])['doc']
                        time.sleep(1)

                        attachs.append(f"doc{doc['owner_id']}_{doc['id']}")

                time.sleep(1)

                for group in params["to_groups"].keys():
                    try:
                        post = api.wall.post(owner_id=-int(group), message=params["text"], copyright=params["source"], attachments=attachs)
                        params["posts"].append(f"-{group}_{post['post_id']}")
                        time.sleep(0.5)
                    except Exception as e:
                        message = f"Создание поста в {group} - доступ запрещен: невозможно опубликовать" if isinstance(e, vk_api.exceptions.ApiError) and e.code == 5 else f"Создание поста в {group} - {e}"
                        params["logs"].append(message)

            changes["create"]["is_done"] = True
            commit()

        elif changes["delete"] and not changes["delete"]["performed"] and changes["delete"]["date"] and int(time.time()) > changes["delete"]["date"]:
            changes["delete"]["performed"] = True
            commit()
            time.sleep(0.1)

            try:
                g_user = Users.get(id=record.user_id)
                vk_session = vk_api.VkApi(token=g_user.token, captcha_handler=lambda captcha: captcha_handler(captcha, g_user.captcha_key))
                api = vk_session.get_api()
            except Exception as e:
                message = "Ошибка пользователя - токен недействительный" if isinstance(e, vk_api.exceptions.ApiError) and e.code == 5 else f"Ошибка пользователя - {e}"
                params["logs"].append(message)
                changes["fatal"] = True

            for post in params["posts"]:
                try:
                    owner_id, post_id = post.split("_")
                    api.wall.delete(owner_id=owner_id, post_id=int(post_id))
                    time.sleep(0.5)
                except Exception as e:
                    params["logs"].append(f"Удаление поста {post} - {e}")

            changes["delete"]["is_done"] = True
            commit()
