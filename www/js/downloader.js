let tooltips = {
    "tooltip_1": "Формат файла в котором он будет сохранен. В файле MP4 недоступны кодеки VP9 и ASS (качество будет не выше чем 1080p и субтитры будут не цветными). В файле MKV никаких ограничений нет.",
    "tooltip_2": "Разрешение видео, которое будет сохранено в файле. Если вы выбрали формат MP4, то выбрать качество выше 1080 вы не сможете. Одновременно можно выбрать только одно качество. Если выбрать вариант 'Без видео' то выбранные озвучки и/или субтитры будут сохранены в ZIP архиве.",
    "tooltip_3": "Звуковые дорожки, которые будут сохранены в файле. Выбрать можно любое количество. По умолчанию в итоговом видео будет установлена только первая дорожка. Если выбрать вариант 'Без озвучек' то видео будет абсолютно без звука.",
    "tooltip_4": "Субтитры (если такие имеются в этом эпизоде), которые будут сохранены в файле. Выбрать можно любое количество. По умолчанию все субтитры отключены в итоговом видео, их нужно включать в ручную. Если выбрать вариант 'Без субтитров' то в видео не будет никаких субтитров.",
    "tooltip_5": "Для сборки файла обязательно нужно пройти каптчу. Каптча появляется если вы собрали больше files файлов за minutes минут.",
    "tooltip_6": "Для сборки файла обязательно нужно выбрать формат файла, и хотя бы один пункт в каждой категории. Если в категории нет нужных вам пунктов, выберите вариант 'Без ...'. Выбрать варианты 'Без ...' во всех категориях сразу тоже нельзя."
}

let temp = null;

function page_load() {
    document.getElementsByTagName("body")[0].addEventListener("contextmenu", () => {
        return false;
    });

    let button = document.getElementById("button");

    if (button !== null) {
        button.addEventListener("click", () => {
            history.back();
            return false;
        });
    }
}

function form_load() {
    page_load();

    let img_list = document.getElementsByTagName("img");

    for (let item in img_list) {
        if ((img_list[item].attributes !== undefined) && (img_list[item].attributes["tooltip"] !== undefined)) {
            let tooltip_div = document.getElementById(img_list[item].attributes["tooltip"].value);
            let data = tooltips[img_list[item].attributes["tooltip"].value];

            if (img_list[item].attributes["tooltip"].value === "tooltip_5") {
                data = tooltips[img_list[item].attributes["tooltip"].value].replace("files", img_list[item].attributes["files"].value).replace("minutes", img_list[item].attributes["minutes"].value);
            }

            tooltip_div.setAttribute("data-tooltip", data);

            img_list[item].addEventListener("mouseover", () => {
                tooltip_div.style.display = "block";
            });

            img_list[item].addEventListener("mouseout", () => {
                tooltip_div.style.display = "none";
            });
        }
    }
}

function admin_login() {
    let alert = document.getElementById("alert");
    let xhr = new XMLHttpRequest();

    xhr.open("GET", ("/api/admin/auth?login=" + encodeURIComponent(document.getElementById("login").value) + "&password=" + encodeURIComponent(document.getElementById("password").value)), true);

    xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
            location.href = "/admin";
        } else if (xhr.status === 401) {
            alert.innerText = "Значение \"Логин\" или \"Пароль\" неверные!";
        } else {
            alert.innerText = "Во время обработки запроса возникла ошибка!";
        }
    });

    xhr.addEventListener("error", () => {
        alert.innerText = "Во время обработки запроса возникла ошибка!";
    });

    xhr.send();
}

function admin_load() {
    let xhr = new XMLHttpRequest();

    xhr.open("GET", ("/api/admin/user"), true);

    xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
            let data = JSON.parse(xhr.responseText);

            document.getElementById("user").innerText += (" " + data["user"]);

            document.getElementById("token").addEventListener("click", () => {
                if (isSecureContext && navigator.clipboard) {
                    navigator.clipboard.writeText(data["token"]).then(r => r);
                } else {
                    let input = document.createElement("input");
                    document.getElementById("token").appendChild(input);
                    input.value = data["token"];
                    input.select();
                    document.execCommand("copy");
                    input.remove();
                }
            });

            document.getElementById("restart").addEventListener("click", () => {
                if (confirm("Вы действительно хотите перезагрузить сервер?\n\nСервер перезагрузится без какого либо ответа.\n\nПосле подтверждения вам нужно будет вручную перезагрузить страницу через несколько секунд.\n\nВнимание: Если в коде сервера имеются ошибки, сервер может не запустится после перезагрузки!")) {
                    let xhr = new XMLHttpRequest();

                    xhr.open("GET", ("/api/admin/restart"), true);
                    xhr.send();

                    location.reload();
                }
            });
        }
    });

    xhr.addEventListener("error", () => {
        alert("Во время обработки запроса возникла ошибка!");
    });

    xhr.send();

    document.getElementById("logout").addEventListener("click", () => {
        document.cookie = "downloader_token=null; max-age=0";
        location.reload();
    });

    admin_generate("settings");

    temp = document.getElementById("select").innerHTML;

    document.getElementById("select").addEventListener("change", () => {
        document.getElementById("form_value_1").style.display = "block";
        document.getElementById("form_value_1_name").innerText = "Значение:";

        document.getElementById("form_submit_input").style.display = "block";

        document.getElementById("form_value_1_input").value = "";

        let allowedStates = ["Время каптчи", "Время хранения", "Порт", "Файлы каптчи"];

        if (allowedStates.includes(document.getElementById("select").value)) {
            document.getElementById("form_value_1_input").type = "number";
        } else {
            document.getElementById("form_value_1_input").type = "text";
        }
    });
}

function admin_manage() {
    let xhr = new XMLHttpRequest();

    xhr.open("GET", ("/api/admin/change?item=" + encodeURIComponent(document.getElementById("select").value) + "&value=" + encodeURIComponent(document.getElementById("form_value_1_input").value)), true);

    xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
            admin_generate("settings");

            document.getElementById("form_value_1").style.display = "none";
            document.getElementById("form_submit_input").style.display = "none";

            document.getElementById("select_none").selected = true;
        } else {
            alert("Во время обработки запроса возникла ошибка!");
        }
    });

    xhr.addEventListener("error", () => {
        alert("Во время обработки запроса возникла ошибка!");
    });

    xhr.send();
}

function admin_generate(value, trigger = true) {
    let title = {
        "settings": "Настройки"
    }

    let block = document.getElementById(value);
    block.innerHTML = "";

    let h3 = document.createElement("h3");
    h3.innerText = title[value] + ":";
    h3.addEventListener("click", () => {
        admin_generate(value, !trigger);
    });
    block.appendChild(h3);

    if (trigger) {
        let xhr = new XMLHttpRequest();

        xhr.open("GET", ("/api/admin/" + value), true);

        xhr.addEventListener("load", () => {
            if (xhr.status === 200) {
                let data = JSON.parse(xhr.responseText);

                block.appendChild(document.createElement("hr"));

                let root = document.createElement("div");
                root.classList.add("settings_data");
                block.appendChild(root);

                let old = document.getElementById("select").value;

                if (temp !== null) {
                    document.getElementById("select").innerHTML = temp;
                }

                for (let item in data) {
                    let div = document.createElement("div");
                    div.classList.add("settings_data_item");
                    root.appendChild(div);

                    let start = document.createElement("div");
                    start.innerText = item + ": " + data[item];
                    div.appendChild(start);

                    let option = document.createElement("option");
                    option.value = item;
                    option.innerText = item;

                    document.getElementById("select").appendChild(option);
                }

                document.querySelector("option[value='" + old + "']").selected = true;
            } else {
                block.innerText = "Во время обработки запроса возникла ошибка!";
            }
        });

        xhr.addEventListener("error", () => {
            block.innerText = "Во время обработки запроса возникла ошибка!";
        });

        xhr.send();
    }
}
