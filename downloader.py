from asyncio import run, new_event_loop, run_coroutine_threadsafe
from datetime import datetime
from functools import partial
from hashlib import sha256
from json import loads, dump
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
from flask import Flask, request, send_file, redirect, url_for, render_template_string, abort, make_response
from pytz import timezone
from requests import get
from waitress import serve
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

APP, LEVELS = Flask(import_name=__name__), {"DEBUG": 0x0000FF,
                                            "INFO": 0x008000,
                                            "WARNING": 0xFFFF00,
                                            "ERROR": 0xFFA500,
                                            "CRITICAL": 0xFF0000}
APP.wsgi_app = ProxyFix(app=APP.wsgi_app)
TIME = str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13].replace(" ", "_").replace("-", "_").replace(":", "_")
ADMINS = {}
TOKENS = [sha256((x + ADMINS[x]).encode(encoding="UTF-8",
                                        errors="ignore")).hexdigest() for x in ADMINS]


async def logs(level, message, file=None):
    try:
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
            with open(file=file,
                      mode="rb") as backup_file:
                webhook.add_file(file=backup_file.read(),
                                 filename=file)

        await webhook.execute()
    except Exception:
        await logs(level="CRITICAL",
                   message=format_exc())


async def backup():
    try:
        await logs(level="INFO",
                   message=f"Бэкап БД создан успешно!",
                   file="db/settings.json")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def restart():
    try:
        try:
            execl(executable, executable, "downloader.py")
        except Exception:
            await logs(level="DEBUG",
                       message=format_exc())
            execl("python3.9", "python3.9", "downloader.py")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def delete():
    try:
        with open(file="db/settings.json",
                  mode="r",
                  encoding="UTF-8") as settings_json:
            db_settings = loads(s=settings_json.read())

            for root, dirs, files in walk(top=f"{db_settings['Временная папка']}/downloader"):
                for file in files:
                    delta = int(t_time() - getmtime(filename=join(root, file)))

                    if delta >= int(db_settings["Время хранения"]) * 60 * 60:
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

        print(f"downloader: {time}")

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


async def data_form(content, name, message=None):
    try:
        with open(file="db/settings.json",
                  mode="r",
                  encoding="UTF-8") as settings_json:
            db_settings = loads(s=settings_json.read())

            with open(file="db/users.json",
                      mode="r",
                      encoding="UTF-8") as users_json:
                db_users = loads(s=users_json.read())

                videos, dubs, subs, captcha = "", "", "", ""

                if len(content["videos"]) > 0:
                    videos = [int(x) for x in content["videos"]]
                    videos.sort()
                    videos.reverse()

                if len(content["dubs"]) > 0:
                    dubs = content["dubs"]

                if len(content["subs"]) > 0:
                    subs = content["subs"]

                if request.remote_addr in db_users:
                    if int(db_users[request.remote_addr]["Запросов"]) >= int(db_settings["Файлы каптчи"]):
                        captcha = {"files": db_settings["Файлы каптчи"],
                                   "minutes": db_settings["Время каптчи"],
                                   "message": message}

                with open(file=f"www/html/forms/form.html",
                          mode="r",
                          encoding="UTF-8") as form_html:
                    return render_template_string(source=form_html.read(),
                                                  domen=db_settings["Домен"],
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


@APP.route(rule="/<path:name>")
async def url_home(name):
    try:
        if request.method == "GET":
            with open(file="db/settings.json",
                      mode="r",
                      encoding="UTF-8") as settings_json:
                db_settings = loads(s=settings_json.read())

                with open(file="db/users.json",
                          mode="r",
                          encoding="UTF-8") as users_json:
                    db_users = loads(s=users_json.read())

                    data = loads(
                        s=get(url=f"https://bronyru.info/api/v1/episodes/name/{quote(string=name, safe='')}").text)

                    if "path" not in data:
                        return None

                    if len(request.args) == 0:
                        return await data_form(content=data,
                                               name=quote(string=name,
                                                          safe=""))
                    else:
                        if request.remote_addr not in db_users:
                            db_users.update({request.remote_addr: {"Запросов": "1",
                                                                   "Время": str(int(t_time()))}})
                        else:
                            delta = (int(t_time()) - int(db_users[request.remote_addr]["Время"]))

                            if delta < 60 * int(db_settings["Время каптчи"]):
                                old = int(db_users[request.remote_addr]["Запросов"])

                                db_users[request.remote_addr]["Запросов"] = str(old + 1)
                            else:
                                db_users[request.remote_addr] = {"Запросов": "1",
                                                                 "Время": str(int(t_time()))}

                        if "ponyacha" in request.args:
                            db_users[request.remote_addr] = {"Запросов": "0",
                                                             "Время": str(int(t_time()))}

                        with open(file="db/users.json",
                                  mode="w",
                                  encoding="UTF-8") as users_json_2:
                            dump(obj=db_users,
                                 fp=users_json_2,
                                 indent=4,
                                 ensure_ascii=False)

                        form_data, episode_id = request.args.to_dict(flat=False), 0
                        temp_path, title_en, not_found = f"{db_settings['Временная папка']}/downloader", "", []
                        user, base, files_str = f"{t_time()}_{random()}".replace(".", "_"), db_settings[
                            'Базовый путь'], ""

                        if not exists(path=f"{temp_path}/{user}"):
                            makedirs(name=f"{temp_path}/{user}")

                        for item in data["translations"]:
                            if item["locale"] == "en":
                                title_en = r_sub(pattern=r"[^\d\s\w]",
                                                 repl="",
                                                 string=item["title"]).replace("  ", " ")
                                episode_id = item["episodeId"]

                        file = f"{episode_id}. {title_en}".encode(encoding="ISO-8859-1",
                                                                  errors="ignore").decode(encoding="UTF-8",
                                                                                          errors="ignore")
                        file = file.replace("  ", " ")

                        if "quality" not in form_data:
                            form_data["quality"].append("none")

                        if form_data["quality"][0] == "none":
                            if "voice" in form_data:
                                if "all" in form_data["voice"] and "none" not in form_data["voice"]:
                                    for dubs in data["dubs"]:
                                        dubs_file = f"{base}/{data['path'][26:-1]}/{dubs['code']}.mp4"

                                        if isfile(path=dubs_file):
                                            files_str += f"{dubs_file} "
                                        else:
                                            not_found.append(f"{dubs_file}\n")

                                if "none" not in form_data["voice"] and "all" not in form_data["voice"]:
                                    for voice in form_data["voice"]:
                                        voice_file = f"{base}/{data['path'][26:-1]}/{voice}.mp4"

                                        if isfile(path=voice_file):
                                            files_str += f"{voice_file} "
                                        else:
                                            not_found.append(f"{voice_file}\n")

                            if "subtitles" in form_data:
                                if "all" in form_data["subtitles"] and "none" not in form_data["subtitles"]:
                                    for subs in data["subs"]:
                                        subs_file = f"{base}/{data['path'][26:-1]}/{subs['code']}.ass"

                                        if isfile(path=subs_file):
                                            files_str += f"{subs_file} "
                                        else:
                                            not_found.append(f"{subs_file}\n")
                                if "none" not in form_data["subtitles"] and "all" not in form_data["subtitles"]:
                                    for subtitles in form_data["subtitles"]:
                                        subtitles_file = f"{base}/{data['path'][26:-1]}/{subtitles}.ass"

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
                            format_str, voice_str, sub_str, i, map_str = "mp4", "", "", 1, ""
                            meta_str, disposition_str = "", ""

                            if form_data["quality"][0] in ["1440", "2160"]:
                                format_str = "webm"

                            video = f"{base}/{data['path'][26:-1]}/{form_data['quality'][0]}.{format_str}"

                            if not isfile(path=video):
                                not_found.append(f"{video}\n")

                            if "voice" in form_data:
                                if "all" in form_data["voice"] and "none" not in form_data["voice"]:
                                    i_2 = 0

                                    for dubs in data["dubs"]:
                                        dubs_file = f"{base}/{data['path'][26:-1]}/{dubs['code']}.mp4"

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
                                        voice_file = f"{base}/{data['path'][26:-1]}/{voice}.mp4"

                                        if isfile(path=voice_file):
                                            voice_str += f"-i {voice_file} "
                                            map_str += f"-map {i} "
                                            i += 1
                                            name_3, lang_3 = "", ""

                                            for dubs in data["dubs"]:
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

                                    for subs in data["subs"]:
                                        subs_file = f"{base}/{data['path'][26:-1]}/{subs['code']}.ass"

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
                                        subtitles_file = f"{base}/{data['path'][26:-1]}/{subtitles}.ass"

                                        if isfile(path=subtitles_file):
                                            sub_str += f"-i {subtitles_file} "
                                            map_str += f"-map {i} "
                                            i += 1
                                            name_4, lang_4 = "", ""

                                            for subs in data["subs"]:
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
        if len(request.args) == 0:
            return abort(code=500)
        else:
            return abort(code=400)


@APP.route(rule="/css/<path:file>")
async def url_css(file):
    try:
        if request.method == "GET":
            return send_file(path_or_file=f"www/css/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/fonts/<path:file>")
async def url_fonts(file):
    try:
        if request.method == "GET":
            return send_file(path_or_file=f"www/fonts/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/images/<path:file>")
async def url_images(file):
    try:
        if request.method == "GET":
            return send_file(path_or_file=f"www/images/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/js/<path:file>")
async def url_js(file):
    try:
        if request.method == "GET":
            return send_file(path_or_file=f"www/js/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/users/<user>")
async def url_users(user):
    try:
        if request.method == "GET":
            with open(file="db/settings.json",
                      mode="r",
                      encoding="UTF-8") as settings_json:
                db_settings = loads(s=settings_json.read())

                temp_path = f"{db_settings['Временная папка']}/downloader"

                if isdir(s=f"{temp_path}/{user}"):
                    files = listdir(path=f"{temp_path}/{user}")

                    if len(files) > 0 and "create.temp" not in files:
                        size = int(getsize(filename=f"{temp_path}/{user}/{files[0]}") / 1024 / 1024)

                        with open(file="www/html/users/files.html",
                                  mode="r",
                                  encoding="UTF-8") as files_html:
                            return render_template_string(source=files_html.read(),
                                                          domen=db_settings["Домен"],
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
        return abort(code=404)


@APP.route(rule="/files/<user>/<file>")
async def url_files(user, file):
    try:
        if request.method == "GET":
            with open(file="db/settings.json",
                      mode="r",
                      encoding="UTF-8") as settings_json:
                db_settings = loads(s=settings_json.read())

                temp_path, mimetype = f"{db_settings['Временная папка']}/downloader", ""

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
        return abort(code=404)


@APP.route(rule="/admin")
async def url_admin():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("downloader_token")

            if token in TOKENS:
                with open(file=f"www/html/admins/admin.html",
                          mode="r",
                          encoding="UTF-8") as admin_html:
                    return render_template_string(source=admin_html.read())
            else:
                with open(file=f"www/html/admins/login.html",
                          mode="r",
                          encoding="UTF-8") as login_html:
                    return render_template_string(source=login_html.read())
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=500)


@APP.route(rule="/api/admin/auth")
async def url_api_admin_auth():
    try:
        if request.method == "GET":
            try:
                password = sha256(request.args["password"].encode(encoding="UTF-8",
                                                                  errors="ignore")).hexdigest()
                token = sha256((request.args["login"] + password).encode(encoding="UTF-8",
                                                                         errors="ignore")).hexdigest()
            except Exception:
                raise Exception

            if token in TOKENS:
                response = make_response({"user": request.args["login"],
                                          "token": token})
                response.set_cookie("downloader_token", token)

                return response
            else:
                raise HTTPException
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=400)


@APP.route(rule="/api/admin/user")
async def url_api_admin_user():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("downloader_token")

            if token is None:
                raise HTTPException

            try:
                for admin in ADMINS:
                    if token == sha256((admin + ADMINS[admin]).encode(encoding="UTF-8",
                                                                      errors="ignore")).hexdigest():
                        return {"user": admin,
                                "token": token}
                raise Exception
            except Exception:
                raise Exception
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/api/admin/restart")
async def url_api_admin_restart():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("downloader_token")

            if token is None or token not in TOKENS:
                raise HTTPException

            try:
                await restart()

                return "1125"
            except Exception:
                raise Exception
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=500)


@APP.route(rule="/api/admin/settings")
async def url_api_admin_settings():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("downloader_token")

            if token is None or token not in TOKENS:
                raise HTTPException

            try:
                with open(file="db/settings.json",
                          mode="r",
                          encoding="UTF-8") as settings_json:
                    db = loads(s=settings_json.read())

                    return db
            except Exception:
                raise Exception
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=500)


@APP.route(rule="/api/admin/change")
async def url_api_admin_change():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("downloader_token")

            if token is None or token not in TOKENS:
                raise HTTPException

            try:
                with open(file="db/settings.json",
                          mode="r",
                          encoding="UTF-8") as settings_json:
                    db = loads(s=settings_json.read())

                    db[request.args["item"]] = request.args["value"]

                    with open(file="db/settings.json",
                              mode="w",
                              encoding="UTF-8") as settings_json_2:
                        dump(obj=db,
                             fp=settings_json_2,
                             indent=4,
                             ensure_ascii=False)
                return "1125"
            except Exception:
                raise Exception
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=400)


@APP.errorhandler(code_or_exception=HTTPException)
async def error_handler(error):
    try:
        print(error)

        with open(file=f"www/html/services/error.html",
                  mode="r",
                  encoding="UTF-8") as error_html:
            return render_template_string(source=error_html.read(),
                                          name=error.name,
                                          code=error.code), error.code
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


if __name__ == "__main__":
    try:
        with open(file="db/settings.json",
                  mode="r",
                  encoding="UTF-8") as SETTINGS_JSON:
            DB_SETTINGS = loads(s=SETTINGS_JSON.read())

            run(main=autores())

            serve(app=APP,
                  port=int(DB_SETTINGS["Порт"]),
                  threads=16)
    except Exception:
        run(main=logs(level="ERROR",
                      message=format_exc()))
