from asyncio import run, sleep, new_event_loop, run_coroutine_threadsafe
from datetime import datetime
from functools import partial
from hashlib import sha256
from json import loads
from os import makedirs, walk, remove, execl, rmdir, getpid, listdir
from os.path import exists, join, isfile, isdir, getsize, getmtime
from random import random
from re import sub as r_sub
from subprocess import run as s_run
from sys import executable
from threading import Timer, Thread
from time import time as t_time
from traceback import format_exc
from urllib.parse import quote

from discord_webhook import AsyncDiscordWebhook, DiscordEmbed
from flask import Flask, request, send_file, redirect, url_for, render_template_string, session
from psutil import cpu_percent, virtual_memory, disk_partitions, disk_usage
from pytz import timezone
from requests import get
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix

APP, LEVELS, TRIGGER = Flask(import_name=__name__), {"DEBUG": 0x0000FF,
                                                     "INFO": 0x008000,
                                                     "WARNING": 0xFFFF00,
                                                     "ERROR": 0xFFA500,
                                                     "CRITICAL": 0xFF0000}, {"Сохранение": False}
APP.secret_key = b""
APP.wsgi_app = ProxyFix(app=APP.wsgi_app)  # type: ignore
TIME = str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13].replace(" ", "_").replace("-", "_").replace(":", "_")
ADMINS = {"JackieRyan": ""}


async def logs(level, message, file=None):
    try:
        if level == "DEBUG":
            from db.settings import settings
            if not settings["Дебаг"]:
                return None
        print(f"{datetime.now(tz=timezone(zone='Europe/Moscow'))} {level}:\n{message}\n\n")
        if not exists(path="temp/logs"):
            makedirs(name="temp/logs")
        with open(file=f"temp/logs/{TIME}.log",
                  mode="a+",
                  encoding="UTF-8") as log_file:
            log_file.write(f"{datetime.now(tz=timezone(zone='Europe/Moscow'))} {level}:\n{message}\n\n")
        webhook = AsyncDiscordWebhook(username="Магия Дружбы",
                                      avatar_url="https://cdn.discordapp.com/attachments/1021085537802649661/"
                                                 "1051579517564616815/bronyru.png",
                                      url="")
        if len(message) <= 4096:
            webhook.add_embed(embed=DiscordEmbed(title=level,
                                                 description=message,
                                                 color=LEVELS[level]))
        else:
            webhook.add_file(file=message.encode(encoding="UTF-8",
                                                 errors="ignore"),
                             filename=f"{level}.log")
        if file is not None:
            with open(file=f"temp/db/{file}",
                      mode="rb") as backup_file:
                webhook.add_file(file=backup_file.read(),
                                 filename=file)
        await webhook.execute()
    except Exception:
        await logs(level="CRITICAL",
                   message=format_exc())


async def save(file, content):
    try:
        while True:
            if not TRIGGER["Сохранение"]:
                TRIGGER["Сохранение"] = True
                if not exists(path="db"):
                    makedirs(name="db")
                if file in ["users"]:
                    with open(file=f"db/{file}.py",
                              mode="w",
                              encoding="UTF-8") as db_py:
                        db_py.write(f"import datetime\n\n{file} = {content}\n")
                else:
                    with open(file=f"db/{file}.py",
                              mode="w",
                              encoding="UTF-8") as db_py:
                        db_py.write(f"{file} = {content}\n")
                TRIGGER["Сохранение"] = False
                break
            else:
                print("Идет сохранение...")
                await sleep(delay=1)
    except Exception:
        TRIGGER["Сохранение"] = False
        await logs(level="ERROR",
                   message=format_exc())


async def backup():
    try:
        date = str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13]
        time = date.replace(" ", "_").replace("-", "_").replace(":", "_")
        if not exists(path="temp/db"):
            makedirs(name="temp/db")
        result = s_run(args=f"zip -9 -r temp/db/bronyru_{time}.zip db",
                       shell=True,
                       capture_output=True,
                       text=True,
                       encoding="UTF-8",
                       errors="ignore")
        try:
            result.check_returncode()
        except Exception:
            raise Exception(result.stderr)
        await logs(level="INFO",
                   message=f"Бэкап БД создан успешно!",
                   file=f"bronyru_{time}.zip")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def restart():
    try:
        try:
            execl(executable, executable, "bronyru.py")
        except Exception:
            await logs(level="DEBUG",
                       message=format_exc())
            execl("python3.9", "python3.9", "bronyru.py")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def delete():
    try:
        for root, dirs, files in walk(top=f"{settings['Временная папка']}/bronyru"):
            for file in files:
                delta = int(t_time() - getmtime(filename=join(root, file)))
                if delta >= int(settings["Время хранения"]) * 60 * 60:
                    try:
                        remove(path=join(root, file))
                    except Exception:
                        await logs(level="DEBUG",
                                   message=format_exc())
            for folder in dirs:
                if len(listdir(path=join(root, folder))) == 0:
                    rmdir(path=join(root, folder))
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def autores():
    try:
        time = int(datetime.now(tz=timezone(zone="Europe/Moscow")).strftime("%H%M%S"))
        print(f"bronyru: {time}")
        if time == 0 or time == 120000:
            await backup()
            await delete()
        try:
            if len(listdir(path=f"/proc/{getpid()}/fd")) > 1000:
                await restart()
        except Exception:
            await logs(level="DEBUG",
                       message=format_exc())
        Timer(interval=1,
              function=partial(run, main=autores())).start()
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def data_form(content, name, mobile, message=None):
    try:
        from db.settings import settings
        from db.users import users
        videos, dubs, subs, captcha = "", "", "", ""
        if len(content["videos"]) > 0:
            videos = [int(x) for x in content["videos"]]
            videos.sort()
            videos.reverse()
        if len(content["dubs"]) > 0:
            dubs = content["dubs"]
        if len(content["subs"]) > 0:
            subs = content["subs"]
        if request.remote_addr in users:
            if users[request.remote_addr]["Запросов"] >= int(settings["Файлы каптчи"]):
                captcha = {"files": settings["Файлы каптчи"],
                           "minutes": settings["Время каптчи"],
                           "message": message}
        with open(file=f"www/html/forms/form.html",
                  mode="r",
                  encoding="UTF-8") as form_html:
            with open(file=f"www/html/forms/mobile/form.html",
                      mode="r",
                      encoding="UTF-8") as mobile_form_html:
                return render_template_string(source=mobile_form_html.read() if mobile else form_html.read(),
                                              domen=settings["Домен"],
                                              name=name,
                                              videos=videos,
                                              dubs=dubs,
                                              subs=subs,
                                              captcha=captcha)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def create_zip(files_str, ttt, tt):
    try:
        from db.settings import settings
        result = s_run(args=f"zip -9 -j '{ttt}.zip' {files_str}",
                       shell=True,
                       capture_output=True,
                       text=True,
                       encoding="UTF-8",
                       errors="ignore")
        try:
            result.check_returncode()
        except Exception:
            raise Exception(result.stderr)
        if not isfile(path=f"{ttt}.zip"):
            raise Exception(result.args, result.stderr)
        if isfile(path=f"{tt}/create.temp"):
            remove(path=f"{tt}/create.temp")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def create_mkv(video, voice_str, sub_str, map_str, meta_str, ttt, tt):
    try:
        from db.settings import settings
        result = s_run(args=f"bin/ffmpeg/ffmpeg -i {video} {voice_str} {sub_str} -map 0 {map_str} -c:v copy -c:a copy "
                            f"-c:s copy {meta_str} -dn -default_mode infer_no_subs -y '{ttt}.mkv'",
                       shell=True,
                       capture_output=True,
                       text=True,
                       encoding="UTF-8",
                       errors="ignore")
        try:
            result.check_returncode()
        except Exception:
            raise Exception(result.stderr)
        if not isfile(path=f"{ttt}.mkv"):
            raise Exception(result.args, result.stderr)
        if isfile(path=f"{tt}/create.temp"):
            remove(path=f"{tt}/create.temp")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def create_mp4(video, voice_str, sub_str, map_str, meta_str, disposition_str, ttt, tt):
    try:
        from db.settings import settings
        result = s_run(args=f"bin/ffmpeg/ffmpeg -i {video} {voice_str} {sub_str} -map 0 {map_str} -c:v copy -c:a copy "
                            f"-c:s mov_text {meta_str} -disposition:v:0 default {disposition_str} -y '{ttt}.mp4'",
                       shell=True,
                       capture_output=True,
                       text=True,
                       encoding="UTF-8",
                       errors="ignore")
        try:
            result.check_returncode()
        except Exception:
            raise Exception(result.stderr)
        if not isfile(path=f"{ttt}.mp4"):
            raise Exception(result.args, result.stderr)
        if isfile(path=f"{tt}/create.temp"):
            remove(path=f"{tt}/create.temp")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def data_admin(error=None):
    try:
        if "user" in session and "token" in session:
            if session["user"] in ADMINS and session["token"] == ADMINS[session["user"]]:
                triggers_str, settings_str, users_str = "", "", ""
                triggers_rows, settings_rows, users_rows = 1, 1, 1
                triggers_cols, settings_cols, users_cols = 55, 55, 55
                for item in TRIGGER:
                    triggers_str += f"{item}: {TRIGGER[item]}\n"
                    if len(f"{item}: {TRIGGER[item]}\n") > triggers_cols:
                        triggers_cols = len(f"{item}: {TRIGGER[item]}\n") + 5
                    triggers_rows += 1
                from db.settings import settings
                for item in settings:
                    settings_str += f"{item}: {settings[item]}\n"
                    if len(f"{item}: {settings[item]}\n") > settings_cols:
                        settings_cols = len(f"{item}: {settings[item]}\n") + 5
                    settings_rows += 1
                from db.users import users
                for user in users:
                    users_str += f"{user}:\n"
                    for value in users[user]:
                        users_str += f"    {value}: {users[user][value]}\n"
                        if len(f"    {value}: {users[user][value]}\n") > users_cols:
                            users_cols = len(f"    {value}: {users[user][value]}\n") + 5
                        users_rows += 1
                    users_rows += 1
                with open(file=f"www/html/admins/admin.html",
                          mode="r",
                          encoding="UTF-8") as admin_html:
                    return render_template_string(source=admin_html.read(),
                                                  triggers_str=triggers_str,
                                                  triggers_cols=triggers_cols,
                                                  triggers_rows=triggers_rows,
                                                  settings_str=settings_str,
                                                  settings_cols=settings_cols,
                                                  settings_rows=settings_rows,
                                                  users_str=users_str,
                                                  users_cols=users_cols,
                                                  users_rows=users_rows,
                                                  error=error)
        with open(file=f"www/html/admins/login.html",
                  mode="r",
                  encoding="UTF-8") as login_html:
            return render_template_string(source=login_html.read(),
                                          error=error)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return redirect(location=url_for(endpoint="url_admin"))


@APP.route(rule="/<path:name>",
           methods=["GET", "POST"])
async def url_home(name):
    try:
        from db.settings import settings
        from db.users import users
        content = loads(s=get(url=f"https://bronyru.info/api/v1/episodes/name/{quote(string=name, safe='')}").text)
        if "path" not in content:
            return None
        if len(request.form) == 0:
            return await data_form(content=content,
                                   name=quote(string=name,
                                              safe=""),
                                   mobile=True if "mobile" in request.args else False)
        else:
            if request.remote_addr not in users:
                users.update({request.remote_addr: {"Запросов": 1,
                                                    "Время": datetime.utcnow()}})
            else:
                delta = (datetime.utcnow() - users[request.remote_addr]["Время"]).seconds
                if delta < 60 * int(settings["Время каптчи"]):
                    users[request.remote_addr]["Запросов"] += 1
                else:
                    users[request.remote_addr] = {"Запросов": 1,
                                                  "Время": datetime.utcnow()}
            await save(file="users",
                       content=users)
            if "ponyacha" in request.form:
                from db.users import users
                users[request.remote_addr] = {"Запросов": 0,
                                              "Время": datetime.utcnow()}
                await save(file="users",
                           content=users)
            form_data, episode_id, title_en, not_found, files_str = request.form.to_dict(flat=False), 0, "", [], ""
            from db.settings import settings
            temp_path, user = f"{settings['Временная папка']}/bronyru", f"{t_time()}_{random()}".replace(".", "_")
            if not exists(path=f"{temp_path}/{user}"):
                makedirs(name=f"{temp_path}/{user}")
            for item in content["translations"]:
                if item["locale"] == "en":
                    title_en = r_sub(pattern=r"[^\d\s\w]",
                                     repl="",
                                     string=item["title"]).replace("  ", " ")
                    episode_id = item["episodeId"]
            file = f"{episode_id}. {title_en}".encode(encoding="ISO-8859-1",
                                                      errors="ignore").decode(encoding="UTF-8",
                                                                              errors="ignore").replace("  ", " ")
            if "quality" not in form_data:
                form_data["quality"].append("none")
            if form_data["quality"][0] == "none":
                if "voice" in form_data:
                    if "all" in form_data["voice"] and "none" not in form_data["voice"]:
                        for dubs in content["dubs"]:
                            dubs_file = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{dubs['code']}.mp4"
                            if isfile(path=dubs_file):
                                files_str += f"{dubs_file} "
                            else:
                                not_found.append(f"{dubs_file}\n")
                    if "none" not in form_data["voice"] and "all" not in form_data["voice"]:
                        for voice in form_data["voice"]:
                            voice_file = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{voice}.mp4"
                            if isfile(path=voice_file):
                                files_str += f"{voice_file} "
                            else:
                                not_found.append(f"{voice_file}\n")
                if "subtitles" in form_data:
                    if "all" in form_data["subtitles"] and "none" not in form_data["subtitles"]:
                        for subs in content["subs"]:
                            subs_file = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{subs['code']}.ass"
                            if isfile(path=subs_file):
                                files_str += f"{subs_file} "
                            else:
                                not_found.append(f"{subs_file}\n")
                    if "none" not in form_data["subtitles"] and "all" not in form_data["subtitles"]:
                        for subtitles in form_data["subtitles"]:
                            subtitles_file = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{subtitles}.ass"
                            if isfile(path=subtitles_file):
                                files_str += f"{subtitles_file} "
                            else:
                                not_found.append(f"{subtitles_file}\n")
                if len(not_found) > 0:
                    await logs(level="ERROR",
                               message=f"Files not found: {''.join(not_found)}")
                    with open(file=f"www/html/forms/notfound.html",
                              mode="r",
                              encoding="UTF-8") as notfound_html:
                        return render_template_string(source=notfound_html.read(),
                                                      files=not_found)
                with open(file=f"{temp_path}/{user}/create.temp",
                          mode="w",
                          encoding="UTF-8") as create_temp:
                    create_temp.close()
                loop = new_event_loop()
                Thread(target=loop.run_forever).start()
                run_coroutine_threadsafe(coro=create_zip(files_str=files_str,
                                                         ttt=f"{temp_path}/{user}/{file}",
                                                         tt=f"{temp_path}/{user}"),
                                         loop=loop)
            else:
                format_str, voice_str, sub_str, i, map_str, meta_str, disposition_str = "mp4", "", "", 1, "", "", ""
                if form_data["quality"][0] in ["1440", "2160"]:
                    format_str = "webm"
                video = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{form_data['quality'][0]}.{format_str}"
                if not isfile(path=video):
                    not_found.append(f"{video}\n")
                if "voice" in form_data:
                    if "all" in form_data["voice"] and "none" not in form_data["voice"]:
                        i_2 = 0
                        for dubs in content["dubs"]:
                            dubs_file = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{dubs['code']}.mp4"
                            if isfile(path=dubs_file):
                                voice_str += f"-i {dubs_file} "
                                map_str += f"-map {i} "
                                i += 1
                                name_1 = dubs["name"].replace("\"", "")
                                lang_1 = dubs["lang"]
                                meta_str += str(f"-metadata:s:a:{i_2} title=\"{name_1}\" "
                                                f"-metadata:s:a:{i_2} description=\"{name_1}\" "
                                                f"-metadata:s:a:{i_2} language={lang_1} ")
                                if i_2 == 0:
                                    disposition_str += f"-disposition:s:{i_2} default "
                                else:
                                    disposition_str += f"-disposition:s:{i_2} 0 "
                                i_2 += 1
                            else:
                                not_found.append(f"{dubs_file}\n")
                    if "none" not in form_data["voice"] and "all" not in form_data["voice"]:
                        i_4 = 0
                        for voice in form_data["voice"]:
                            voice_file = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{voice}.mp4"
                            if isfile(path=voice_file):
                                voice_str += f"-i {voice_file} "
                                map_str += f"-map {i} "
                                i += 1
                                name_3, lang_3 = "", ""
                                for dubs in content["dubs"]:
                                    if dubs["code"] == voice:
                                        name_3 = dubs["name"].replace("\"", "")
                                        lang_3 = dubs["lang"]
                                        break
                                meta_str += str(f"-metadata:s:a:{i_4} title=\"{name_3}\" "
                                                f"-metadata:s:a:{i_4} description=\"{name_3}\" "
                                                f"-metadata:s:a:{i_4} language={lang_3} ")
                                if i_4 == 0:
                                    disposition_str += f"-disposition:s:{i_4} default "
                                else:
                                    disposition_str += f"-disposition:s:{i_4} 0 "
                                i_4 += 1
                            else:
                                not_found.append(f"{voice_file}\n")
                if "subtitles" in form_data:
                    if "all" in form_data["subtitles"] and "none" not in form_data["subtitles"]:
                        i_3 = 0
                        for subs in content["subs"]:
                            subs_file = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{subs['code']}.ass"
                            if isfile(path=subs_file):
                                sub_str += f"-i {subs_file} "
                                map_str += f"-map {i} "
                                i += 1
                                name_2 = subs["name"].replace("\"", "")
                                lang_2 = subs["lang"]
                                meta_str += str(f"-metadata:s:s:{i_3} title=\"{name_2}\" "
                                                f"-metadata:s:s:{i_3} description=\"{name_2}\" "
                                                f"-metadata:s:s:{i_3} language={lang_2} ")
                                disposition_str += f"-disposition:s:{i_3} 0 "
                                i_3 += 1
                            else:
                                not_found.append(f"{subs_file}\n")
                    if "none" not in form_data["subtitles"] and "all" not in form_data["subtitles"]:
                        i_5 = 0
                        for subtitles in form_data["subtitles"]:
                            subtitles_file = f"{settings['Базовый путь']}/{content['path'][26:-1]}/{subtitles}.ass"
                            if isfile(path=subtitles_file):
                                sub_str += f"-i {subtitles_file} "
                                map_str += f"-map {i} "
                                i += 1
                                name_4, lang_4 = "", ""
                                for subs in content["subs"]:
                                    if subs["code"] == subtitles:
                                        name_4 = subs["name"].replace("\"", "")
                                        lang_4 = subs["lang"]
                                        break
                                meta_str += str(f"-metadata:s:s:{i_5} title=\"{name_4}\" "
                                                f"-metadata:s:s:{i_5} description=\"{name_4}\" "
                                                f"-metadata:s:s:{i_5} language={lang_4} ")
                                disposition_str += f"-disposition:s:{i_5} 0 "
                                i_5 += 1
                            else:
                                not_found.append(f"{subtitles_file}\n")
                if len(not_found) > 0:
                    await logs(level="ERROR",
                               message=f"Files not found: {''.join(not_found)}")
                    with open(file=f"www/html/forms/notfound.html",
                              mode="r",
                              encoding="UTF-8") as notfound_html:
                        return render_template_string(source=notfound_html.read(),
                                                      files=not_found)
                if form_data["format"][0] == "mkv":
                    with open(file=f"{temp_path}/{user}/create.temp",
                              mode="w",
                              encoding="UTF-8") as create_temp:
                        create_temp.close()
                    loop_2 = new_event_loop()
                    Thread(target=loop_2.run_forever).start()
                    run_coroutine_threadsafe(coro=create_mkv(video=video,
                                                             voice_str=voice_str,
                                                             sub_str=sub_str,
                                                             map_str=map_str,
                                                             meta_str=meta_str,
                                                             ttt=f"{temp_path}/{user}/{file}",
                                                             tt=f"{temp_path}/{user}"),
                                             loop=loop_2)
                if form_data["format"][0] == "mp4" and form_data["quality"][0] not in ["1440", "2160"]:
                    with open(file=f"{temp_path}/{user}/create.temp",
                              mode="w",
                              encoding="UTF-8") as create_temp:
                        create_temp.close()
                    loop_3 = new_event_loop()
                    Thread(target=loop_3.run_forever).start()
                    run_coroutine_threadsafe(coro=create_mp4(video=video,
                                                             voice_str=voice_str,
                                                             sub_str=sub_str,
                                                             map_str=map_str,
                                                             meta_str=meta_str,
                                                             disposition_str=disposition_str,
                                                             ttt=f"{temp_path}/{user}/{file}",
                                                             tt=f"{temp_path}/{user}"),
                                             loop=loop_3)
            return redirect(location=url_for(endpoint="url_users",
                                             user=user))
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/css/<file>",
           methods=["GET", "POST"])
async def url_css(file):
    try:
        return send_file(path_or_file=f"www/css/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/fonts/<file>",
           methods=["GET", "POST"])
async def url_fonts(file):
    try:
        return send_file(path_or_file=f"www/fonts/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/images/<path:file>",
           methods=["GET", "POST"])
async def url_images(file):
    try:
        return send_file(path_or_file=f"www/images/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/js/<file>",
           methods=["GET", "POST"])
async def url_js(file):
    try:
        return send_file(path_or_file=f"www/js/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/users/<user>",
           methods=["GET", "POST"])
async def url_users(user):
    try:
        from db.settings import settings
        temp_path = f"{settings['Временная папка']}/bronyru"
        if isdir(s=f"{temp_path}/{user}"):
            files = listdir(path=f"{temp_path}/{user}")
            if len(files) > 0 and "create.temp" not in files:
                size = int(getsize(filename=f"{temp_path}/{user}/{files[0]}") / 1024 / 1024)
                with open(file="www/html/users/files.html",
                          mode="r",
                          encoding="UTF-8") as files_html:
                    return render_template_string(source=files_html.read(),
                                                  domen=settings["Домен"],
                                                  folder=user,
                                                  file=files[0],
                                                  size=size)
            else:
                with open(file="www/html/users/wait.html",
                          mode="r",
                          encoding="UTF-8") as wait_html:
                    return wait_html.read()
        else:
            with open(file="www/html/users/delete.html",
                      mode="r",
                      encoding="UTF-8") as delete_html:
                return delete_html.read()
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/files/<user>/<file>",
           methods=["GET", "POST"])
async def url_files(user, file):
    try:
        from db.settings import settings
        temp_path, mimetype = f"{settings['Временная папка']}/bronyru", ""
        if isdir(s=f"{temp_path}/{user}") and isfile(path=f"{temp_path}/{user}/{file}"):
            def generate():
                with open(file=f"{temp_path}/{user}/{file}",
                          mode="rb") as temp_file:
                    full_size, down_size = getsize(filename=f"{temp_path}/{user}/{file}"), 0
                    while True:
                        chunk = temp_file.read(1024 * 1024 * 10)
                        if chunk:
                            down_size += len(chunk)
                            yield chunk
                        else:
                            if down_size >= full_size:
                                remove(path=f"{temp_path}/{user}/{file}")
                                if len(listdir(path=f"{temp_path}/{user}")) == 0:
                                    rmdir(path=f"{temp_path}/{user}")
                            break

            if file.endswith(".zip"):
                mimetype = "application/zip"
            if file.endswith(".mkv"):
                mimetype = "video/x-matroska"
            if file.endswith(".mp4"):
                mimetype = "video/mp4"
            return APP.response_class(response=generate(),
                                      mimetype=mimetype,
                                      headers={"Content-Disposition": f"attachment; filename={file}"})
        else:
            with open(file=f"www/html/users/delete.html",
                      mode="r",
                      encoding="UTF-8") as delete_html:
                return delete_html.read()
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/admin",
           methods=["GET", "POST"])
async def url_admin():
    try:
        if len(request.form) == 0:
            return await data_admin()
        else:
            if "login" in request.form and "password" in request.form:
                pass_hash = sha256(request.form["password"].encode(encoding="UTF-8",
                                                                   errors="ignore")).hexdigest()
                if request.form["login"] in ADMINS and pass_hash == ADMINS[request.form["login"]]:
                    session["user"] = request.form["login"]
                    session["token"] = ADMINS[request.form["login"]]
                    session.permanent = True
                else:
                    return await data_admin(error=True)
            if "debug" in request.form and "token" in session:
                if session["token"] == ADMINS[session["user"]]:
                    from db.settings import settings
                    if settings["Дебаг"]:
                        settings["Дебаг"] = False
                    else:
                        settings["Дебаг"] = True
                    await save(file="settings",
                               content=settings)
            if "res" in request.form and "token" in session:
                if session["token"] == ADMINS[session["user"]]:
                    await restart()
            if "exit" in request.form and "token" in session:
                if session["token"] == ADMINS[session["user"]]:
                    session.clear()
            if "id" in request.form and "value" in request.form and "token" in session:
                token = ADMINS[session["user"]]
                if request.form["id"] != "" and request.form["value"] != "" and session["token"] == token:
                    if request.form["value"] not in ["Дебаг", "Дата очистки", "Дата обновления"]:
                        from db.settings import settings
                        if request.form["id"] in settings:
                            settings[request.form["id"]] = request.form["value"]
                            await save(file="settings",
                                       content=settings)
                        else:
                            return await data_admin(error=1)
                    else:
                        return await data_admin(error=2)
                else:
                    return await data_admin(error=3)
        return redirect(location=url_for(endpoint="url_admin"))
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return redirect(location=url_for(endpoint="url_admin"))


@APP.route(rule="/admin/monitor",
           methods=["GET", "POST"])
async def url_monitor():
    try:
        monitor_str, monitor_rows = f"Процессор: {cpu_percent()} %\n\n", 8
        total = str(virtual_memory().total / 1024 / 1024 / 1024).split(".")
        available = str(virtual_memory().available / 1024 / 1024 / 1024).split(".")
        monitor_str += str(f"ОЗУ:\n"
                           f"    Всего: {total[0]}.{total[1][:2]} ГБ\n"
                           f"    Свободно: {available[0]}.{available[1][:2]} ГБ\n"
                           f"    Процент: {virtual_memory().percent} %\n\n")
        for disk in disk_partitions():
            if int(disk_usage(disk.mountpoint).total / 1024 / 1024 / 1024) > 0:
                monitor_str += str(f"Диск {disk.device}:\n"
                                   f"    Всего: "
                                   f"{int(disk_usage(disk.mountpoint).total / 1024 / 1024 / 1024)} ГБ\n"
                                   f"    Использовано: "
                                   f"{int(disk_usage(disk.mountpoint).used / 1024 / 1024 / 1024)} ГБ\n"
                                   f"    Свободно: "
                                   f"{int(disk_usage(disk.mountpoint).free / 1024 / 1024 / 1024)} ГБ\n"
                                   f"    Процент: {disk_usage(disk.mountpoint).percent} %\n\n")
                monitor_rows += 6
        with open(file=f"www/html/admins/monitor.html",
                  mode="r",
                  encoding="UTF-8") as monitor_html:
            return render_template_string(source=monitor_html.read(),
                                          monitor_str=monitor_str,
                                          monitor_rows=monitor_rows,
                                          clear=True if "clear" in request.args else False)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return redirect(location=url_for(endpoint="url_monitor"))


@APP.errorhandler(code_or_exception=404)
async def error_404(error):
    try:
        print(error)
        with open(file=f"www/html/services/error.html",
                  mode="r",
                  encoding="UTF-8") as error_html:
            return error_html.read()
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.errorhandler(code_or_exception=500)
async def error_500(error):
    try:
        print(error)
        with open(file=f"www/html/services/error.html",
                  mode="r",
                  encoding="UTF-8") as error_html:
            return error_html.read()
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


if __name__ == "__main__":
    try:
        from db.settings import settings

        run(main=autores())
        serve(app=APP,
              port=int(settings["Порт"]),
              threads=16)
    except Exception:
        run(main=logs(level="ERROR",
                      message=format_exc()))
