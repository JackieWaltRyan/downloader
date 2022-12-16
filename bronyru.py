from asyncio import run, sleep, new_event_loop, run_coroutine_threadsafe
from datetime import datetime
from hashlib import sha256
from json import loads
from os import makedirs, system, walk, remove, execl, rmdir
from os.path import exists, join, isfile, getsize
from pathlib import Path
from random import random
from re import sub
from sys import executable
from threading import Thread, Timer
from time import time as unix
from traceback import format_exc

from discord_webhook import DiscordWebhook, DiscordEmbed
from flask import Flask, request, send_file, redirect, url_for, render_template_string, session
from psutil import cpu_percent, virtual_memory, disk_partitions, disk_usage
from pytz import timezone
from requests import get
from waitress import serve

APP, TRIGGER = Flask(import_name=__name__), {"Сохранение": False, "Бэкап": False, "Очистка": False}
LEVELS = {1: {"Название": "DEBUG", "Цвет": 0x0000FF}, 2: {"Название": "INFO", "Цвет": 0x008000},
          3: {"Название": "WARNING", "Цвет": 0xFFFF00}, 4: {"Название": "ERROR", "Цвет": 0xFFA500},
          5: {"Название": "CRITICAL", "Цвет": 0xFF0000}}
TIME = str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13].replace(" ", "_").replace("-", "_").replace(":", "_")
APP.secret_key = b""
LOGIN, PASSWORD = "JackieRyan", ""


async def logs(level, message, file=None):
    try:
        if level == LEVELS[1]:
            from db.settings import settings
            if not settings["Дебаг"]:
                return None
        print(f"{datetime.now(tz=timezone(zone='Europe/Moscow'))} {level['Название']}\n{message}")
        if not exists(path="temp/logs"):
            makedirs(name="temp/logs")
        with open(file=f"temp/logs/{TIME}.log", mode="a+", encoding="UTF-8") as log_file:
            log_file.write(f"{datetime.now(tz=timezone(zone='Europe/Moscow'))} {level['Название']}:\n{message}\n\n")
        webhook = DiscordWebhook(username="Brony Ru",
                                 avatar_url="https://cdn.discordapp.com/attachments/1021085537802649661/"
                                            "1051579517564616815/bronyru.png", url="")
        webhook.add_embed(embed=DiscordEmbed(title=level["Название"], description=str(message), color=level["Цвет"]))
        if file is not None:
            with open(file=f"temp/backups/{file}", mode="rb") as backup_file:
                webhook.add_file(file=backup_file.read(), filename=file)
        webhook.execute()
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())


async def save(file, content):
    try:
        while True:
            if not TRIGGER["Сохранение"]:
                TRIGGER["Сохранение"] = True
                if not exists(path="db"):
                    makedirs(name="db")
                if file in ["settings", "users"]:
                    with open(file=f"db/{file}.py", mode="w", encoding="UTF-8") as db_file:
                        db_file.write(f"import datetime\n\n{file} = {content}\n")
                else:
                    with open(file=f"db/{file}.py", mode="w", encoding="UTF-8") as db_file:
                        db_file.write(f"{file} = {content}\n")
                TRIGGER["Сохранение"] = False
                break
            else:
                print("Идет сохранение...")
                await sleep(delay=1)
    except Exception:
        TRIGGER["Сохранение"] = False
        await logs(level=LEVELS[4], message=format_exc())


async def backup():
    try:
        from db.settings import settings
        if (datetime.utcnow() - settings["Дата обновления"]).days >= 1:
            if not TRIGGER["Бэкап"]:
                TRIGGER["Бэкап"] = True
                if not exists(path="temp/backups"):
                    makedirs(name="temp/backups")
                date = str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13]
                time = date.replace(" ", "_").replace("-", "_").replace(":", "_")
                system(command=f"zip -9 -r temp/backups/bronyru_{time}.zip db")
                settings["Дата обновления"] = datetime.utcnow()
                await save(file="settings", content=settings)
                await logs(level=LEVELS[2], message=f"Бэкап БД создан успешно!", file=f"bronyru_{time}.zip")
                TRIGGER["Бэкап"] = False
    except Exception:
        TRIGGER["Бэкап"] = False
        await logs(level=LEVELS[4], message=format_exc())


async def delete():
    try:
        timer = int(datetime.now(tz=timezone(zone="Europe/Moscow")).strftime("%H%M%S"))
        print(f"bronyru: {timer}")
        from db.settings import settings
        if (datetime.utcnow() - settings["Дата очистки"]).seconds >= 3600:
            if not TRIGGER["Очистка"]:
                TRIGGER["Очистка"] = True
                for root, dirs, filess in walk(top=f"{settings['Временная папка']}/bronyru"):
                    for file in filess:
                        if (datetime.utcnow() - datetime.fromtimestamp(Path(root, file).stat().st_mtime)).days >= 1:
                            try:
                                remove(path=join(root, file))
                            except Exception:
                                await logs(level=LEVELS[1], message=format_exc())
                    for dirr in dirs:
                        for roott, dirss, filesss in walk(top=join(root, dirr)):
                            if len(filesss) == 0:
                                rmdir(path=join(root, dirr))
                settings["Дата очистки"] = datetime.utcnow()
                await save(file="settings", content=settings)
                TRIGGER["Очистка"] = False
            await backup()
        Timer(interval=1, function=lambda: run(main=delete())).start()
    except Exception:
        TRIGGER["Очистка"] = False
        await logs(level=LEVELS[4], message=format_exc())


@APP.route(rule="/<name>", methods=["GET", "POST"])
async def home(name, captcha_mes=None):
    try:
        from db.settings import settings
        from db.users import users
        content = loads(s=get(url=f"https://xn--80acfekkz0b1a6ftb.xn--p1ai/api/v1/episodes/name/{name}").text)
        if "path" not in content:
            return None
        path, domen, captcha = content["path"][26:-1], f"{settings['Домен']}:{settings['Порт']}", ""
        if len(request.form) == 0:
            videos_str, quality_str, voice_str, subtitles_str = [int(x) for x in content["videos"]], "", "", ""
            videos_str.sort()
            videos_str.reverse()
            for q in videos_str:
                quality_str += str(f"<label class=\"radio\"><input name=\"quality\" type=\"radio\" "
                                   f"value=\"{q}\"> {q}p</label><br>\n{' ' * 28}")
            for v in content["dubs"]:
                voice_str += str(f"<label class=\"checkbox\"><input name=\"voice\" type=\"checkbox\" "
                                 f"value=\"{v['code']}\"> [{v['lang']}] {v['name']}</label><br>\n{' ' * 28}")
            for s in content["subs"]:
                subtitles_str += str(f"<label class=\"checkbox\"><input name=\"subtitles\" type=\"checkbox\" "
                                     f"value=\"{s['code']}\"> [{s['lang']}] {s['name']}</label><br>\n{' ' * 28}")
            if request.remote_addr in users:
                if users[request.remote_addr]["Запросов"] >= int(settings["Файлы каптчи"]):
                    if captcha_mes is not None:
                        captcha = str(f"<script src=\"https://www.google.com/recaptcha/api.js\"></script>\n"
                                      f"{' ' * 24}<div>{captcha_mes}</div>\n{' ' * 24}<div class=\"g-recaptcha\" "
                                      f"data-sitekey=\"6LcuV3QjAAAAAHLww7kTnzj8BCkldDkysT54xfBB\"></div>")
                    else:
                        captcha = str(f"<script src=\"https://www.google.com/recaptcha/api.js\"></script>\n"
                                      f"{' ' * 24}<div class=\"g-recaptcha\" data-sitekey=\"6LcuV3QjAAAAAHLw"
                                      f"w7kTnzj8BCkldDkysT54xfBB\"></div>")
            with open(file=f"www/html/form.html", mode="r", encoding="UTF-8") as form_html:
                return render_template_string(source=form_html.read(), domen=domen, name=name, quality=quality_str,
                                              voice=voice_str, subtitles=subtitles_str, captcha=captcha)
        else:
            if request.remote_addr not in users:
                users.update({request.remote_addr: {"Запросов": 1, "Время": datetime.utcnow()}})
            else:
                delta = (datetime.utcnow() - users[request.remote_addr]["Время"]).seconds
                if delta < 60 * int(settings["Время каптчи"]):
                    users[request.remote_addr]["Запросов"] += 1
                else:
                    users[request.remote_addr] = {"Запросов": 1, "Время": datetime.utcnow()}
            await save(file="users", content=users)
            if "g-recaptcha-response" in request.form:
                if len(request.form['g-recaptcha-response']) > 0:
                    text = loads(get(url=f"https://www.google.com/recaptcha/api/siteverify?secret="
                                         f"&response={request.form['g-recaptcha-response']}").text)
                    if text["success"]:
                        from db.users import users
                        users[request.remote_addr] = {"Запросов": 0, "Время": datetime.utcnow()}
                        await save(file="users", content=users)
                    else:
                        return redirect(location=url_for(endpoint="home", name=name,
                                                         captcha_mes="Вы не прошли проверку \"Я не робот\"!"))
                else:
                    return redirect(location=url_for(endpoint="home", name=name,
                                                     captcha_mes="Вы должны пройти проверку \"Я не робот\"!"))
            data, episode_id, title_en = request.form.to_dict(flat=False), 0, ""
            from db.settings import settings
            t_path, t_folder = f"{settings['Временная папка']}/bronyru", f"{unix()}_{random()}".replace(".", "_")
            if not exists(path=f"{t_path}/{t_folder}"):
                makedirs(name=f"{t_path}/{t_folder}")
            for item in content["translations"]:
                if item["locale"] == "en":
                    title_en = sub(pattern=r"[^\d\s\w]", repl="", string=item["title"]).replace("  ", " ")
                    episode_id = item["episodeId"]
            t_file = f"{episode_id}. {title_en}"
            if data["quality"][0] == "none":
                files_str = ""
                if "all" in data["voice"] and "none" not in data["voice"]:
                    for dubs in content["dubs"]:
                        files_str += f"{settings['Базовый путь']}/{path}/{dubs['code']}.mp4 "
                elif "all" in data["subtitles"] and "none" not in data["subtitles"]:
                    for subs in content["subs"]:
                        files_str += f"{settings['Базовый путь']}/{path}/{subs['code']}.ass "
                elif "none" not in data["voice"] and "all" not in data["voice"]:
                    for voice in data["voice"]:
                        files_str += f"{settings['Базовый путь']}/{path}/{voice}.mp4 "
                elif "none" not in data["subtitles"] and "all" not in data["subtitles"]:
                    for subtitles in data["subtitles"]:
                        files_str += f"{settings['Базовый путь']}/{path}/{subtitles}.ass "
                else:
                    raise Exception(data)

                async def zipp():
                    system(command=f"zip -9 -j '{t_path}/{t_folder}/{t_file}.zip' {files_str}")
                    if isfile(path=f"{t_path}/{t_folder}/{t_file}.zip"):
                        with open(file=f"{t_path}/{t_folder}/index.html", mode="w", encoding="UTF-8") as index_html_2:
                            with open(file=f"www/html/files.html", mode="r", encoding="UTF-8") as files_html:
                                index_html_2.write(render_template_string(
                                    source=files_html.read(), domen=domen, folder=t_folder, file=f"{t_file}.zip",
                                    size=int(getsize(filename=f"{t_path}/{t_folder}/{t_file}.zip") / 1024 / 1024)))
                    else:
                        raise Exception(f"zip -9 -j '{t_path}/{t_folder}/{t_file}.zip' {files_str}")

                new_loop = new_event_loop()
                Thread(target=new_loop.run_forever).start()
                run_coroutine_threadsafe(coro=zipp(), loop=new_loop)
            else:
                format_str, voice_str, sub_str, i, map_str, meta_str, disposition_str = "mp4", "", "", 1, "", "", ""
                if data["quality"][0] in ["1440", "2160"]:
                    format_str = "webm"
                if "all" in data["voice"] and "none" not in data["voice"]:
                    i_2 = 0
                    for dubs in content["dubs"]:
                        voice_str += f"-i {settings['Базовый путь']}/{path}/{dubs['code']}.mp4 "
                        map_str += f"-map {i} "
                        i += 1
                        name_1, lang_1 = "", ""
                        name_1 = dubs["name"].replace("\"", "")
                        lang_1 = dubs["lang"]
                        meta_str += str(f"-metadata:s:a:{i_2} handler_name=\"{name_1}\" "
                                        f"-metadata:s:a:{i_2} language={lang_1} ")
                        if i_2 == 0:
                            disposition_str += f"-disposition:s:{i_2} default "
                        else:
                            disposition_str += f"-disposition:s:{i_2} 0 "
                        i_2 += 1
                if "all" in data["subtitles"] and "none" not in data["subtitles"]:
                    i_3 = 0
                    for subs in content["subs"]:
                        sub_str += f"-i {settings['Базовый путь']}/{path}/{subs['code']}.ass "
                        map_str += f"-map {i} "
                        i += 1
                        name_2, lang_2 = "", ""
                        name_2 = subs["name"].replace("\"", "")
                        lang_2 = subs["lang"]
                        meta_str += str(f"-metadata:s:s:{i_3} handler_name=\"{name_2}\" "
                                        f"-metadata:s:s:{i_3} language={lang_2} ")
                        disposition_str += f"-disposition:s:{i_3} 0 "
                        i_3 += 1
                if "none" not in data["voice"] and "all" not in data["voice"]:
                    i_4 = 0
                    for voice in data["voice"]:
                        voice_str += f"-i {settings['Базовый путь']}/{path}/{voice}.mp4 "
                        map_str += f"-map {i} "
                        i += 1
                        name_3, lang_3 = "", ""
                        for dubs in content["dubs"]:
                            if dubs["code"] == voice:
                                name_3 = dubs["name"].replace("\"", "")
                                lang_3 = dubs["lang"]
                                break
                        meta_str += str(f"-metadata:s:a:{i_4} handler_name=\"{name_3}\" "
                                        f"-metadata:s:a:{i_4} language={lang_3} ")
                        if i_4 == 0:
                            disposition_str += f"-disposition:s:{i_4} default "
                        else:
                            disposition_str += f"-disposition:s:{i_4} 0 "
                        i_4 += 1
                if "none" not in data["subtitles"] and "all" not in data["subtitles"]:
                    i_5 = 0
                    for subtitles in data["subtitles"]:
                        sub_str += f"-i {settings['Базовый путь']}/{path}/{subtitles}.ass "
                        map_str += f"-map {i} "
                        i += 1
                        name_4, lang_4 = "", ""
                        for subs in content["subs"]:
                            if subs["code"] == subtitles:
                                name_4 = subs["name"].replace("\"", "")
                                lang_4 = subs["lang"]
                                break
                        meta_str += str(f"-metadata:s:s:{i_5} handler_name=\"{name_4}\" "
                                        f"-metadata:s:s:{i_5} language={lang_4} ")
                        disposition_str += f"-disposition:s:{i_5} 0 "
                        i_5 += 1
                if data["format"][0] == "mkv":
                    async def mkv():
                        system(command=f"bin/ffmpeg/ffmpeg -i {settings['Базовый путь']}/{path}/{data['quality'][0]}."
                                       f"{format_str} {voice_str} {sub_str} -map 0 {map_str} -c:v copy -c:a copy "
                                       f"-c:s copy {meta_str} -default_mode infer_no_subs -y '{t_path}/{t_folder}/"
                                       f"{t_file}.mkv'")
                        if isfile(path=f"{t_path}/{t_folder}/{t_file}.mkv"):
                            with open(file=f"{t_path}/{t_folder}/index.html", mode="w", encoding="UTF-8") as i_html_2:
                                with open(file=f"www/html/files.html", mode="r", encoding="UTF-8") as files_html:
                                    i_html_2.write(render_template_string(
                                        source=files_html.read(), domen=domen, folder=t_folder, file=f"{t_file}.mkv",
                                        size=int(getsize(filename=f"{t_path}/{t_folder}/{t_file}.mkv") / 1024 / 1024)))
                        else:
                            raise Exception(f"bin/ffmpeg/ffmpeg -i {settings['Базовый путь']}/{path}/"
                                            f"{data['quality'][0]}.{format_str} {voice_str} {sub_str} -map 0 "
                                            f"{map_str} -c:v copy -c:a copy -c:s copy {meta_str} -default_mode "
                                            f"infer_no_subs -y '{t_path}/{t_folder}/{t_file}.mkv'")

                    new_loop_2 = new_event_loop()
                    Thread(target=new_loop_2.run_forever).start()
                    run_coroutine_threadsafe(coro=mkv(), loop=new_loop_2)
                elif data["format"][0] == "mp4" and data["quality"][0] not in ["1440", "2160"]:
                    async def mp4():
                        system(command=f"bin/ffmpeg/ffmpeg -i {settings['Базовый путь']}/{path}/{data['quality'][0]}."
                                       f"{format_str} {voice_str} {sub_str} -map 0 {map_str} -c:v copy -c:a copy "
                                       f"-c:s mov_text {meta_str} -disposition:v:0 default {disposition_str} -y "
                                       f"'{t_path}/{t_folder}/{t_file}.mp4'")
                        if isfile(path=f"{t_path}/{t_folder}/{t_file}.mp4"):
                            with open(file=f"{t_path}/{t_folder}/index.html", mode="w", encoding="UTF-8") as i_html_2:
                                with open(file=f"www/html/files.html", mode="r", encoding="UTF-8") as files_html:
                                    i_html_2.write(render_template_string(
                                        source=files_html.read(), domen=domen, folder=t_folder, file=f"{t_file}.mp4",
                                        size=int(getsize(filename=f"{t_path}/{t_folder}/{t_file}.mp4") / 1024 / 1024)))
                        else:
                            raise Exception(f"bin/ffmpeg/ffmpeg -i {settings['Базовый путь']}/{path}/"
                                            f"{data['quality'][0]}.{format_str} {voice_str} {sub_str} -map 0 "
                                            f"{map_str} -c:v copy -c:a copy -c:s mov_text {meta_str} -y '{t_path}/"
                                            f"{t_folder}/{t_file}'.mp4")

                    new_loop_3 = new_event_loop()
                    Thread(target=new_loop_3.run_forever).start()
                    run_coroutine_threadsafe(coro=mp4(), loop=new_loop_3)
                else:
                    raise Exception(data)
            with open(file=f"{t_path}/{t_folder}/index.html", mode="w", encoding="UTF-8") as index_html:
                with open(file=f"www/html/wait.html", mode="r", encoding="UTF-8") as wait_html:
                    index_html.write(render_template_string(source=wait_html.read()))
            return redirect(location=url_for(endpoint="files", user=t_folder, file="index.html"))
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())
        with open(file=f"www/html/error.html", mode="r", encoding="UTF-8") as error_html:
            return render_template_string(source=error_html.read(),
                                          time=datetime.now(tz=timezone(zone="Europe/Moscow")))


@APP.route(rule="/css/<file>", methods=["GET", "POST"])
async def css(file):
    try:
        return send_file(path_or_file=f"www/css/{file}")
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())


@APP.route(rule="/fonts/<file>", methods=["GET", "POST"])
async def fonts(file):
    try:
        return send_file(path_or_file=f"www/fonts/{file}")
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())


@APP.route(rule="/images/<file>", methods=["GET", "POST"])
async def images(file):
    try:
        return send_file(path_or_file=f"www/images/{file}")
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())


@APP.route(rule="/js/<file>", methods=["GET", "POST"])
async def js(file):
    try:
        return send_file(path_or_file=f"www/js/{file}")
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())


@APP.route(rule="/files/<user>/<file>", methods=["GET", "POST"])
async def files(user, file):
    from db.settings import settings
    temp_path = f"{settings['Временная папка']}/bronyru"
    try:
        if file == "index.html":
            with open(file=f"{temp_path}/{user}/index.html", mode="r", encoding="UTF-8") as index_html:
                return index_html.read()
        else:
            if isfile(path=f"{temp_path}/{user}/{file}"):
                def generate():
                    with open(file=f"{temp_path}/{user}/{file}", mode="rb") as temp_file:
                        full_size, down_size = getsize(filename=f"{temp_path}/{user}/{file}"), 0
                        while True:
                            chunk = temp_file.read(1024 * 1024 * 10)
                            if chunk:
                                down_size += len(chunk)
                                yield chunk
                            else:
                                if down_size >= full_size:
                                    remove(path=f"{temp_path}/{user}/{file}")
                                break

                mimetype = ""
                if file.endswith(".zip"):
                    mimetype = "application/zip"
                if file.endswith(".mkv"):
                    mimetype = "video/x-matroska"
                if file.endswith(".mp4"):
                    mimetype = "video/mp4"
                return APP.response_class(response=generate(), mimetype=mimetype,
                                          headers={"Content-Disposition": f"attachment; filename={file}"})
            else:
                with open(file=f"www/html/delete.html", mode="r", encoding="UTF-8") as delete_html:
                    return render_template_string(source=delete_html.read())
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())
        if exists(path=f"{temp_path}/{user}/index.html"):
            return redirect(location=url_for(endpoint="files", user=user, file="index.html"))
        else:
            with open(file=f"www/html/error.html", mode="r", encoding="UTF-8") as error_html:
                return render_template_string(source=error_html.read(),
                                              time=datetime.now(tz=timezone(zone="Europe/Moscow")))


@APP.route(rule="/admin", methods=["GET", "POST"])
async def admin():
    try:
        if len(request.form) == 0:
            if "user" in session and "token" in session:
                if session["user"] == LOGIN and session["token"] == PASSWORD:
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
                    for item in users:
                        users_str += f"{item}: {users[item]}\n"
                        if len(f"{item}: {users[item]}\n") > users_cols:
                            users_cols = len(f"{item}: {users[item]}\n") + 5
                        users_rows += 1
                    with open(file=f"www/html/admin.html", mode="r", encoding="UTF-8") as admin_html:
                        return render_template_string(
                            source=admin_html.read(), triggers_str=triggers_str, triggers_cols=triggers_cols,
                            triggers_rows=triggers_rows, settings_str=settings_str, settings_cols=settings_cols,
                            settings_rows=settings_rows, users_str=users_str, users_cols=users_cols,
                            users_rows=users_rows)
            with open(file=f"www/html/login.html", mode="r", encoding="UTF-8") as login_html:
                return render_template_string(source=login_html.read())
        else:
            if "login" in request.form and "password" in request.form:
                pass_hash = sha256(request.form["password"].encode(encoding="UTF-8")).hexdigest()
                if request.form["login"] == LOGIN and pass_hash == PASSWORD:
                    session["user"] = LOGIN
                    session["token"] = PASSWORD
                    session.permanent = True
            if "debug" in request.form and "token" in session:
                if session["token"] == PASSWORD:
                    from db.settings import settings
                    if settings["Дебаг"]:
                        settings["Дебаг"] = False
                    else:
                        settings["Дебаг"] = True
                    await save(file="settings", content=settings)
            if "res" in request.form and "token" in session:
                if session["token"] == PASSWORD:
                    try:
                        execl(executable, executable, "bronyru.py")
                    except Exception:
                        await logs(level=LEVELS[1], message=format_exc())
                        execl("python3.9", "python3.9", "bronyru.py")
            if "id" in request.form and "value" in request.form and "token" in session:
                if request.form["id"] != "" and request.form["value"] != "" and session["token"] == PASSWORD:
                    if request.form["value"] not in ["Дебаг", "Дата очистки", "Дата обновления"]:
                        from db.settings import settings
                        settings[request.form["id"]] = request.form["value"]
                        await save(file="settings", content=settings)
        return redirect(location=url_for(endpoint="admin"))
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())
        return redirect(location=url_for(endpoint="admin"))


@APP.route(rule="/monitor", methods=["GET", "POST"])
async def monitor():
    try:
        monitor_str, monitor_rows = f"Процессор: {cpu_percent()} %\n\n", 8
        total = str(virtual_memory().total / 1024 / 1024 / 1024).split(".")
        available = str(virtual_memory().available / 1024 / 1024 / 1024).split(".")
        monitor_str += str(f"ОЗУ:\n"
                           f"    Всего: {total[0]}.{total[1][:2]} ГБ\n"
                           f"    Свободно: {available[0]}.{available[1][:2]} ГБ\n"
                           f"    Процент: {virtual_memory().percent} %\n\n")
        for disk in disk_partitions():
            monitor_str += str(f"Диск {disk.device}:\n"
                               f"    Всего: "
                               f"{int(disk_usage(disk.mountpoint).total / 1024 / 1024 / 1024)} ГБ\n"
                               f"    Использовано: "
                               f"{int(disk_usage(disk.mountpoint).used / 1024 / 1024 / 1024)} ГБ\n"
                               f"    Свободно: "
                               f"{int(disk_usage(disk.mountpoint).free / 1024 / 1024 / 1024)} ГБ\n"
                               f"    Процент: {disk_usage(disk.mountpoint).percent} %\n\n")
            monitor_rows += 6
        with open(file=f"www/html/monitor.html", mode="r", encoding="UTF-8") as monitor_html:
            return render_template_string(source=monitor_html.read(), monitor_str=monitor_str,
                                          monitor_rows=monitor_rows)
    except Exception:
        await logs(level=LEVELS[4], message=format_exc())
        return redirect(location=url_for(endpoint="monitor"))


if __name__ == "__main__":
    try:
        run(main=delete())
        from db.settings import settings

        serve(app=APP, port=int(settings["Порт"]))
    except Exception:
        run(main=logs(level=LEVELS[4], message=format_exc()))
