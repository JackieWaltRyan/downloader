let relations = {
    quality: [{
        cb: function cb(input) {
            let formatValue = getRadioGroupValue("format");
            if (!formatValue) return false;
            return !(["2160", "1440"].includes(input.value) && formatValue !== "mkv");
        }
    }],
    voice: [{
        cb: function cb() {
            return getRadioGroupValue("format");
        }
    }],
    subtitles: [{
        cb: function cb() {
            return getRadioGroupValue("format");
        }
    }],
    submit: [{
        cb: function cb() {
            let formatValue = getRadioGroupValue("format");
            let qualityValue = getRadioGroupValue("quality");
            let voiceValues = getCheckboxGroupValues("voice");
            let subtitlesValues = getCheckboxGroupValues("subtitles");
            if (document.querySelectorAll('input[name="quality"]').length === 0) {
                qualityValue = "none"
            }
            if (document.querySelectorAll('input[name="voice"]').length === 0) {
                voiceValues = ["none"]
            }
            if (document.querySelectorAll('input[name="subtitles"]').length === 0) {
                subtitlesValues = ["none"]
            }
            let ponyacha = document.getElementById("ponyacha");
            if (ponyacha !== null) {
                let ponyacha_label = document.getElementById("ponyacha_label");
                if (ponyacha_label !== null) {
                    if (ponyacha_label.children.length === 0) {
                        return false;
                    }
                } else {
                    return false;
                }
            }
            if (qualityValue === "none" && voiceValues.includes("none") && subtitlesValues.includes("none")) return false;
            return !(!formatValue || !qualityValue || voiceValues.length === 0 || subtitlesValues.length === 0);
        }
    }]
};

function validate() {
    let relationsKeys = Object.keys(relations);
    relationsKeys.forEach(function (key) {
        let rules = relations[key];
        let inputs = document.querySelectorAll("[name=" + key + "]");
        [].slice.call(inputs).forEach(function (input) {
            input.disabled = false;
            rules.forEach(function (rule) {
                if (input.disabled) return;
                let satisfied = rule.cb(input);
                input.disabled = !satisfied;
                if (!satisfied) {
                    input.checked = false;
                }
            });
        });
    });
}

function getRadioGroupValue(name) {
    let input = document.querySelector('input[name="' + name + '"]:checked');
    return input && input.value;
}

function getCheckboxGroupValues(name) {
    let inputs = document.querySelectorAll('input[name="' + name + '"]:checked');
    return [].slice.call(inputs).map(function (input) {
        return input.value;
    });
}

function uncheckOtherInGroupOnNone(name) {
    let inputs = document.querySelectorAll('input[name="' + name + '"]:not([value="none"])');
    [].slice.call(inputs).forEach(function (input) {
        input.checked = false;
    });
}

function checkOtherInGroupOnAll(name) {
    let inputs = document.querySelectorAll('input[name="' + name + '"]:not([value="none"])');
    [].slice.call(inputs).forEach(function (input) {
        input.checked = true;
        uncheckNoneInGroup(input.name);
        uncheckNoneInGroup(input.name);
    });
}

function uncheckNoneInGroup(name) {
    let input = document.querySelector('input[name="' + name + '"][value="none"]');
    if (input) {
        input.checked = false;
    }
}

function uncheckAllInGroup(name) {
    let input = document.querySelector('input[name="' + name + '"][value="all"]');
    if (input) {
        input.checked = false;
    }
}

function bindEvents() {
    let inputs = document.querySelectorAll("input");
    [].slice.call(inputs).forEach(function (input) {
        input.addEventListener("change", function () {
            if (input.name) {
                if (input.value === "none") {
                    uncheckOtherInGroupOnNone(input.name);
                    uncheckOtherInGroupOnNone(input.name);
                } else {
                    if (input.value === "all") {
                        checkOtherInGroupOnAll(input.name);
                        checkOtherInGroupOnAll(input.name);
                    } else {
                        uncheckNoneInGroup(input.name);
                        uncheckNoneInGroup(input.name);
                        uncheckAllInGroup(input.name);
                        uncheckAllInGroup(input.name);
                    }
                }
            }
            validate();
        });
    });
}
