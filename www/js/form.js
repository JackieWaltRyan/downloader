var relations = {
    quality: [
        {
            cb: function cb(input) {
                var formatValue = getRadioGroupValue("format");
                if (!formatValue) return false;
                if (["2160", "1440"].includes(input.value) && formatValue !== "mkv") return false;

                return true;
            }
        }
    ],
    voice: [
        {
            cb: function cb() {
                var formatValue = getRadioGroupValue("format");
                if (!formatValue) return false;

                return true;
            }
        }
    ],
    subtitles: [
        {
            cb: function cb() {
                var formatValue = getRadioGroupValue("format");
                if (!formatValue) return false;

                return true;
            }
        }
    ],
    submit: [
        {
            cb: function cb() {
                var formatValue = getRadioGroupValue("format");
                var qualityValue = getRadioGroupValue("quality");
                var voiceValues = getCheckboxGroupValues("voice");
                var subtitlesValues = getCheckboxGroupValues("subtitles");

                if (qualityValue === "none" && voiceValues.includes("none") && subtitlesValues.includes("none")) return false;
                if (!formatValue || !qualityValue || voiceValues.length === 0 || subtitlesValues.length === 0) return false;

                return true;
            }
        }
    ]
};

function validate() {
    var relationsKeys = Object.keys(relations);
    relationsKeys.forEach(function (key) {
        var rules = relations[key];
        var inputs = document.querySelectorAll("[name=" + key + "]");
        [].slice.call(inputs).forEach(function (input) {
            input.disabled = false;

            rules.forEach(function (rule) {
                if (input.disabled) return;

                var satisfied = rule.cb(input);
                input.disabled = !satisfied;

                if (!satisfied) {
                    input.checked = false;
                }
            });
        });
    });
}

function getRadioGroupValue(name) {
    var input = document.querySelector('input[name="' + name + '"]:checked');
    return input && input.value;
}

function getCheckboxGroupValues(name) {
    var inputs = document.querySelectorAll('input[name="' + name + '"]:checked');
    return [].slice.call(inputs).map(function (input) {
        return input.value;
    });
}

function uncheckOtherInGroupOnNone(name) {
    var inputs = document.querySelectorAll('input[name="' + name + '"]:not([value="none"])');
    [].slice.call(inputs).forEach(function (input) {
        input.checked = false;
    });
}

function checkOtherInGroupOnAll(name) {
    var inputs = document.querySelectorAll('input[name="' + name + '"]:not([value="none"])');
    [].slice.call(inputs).forEach(function (input) {
        input.checked = true;
        uncheckNoneInGroup(input.name);
        uncheckNoneInGroup(input.name);
    });
}

function uncheckNoneInGroup(name) {
    var input = document.querySelector('input[name="' + name + '"][value="none"]');
    if (input) {
        input.checked = false;
    }
}

function uncheckAllInGroup(name) {
    var input = document.querySelector('input[name="' + name + '"][value="all"]');
    if (input) {
        input.checked = false;
    }
}

function bindEvents() {
    var inputs = document.querySelectorAll("input");
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
