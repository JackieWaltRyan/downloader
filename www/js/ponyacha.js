let all_pony = [["Сумеречной Искоркой", "ts"], ["Эпплджек", "aj"], ["Рарити", "rr"], ["Пинки Пай", "pp"], ["Радугой Дэш", "rd"], ["Флаттершай", "fs"]]
let all_cat = ["ts", "aj", "rr", "pp", "rd", "fs", "other"]
let all_color = {"ts": "#5f0087", "aj": "#854f00", "rr": "#3e2f87", "pp": "#8b003c", "rd": "#005e8d", "fs": "#877a00"}
let chek_list = []
let select_list = []

function ponyacha_create() {
    try {
        let ponyacha = document.getElementById("ponyacha");
        ponyacha.addEventListener("contextmenu", (event) => {
            event.preventDefault();
            return false;
        });
        ponyacha.addEventListener("click", ponyacha_start);

        let ponyacha_checkbox = document.createElement("div");
        ponyacha_checkbox.id = "ponyacha_checkbox";
        ponyacha.appendChild(ponyacha_checkbox);

        let ponyacha_checkbox_filter = document.createElement("span");
        ponyacha_checkbox_filter.id = "ponyacha_checkbox_filter";
        ponyacha_checkbox.appendChild(ponyacha_checkbox_filter);

        let ponyacha_checkbox_logo = document.createElement("img");
        ponyacha_checkbox_logo.id = "ponyacha_checkbox_logo";
        ponyacha_checkbox_logo.src = "/images/ponyacha/checkbox.png";
        ponyacha_checkbox.appendChild(ponyacha_checkbox_logo);

        let ponyacha_checkbox_spinner = document.createElement("img");
        ponyacha_checkbox_spinner.id = "ponyacha_checkbox_spinner";
        ponyacha_checkbox_spinner.src = "/images/ponyacha/spinner.png";
        ponyacha_checkbox.appendChild(ponyacha_checkbox_spinner);

        let ponyacha_checkbox_check = document.createElement("img");
        ponyacha_checkbox_check.id = "ponyacha_checkbox_check";
        ponyacha_checkbox_check.src = "/images/ponyacha/checkmark.png";
        ponyacha_checkbox.appendChild(ponyacha_checkbox_check);

        let ponyacha_checkbox_text = document.createElement("div");
        ponyacha_checkbox_text.id = "ponyacha_checkbox_text";
        ponyacha_checkbox.appendChild(ponyacha_checkbox_text);

        let ponyacha_checkbox_text_pony = document.createElement("div");
        ponyacha_checkbox_text_pony.id = "ponyacha_checkbox_text_pony";
        ponyacha_checkbox_text_pony.textContent = "Я поняшка";
        ponyacha_checkbox_text.appendChild(ponyacha_checkbox_text_pony);

        let ponyacha_checkbox_text_error = document.createElement("div");
        ponyacha_checkbox_text_error.id = "ponyacha_checkbox_text_error";
        ponyacha_checkbox_text_error.textContent = "Проверка не пройдена!";
        ponyacha_checkbox_text.appendChild(ponyacha_checkbox_text_error);

        let ponyacha_logo = document.createElement("div");
        ponyacha_logo.id = "ponyacha_logo";
        ponyacha.appendChild(ponyacha_logo);

        let ponyacha_logo_icon = document.createElement("img");
        ponyacha_logo_icon.id = "ponyacha_logo_icon";
        ponyacha_logo_icon.src = "/images/ponyacha/roku_chan.png";
        ponyacha_logo.appendChild(ponyacha_logo_icon);

        let ponyacha_logo_text = document.createElement("div");
        ponyacha_logo_text.id = "ponyacha_logo_text";
        ponyacha_logo_text.textContent = "poNYACHA";
        ponyacha_logo.appendChild(ponyacha_logo_text);
    } catch {
        return false;
    }
}

function ponyacha_start() {
    try {
        let scrollWidth = Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, document.body.offsetWidth, document.documentElement.offsetWidth, document.body.clientWidth, document.documentElement.clientWidth);
        let ponyacha_box = document.getElementById("ponyacha_box");

        if (ponyacha_box === null) {
            let ponyacha_checkbox_filter = document.getElementById("ponyacha_checkbox_filter");
            ponyacha_checkbox_filter.style.display = "none";

            let ponyacha_checkbox_text_error = document.getElementById("ponyacha_checkbox_text_error");
            ponyacha_checkbox_text_error.style.display = "none";

            let ponyacha_checkbox_logo = document.getElementById("ponyacha_checkbox_logo");
            ponyacha_checkbox_logo.style.display = "none";

            let ponyacha_checkbox_text_pony = document.getElementById("ponyacha_checkbox_text_pony");
            ponyacha_checkbox_text_pony.style.display = "inline-block";

            let ponyacha_checkbox_spinner = document.getElementById("ponyacha_checkbox_spinner");
            ponyacha_checkbox_spinner.style.display = "inline-block";

            let ponyacha = document.getElementById("ponyacha");
            ponyacha.removeEventListener("click", ponyacha_start);

            let rand_pony = all_pony[Math.floor(Math.random() * all_pony.length)];

            let ponyacha_box_hide = document.createElement("div");
            ponyacha_box_hide.id = "ponyacha_box_hide";
            ponyacha_box_hide.addEventListener("click", ponyacha_hide);
            ponyacha.appendChild(ponyacha_box_hide);

            let ponyacha_box = document.createElement("div");
            ponyacha_box.id = "ponyacha_box";
            ponyacha.appendChild(ponyacha_box);

            let ponyacha_box_header = document.createElement("div");
            ponyacha_box_header.id = "ponyacha_box_header";
            ponyacha_box_header.style.backgroundColor = all_color[rand_pony[1]];
            ponyacha_box.appendChild(ponyacha_box_header);

            let ponyacha_box_header_description = document.createElement("div");
            ponyacha_box_header_description.id = "ponyacha_box_header_description";
            ponyacha_box_header_description.textContent = "Выберите все изображения с ";
            ponyacha_box_header.appendChild(ponyacha_box_header_description);

            let ponyacha_box_header_description_strong = document.createElement("strong");
            ponyacha_box_header_description_strong.id = "ponyacha_box_header_description_strong";
            ponyacha_box_header_description_strong.textContent = rand_pony[0];
            ponyacha_box_header_description.appendChild(ponyacha_box_header_description_strong);

            let ponyacha_box_header_image = document.createElement("img");
            ponyacha_box_header_image.id = "ponyacha_box_header_image";
            ponyacha_box_header_image.src = "/images/ponyacha/" + rand_pony[1] + ".png";
            ponyacha_box_header.appendChild(ponyacha_box_header_image);

            let ponyacha_box_body = document.createElement("div");
            ponyacha_box_body.id = "ponyacha_box_body";
            ponyacha_box.appendChild(ponyacha_box_body);

            let ponyacha_box_body_table = document.createElement("table");
            ponyacha_box_body_table.id = "ponyacha_box_body_table";
            ponyacha_box_body.appendChild(ponyacha_box_body_table);

            chek_list = [];
            select_list = [];

            let ponyacha_box_body_table_tbody = document.createElement("tbody");
            ponyacha_box_body_table_tbody.id = "ponyacha_box_body_table_tbody";
            ponyacha_box_body_table.appendChild(ponyacha_box_body_table_tbody);

            for (let i = 1; i < 4; i++) {
                try {
                    let tr = document.createElement("tr")

                    for (let ii = 1; ii < 4; ii++) {
                        try {
                            let ponyacha_box_body_table_td = document.createElement("td");
                            ponyacha_box_body_table_td.className = "ponyacha_box_body_table_td";
                            tr.appendChild(ponyacha_box_body_table_td);

                            let rand_cat = all_cat[Math.floor(Math.random() * all_cat.length)];
                            let rand_image = rand_cat + "_" + (Math.floor(Math.random() * 29) + 1) + ".jpg";
                            if (rand_cat === rand_pony[1]) {
                                chek_list.push(rand_image)
                            }

                            let ponyacha_box_body_table_tbody_td_image = document.createElement("img");
                            ponyacha_box_body_table_tbody_td_image.className = "ponyacha_box_body_table_tbody_td_image";
                            ponyacha_box_body_table_tbody_td_image.id = i.toString() + ii.toString() + "_&_" + rand_image;
                            ponyacha_box_body_table_tbody_td_image.src = "/images/ponyacha/" + rand_cat + "/" + rand_image;
                            ponyacha_box_body_table_tbody_td_image.addEventListener("click", (event) => ponyacha_check(event));
                            ponyacha_box_body_table_td.appendChild(ponyacha_box_body_table_tbody_td_image);

                            let ponyacha_box_body_table_tbody_td_checkbox = document.createElement("img");
                            ponyacha_box_body_table_tbody_td_checkbox.className = "ponyacha_box_body_table_tbody_td_checkbox_" + ii;
                            ponyacha_box_body_table_tbody_td_checkbox.id = "checkbox_" + i.toString() + ii.toString();
                            ponyacha_box_body_table_tbody_td_checkbox.src = "/images/ponyacha/checkmark_blue.png";
                            ponyacha_box_body_table_td.appendChild(ponyacha_box_body_table_tbody_td_checkbox);
                        } catch {
                            return false;
                        }
                    }
                    ponyacha_box_body_table_tbody.appendChild(tr);
                } catch {
                    return false;
                }
            }

            let ponyacha_box_body_error = document.createElement("div");
            ponyacha_box_body_error.id = "ponyacha_box_body_error";
            ponyacha_box_body_error.textContent = "Пожалуйста, выберите хотя бы один объект, или перезагрузите, если их нет.";
            ponyacha_box_body.appendChild(ponyacha_box_body_error);

            let ponyacha_box_footer = document.createElement("div");
            ponyacha_box_footer.id = "ponyacha_box_footer";
            ponyacha_box.appendChild(ponyacha_box_footer);

            let ponyacha_box_footer_separator = document.createElement("div");
            ponyacha_box_footer_separator.id = "ponyacha_box_footer_separator";
            ponyacha_box_footer.appendChild(ponyacha_box_footer_separator);

            let ponyacha_box_footer_reload = document.createElement("img");
            ponyacha_box_footer_reload.id = "ponyacha_box_footer_reload";
            ponyacha_box_footer_reload.src = "/images/ponyacha/refresh_2x.png";
            ponyacha_box_footer_reload.addEventListener("click", ponyacha_reload);
            ponyacha_box_footer.appendChild(ponyacha_box_footer_reload);

            let ponyacha_box_footer_confirm = document.createElement("input");
            ponyacha_box_footer_confirm.id = "ponyacha_box_footer_confirm";
            ponyacha_box_footer_confirm.type = "button";
            ponyacha_box_footer_confirm.value = "Проверить";
            ponyacha_box_footer_confirm.style.background = all_color[rand_pony[1]];
            ponyacha_box_footer_confirm.addEventListener("click", ponyacha_confirm);
            ponyacha_box_footer.appendChild(ponyacha_box_footer_confirm);

            if ((ponyacha.getBoundingClientRect().top + window.scrollY) > ponyacha_box.offsetHeight) {
                ponyacha_box.style.top = ((ponyacha.getBoundingClientRect().top + window.scrollY) - ponyacha_box.offsetHeight + 38).toString() + "px";
            } else {
                ponyacha_box.style.top = "0px";
            }

            if ((scrollWidth - (ponyacha.getBoundingClientRect().left + window.scrollX)) > ponyacha_box.offsetWidth) {
                ponyacha_box.style.left = ((ponyacha.getBoundingClientRect().left + window.scrollX) + 29).toString() + "px";
            } else {
                ponyacha_box.style.left = (scrollWidth - ponyacha_box.offsetWidth - 1).toString() + "px";
            }
        }
    } catch {
        return false;
    }
}

function ponyacha_check(event) {
    try {
        let split = event["target"]["id"].split("_&_");
        let image = document.getElementById(event["target"]["id"]);

        if (image.style.transform !== "scale(0.8)") {
            image.style.transform = "scale(0.8)";

            let checkbox = document.getElementById("checkbox_" + split[0]);
            checkbox.style.display = "inline-block";

            select_list.push(split[1]);
        } else {
            image.style.transform = "scale(1)";

            let checkbox = document.getElementById("checkbox_" + split[0]);
            checkbox.style.display = "none";

            let temp_list = [];
            let i = 1;

            for (let item in select_list) {
                try {
                    if (select_list[item] === split[1] && i === 1) {
                        i++;
                    } else {
                        temp_list.push(select_list[item]);
                    }
                } catch {
                    return false;
                }
            }

            select_list = temp_list;
        }
    } catch {
        return false;
    }
}

function ponyacha_reload() {
    try {
        let ponyacha_box = document.getElementById("ponyacha_box");
        ponyacha_box.remove();

        let ponyacha_box_hide = document.getElementById("ponyacha_box_hide");
        ponyacha_box_hide.remove();

        ponyacha_start();
    } catch {
        return false;
    }
}

function ponyacha_confirm() {
    try {
        if (select_list.length === 0) {
            let ponyacha_box_body_error = document.getElementById("ponyacha_box_body_error");
            ponyacha_box_body_error.style.display = "inline-block";
        } else {
            let ponyacha = document.getElementById("ponyacha");

            let ponyacha_checkbox_spinner = document.getElementById("ponyacha_checkbox_spinner");
            ponyacha_checkbox_spinner.style.display = "none";

            if (JSON.stringify(chek_list.sort()) === JSON.stringify(select_list.sort())) {
                let ponyacha_checkbox_check = document.getElementById("ponyacha_checkbox_check");
                ponyacha_checkbox_check.style.display = "inline-block";

                let ponyacha_checkbox_text_pony = document.getElementById("ponyacha_checkbox_text_pony");
                ponyacha_checkbox_text_pony.style.color = "green";

                let ponyacha_label = document.createElement("label");
                ponyacha_label.id = "ponyacha_label";
                ponyacha.appendChild(ponyacha_label);

                let input = document.createElement("input");
                input.name = "ponyacha";
                input.type = "hidden";
                input.value = "ponyacha";
                ponyacha_label.appendChild(input);

                validate();

                ponyacha.removeEventListener("click", ponyacha_start);
            } else {
                let ponyacha_checkbox_text_pony = document.getElementById("ponyacha_checkbox_text_pony");
                ponyacha_checkbox_text_pony.style.display = "none";

                let ponyacha_checkbox_logo = document.getElementById("ponyacha_checkbox_logo");
                ponyacha_checkbox_logo.style.display = "inline-block";

                let ponyacha_checkbox_filter = document.getElementById("ponyacha_checkbox_filter");
                ponyacha_checkbox_filter.style.display = "inline-block";

                let ponyacha_checkbox_text_error = document.getElementById("ponyacha_checkbox_text_error");
                ponyacha_checkbox_text_error.style.display = "inline-block";

                ponyacha.addEventListener("click", ponyacha_start);
            }

            setTimeout(() => {
                let ponyacha_box = document.getElementById("ponyacha_box");
                ponyacha_box.remove();

                let ponyacha_box_hide = document.getElementById("ponyacha_box_hide");
                ponyacha_box_hide.remove();
            }, 100);
        }
    } catch {
        return false;
    }
}

function ponyacha_hide() {
    try {
        let ponyacha_box = document.getElementById("ponyacha_box");
        ponyacha_box.remove();

        let ponyacha_box_hide = document.getElementById("ponyacha_box_hide");
        ponyacha_box_hide.remove();

        let ponyacha_checkbox_spinner = document.getElementById("ponyacha_checkbox_spinner");
        ponyacha_checkbox_spinner.style.display = "none";

        let ponyacha_checkbox_check = document.getElementById("ponyacha_checkbox_check");

        if (ponyacha_checkbox_check.style.display !== "inline-block") {
            let ponyacha_checkbox_logo = document.getElementById("ponyacha_checkbox_logo");
            ponyacha_checkbox_logo.style.display = "inline-block";
        }

        setTimeout(() => {
            let ponyacha = document.getElementById("ponyacha");
            ponyacha.addEventListener("click", ponyacha_start);
        }, 100);
    } catch {
        return false;
    }
}
