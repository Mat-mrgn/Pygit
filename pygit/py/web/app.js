/* =============================================================================
   PyGit — app.js
   -----------------------------------------------------------------------------
   Toute l'interface. Ne connaît que Bridge.call() et des objets JSON : aucune
   mention de pywebview ici, aucune règle métier non plus.

   Sommaire
     1. état et raccourcis DOM
     2. i18n : t() et applyStrings()
     3. rendu du markup rich
     4. appels moteur et signalement d'échec
     5. navigation
     6. modales et toast
     7. cycle de vie d'un job
     8. actions
     9. rendus par écran
    10. thème et accent
    11. démarrage
   ============================================================================= */

(function (global) {
    "use strict";

    /* =========================================================================
       1. ÉTAT ET RACCOURCIS DOM
       ========================================================================= */

    var POLL_MS = 250;

    var STR = {};          /* clé -> chaîne, rempli une fois par i18n.bootstrap */

    var STATE = {
        job: null,         /* {id, kind, cursor, timer} */
        askedKey: null,    /* question déjà affichée : évite de rouvrir la modale
                              à chaque tour de boucle tant que l'utilisateur
                              n'a pas répondu */
        confirmResolve: null,
        sel: { path: null, slot: null, archive: null, fromOlder: false, rule: null }
    };

    function $(sel, root) { return (root || document).querySelector(sel); }
    function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

    function field(name) { return $('[data-field="' + name + '"]'); }

    function val(name) {
        var n = field(name);
        if (!n) { return ""; }
        return n.type === "checkbox" ? n.checked : n.value;
    }

    function setVal(name, v) {
        var n = field(name);
        if (!n) { return; }
        if (n.type === "checkbox") { n.checked = !!v; }
        else { n.value = (v === null || v === undefined) ? "" : v; }
    }

    function show(node, on) { if (node) { node.hidden = !on; } }

    /* Écrire dans un nœud absent lève au milieu d'une chaîne de promesses, et
       la suite du démarrage est annulée sans message. Tous les accès directs à
       un id fixe passent donc par ces deux fonctions. */
    function text(selector, value) {
        var node = $(selector);
        if (node) { node.textContent = value; }
    }

    function width(selector, percent) {
        var node = $(selector);
        if (node) { node.style.width = percent + "%"; }
    }

    function el(tag, cls, text) {
        var n = document.createElement(tag);
        if (cls) { n.className = cls; }
        if (text !== undefined && text !== null) { n.textContent = text; }
        return n;
    }

    /* =========================================================================
       2. I18N
       lang.py fait text.format(**kwargs) et rend la chaîne brute si une clé
       manque. On reproduit exactement ça : un paramètre absent reste visible
       sous sa forme {nom} au lieu de faire disparaître la phrase.
       ========================================================================= */

    var PLACEHOLDER = /\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g;

    function t(key, params) {
        /* Seule chaine en dur du fichier, et elle ne peut pas etre autrement :
           c'est le marqueur affiche quand une cle manque, donc il doit
           fonctionner alors meme que STR est vide. Meme forme que lang.py:99
           pour qu'on reconnaisse un trou d'i18n d'un coup d'oeil. */
        var raw = Object.prototype.hasOwnProperty.call(STR, key) ? STR[key] : "[Missing: " + key + "]";
        if (!params) { return raw; }
        return raw.replace(PLACEHOLDER, function (whole, name) {
            return Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : whole;
        });
    }

    function fmtOf(node) {
        var raw = node.getAttribute("data-fmt");
        if (!raw) { return null; }
        try { return JSON.parse(raw); } catch (err) { return null; }
    }

    /* Seule fonction du fichier qui écrit du texte d'interface. Elle ne touche
       qu'aux nœuds porteurs d'un data-i18n : le contenu monté dynamiquement
       survit, à condition que les rendus posent eux aussi des data-i18n sur ce
       qu'ils créent — c'est ce qui rend le changement de langue instantané
       jusque dans les tableaux, sans rien recharger. */
    function applyStrings(root) {
        root = root || document;
        document.documentElement.setAttribute("dir",STRINGS._DIR==="rtl"?"rtl":"ltr");
        $$("[data-i18n]", root).forEach(function (n) {
            n.textContent = t(n.getAttribute("data-i18n"), fmtOf(n));
        });
        $$("[data-i18n-ph]", root).forEach(function (n) {
            n.setAttribute("placeholder", t(n.getAttribute("data-i18n-ph"), fmtOf(n)));
        });
        $$("[data-i18n-title]", root).forEach(function (n) {
            n.setAttribute("title", t(n.getAttribute("data-i18n-title"), fmtOf(n)));
        });

        if (root !== document && root.hasAttribute && root.hasAttribute("data-i18n")) {
            root.textContent = t(root.getAttribute("data-i18n"), fmtOf(root));
        }
    }

    /* Écrit une clé dans un nœud et garde le lien : au prochain changement de
       langue, applyStrings() le retrouvera tout seul. */
    function setKey(node, key, params) {
        if (!node) { return; }
        node.setAttribute("data-i18n", key);
        if (params) { node.setAttribute("data-fmt", JSON.stringify(params)); }
        else { node.removeAttribute("data-fmt"); }
        node.textContent = t(key, params);
    }

    /* =========================================================================
       3. MARKUP RICH
       Les lignes du journal viennent telles quelles du cœur, balises comprises.
       Deux précautions :
         - on échappe AVANT de convertir, donc rien venant d'un nom de fichier
           ne peut injecter de HTML ;
         - on ne convertit que des balises dont tous les mots sont connus de
           rich. Sans ça, "[Missing: dryrun_willtosave]" ou un chemin contenant
           des crochets seraient avalés silencieusement.
       ========================================================================= */

    var RICH_WORDS = {
        bold: 1, dim: 1, italic: 1, underline: 1, strike: 1, reverse: 1,
        red: 1, green: 1, yellow: 1, blue: 1, magenta: 1, cyan: 1, white: 1, black: 1,
        bright_red: 1, bright_green: 1, bright_yellow: 1, bright_blue: 1,
        bright_magenta: 1, bright_cyan: 1, bright_white: 1
    };

    var RICH_TAG = /\[(\/?)([a-z_]*(?: [a-z_]+)*)\]/g;

    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function renderRich(text) {
        return escapeHtml(text).replace(RICH_TAG, function (whole, slash, body) {
            if (body === "") {
                return slash ? "</span>" : whole;   /* [/] ferme, [] n'est rien */
            }
            var words = body.split(" ");
            for (var i = 0; i < words.length; i += 1) {
                if (RICH_WORDS[words[i]] !== 1) { return whole; }
            }
            return slash ? "</span>" : '<span class="' + words.join(" ") + '">';
        });
    }

    /* Une ligne = un <div>. Une balise non fermée par le cœur reste confinée à
       sa ligne au lieu de teindre tout le reste du journal. */
    function logLine(text) {
        var line = document.createElement("div");
        line.innerHTML = renderRich(text);
        return line;
    }

    /* =========================================================================
       4. APPELS MOTEUR
       Bridge.call ne lève jamais : tout échec arrive sous la forme
       {ok:false, reason}. Un seul endroit décide de ce qu'on en montre.
       ========================================================================= */

    function call(endpoint, payload) {
        return Bridge.call(endpoint, payload).then(function (res) {
            if (res && res.ok === false) { reportFailure(res); }
            return res;
        });
    }

    function reportFailure(res) {
        if (res.reason === "no_backend") {
            /* Page ouverte hors pywebview : silence, c'est le mode maquette. */
            return;
        }
        if (res.reason === "busy") {
            /* Un job refuse et un reglage gele ne se disent pas pareil :
               le premier est un conflit, le second une consequence. */
            var frozen = /^(config|pygnore)\./.test(String(res.endpoint || ""));
            toast(t(frozen ? "gui_busy_config" : "gui_busy"), "warn");
            return;
        }
        if (res.key) {                      /* le moteur a renvoyé une clé à lui */
            toast(t(res.key, res.params), "err");
            return;
        }
        toast(t("gui_error_generic"), "err");
    }

    /* =========================================================================
       5. NAVIGATION
       Une classe sur <body>, rien de plus : le contexte JS, la boucle de
       polling et le journal survivent au changement d'écran.
       ========================================================================= */

    function gotoView(name) {
        document.body.dataset.view = name;
        if (name === "saves") { loadSaves(); }
        if (name === "pygnore") { loadRules(); }
    }

    /* =========================================================================
       6. MODALES ET TOAST
       ========================================================================= */

    var toastTimer = null;

    function toast(message, tone) {
        var node = $("#toast");
        if (!node) { return; }
        node.textContent = message;
        if (tone) { node.dataset.tone = tone; } else { node.removeAttribute("data-tone"); }
        show(node, true);
        global.clearTimeout(toastTimer);
        toastTimer = global.setTimeout(function () { show(node, false); }, 4000);
    }

    /* Confirmation côté front, sans aller-retour Python. Renvoie une promesse
       pour que l'appelant s'écrive de haut en bas. */
    function confirmDialog(message) {
        return new Promise(function (resolve) {
            text("#confirm-body", message);
            show($("#confirm"), true);
            STATE.confirmResolve = resolve;
        });
    }

    function closeConfirm(answer) {
        show($("#confirm"), false);
        var fn = STATE.confirmResolve;
        STATE.confirmResolve = null;
        if (fn) { fn(answer); }
    }

    /* Question posée par le cœur en plein job. Le corps est
       "gui_ask_" + la clé de la question : mapping mécanique, aucune table. */
    function openAsk(question) {
        STATE.askedKey = question.key;
        text("#ask-body", t("gui_ask_" + question.key, question.params));
        show($("#ask"), true);
    }

    function answerAsk(value) {
        show($("#ask"), false);
        if (!STATE.job) { return; }
        call("job.answer", { id: STATE.job.id, value: value });
    }

    /* =========================================================================
       7. CYCLE DE VIE D'UN JOB
       ========================================================================= */

    function setBusy(on) {
        if (on) { document.body.setAttribute("data-busy", ""); }
        else { document.body.removeAttribute("data-busy"); }
        show($("#job-badge"), on);
    }

    function clearLog() {
        text("#log", "");
        setPercent(0, null);
        closeReport();
    }

    function setPercent(percent, task) {
        var pct = Math.max(0, Math.min(100, Number(percent) || 0));
        width("#job-meter", pct);
        width("#job-badge-meter", pct);

        /* Le pourcentage est celui de la TÂCHE en vol, pas du job : un save en
           produit trois. Sans le libellé à côté, la barre a l'air de reculer
           deux fois sans raison. */
        var label = t("gui_percent", { value: pct });
        if (task && task.label) {
            var name = t("gui_task_" + task.label);
            if (task.count > 1) {
                name = t("gui_task_step", { index: task.index + 1, count: task.count, label: name });
            }
            label = t("gui_task_progress", { label: name, value: pct });
        }
        text("#job-percent", label);
        text("#job-badge-label", label);
    }

    function startJob(kind, params) {
        if (STATE.job) { toast(t("gui_busy"), "warn"); return; }

        call("job.start", { kind: kind, params: params || {} }).then(function (res) {
            if (!res || res.ok === false || !res.id) { return; }
            STATE.job = { id: res.id, kind: kind, cursor: 0, timer: null };
            STATE.askedKey = null;
            setBusy(true);
            clearLog();
            poll();
        });
    }

    /* setTimeout chaîné, pas setInterval : un appel qui traîne (la fenêtre et
       le worker sont sur des threads différents) empilerait les tours et le
       curseur du journal partirait en vrille. Ici le tour suivant n'est armé
       qu'une fois le précédent revenu. */
    function poll() {
        if (!STATE.job) { return; }

        call("job.state", { id: STATE.job.id, cursor: STATE.job.cursor }).then(function (snap) {
            if (!STATE.job) { return; }

            if (!snap || !snap.state) {      /* le moteur ne répond plus */
                finishJob(null);
                return;
            }

            applySnapshot(snap);

            if (STATE.job && (snap.state === "running" || snap.state === "waiting")) {
                STATE.job.timer = global.setTimeout(poll, POLL_MS);
            }
        });
    }

    function applySnapshot(snap) {
        /* lines s'AJOUTE, ne remplace jamais : le moteur n'envoie que la
           tranche [cursor:]. Ignorer le curseur duplique tout le journal à
           chaque tour. */
        if (snap.lines && snap.lines.length) {
            var log = $("#log");
            if (!log) { return; }
            var atBottom = log.scrollTop + log.clientHeight >= log.scrollHeight - 4;
            snap.lines.forEach(function (line) { log.appendChild(logLine(line)); });
            if (atBottom) { log.scrollTop = log.scrollHeight; }
        }
        if (typeof snap.cursor === "number") { STATE.job.cursor = snap.cursor; }

        setPercent(snap.percent, snap.task);

        if (snap.state === "waiting" && snap.question) {
            if (STATE.askedKey !== snap.question.key) { openAsk(snap.question); }
        } else if (STATE.askedKey !== null && snap.state === "running") {
            STATE.askedKey = null;           /* le worker est reparti */
            show($("#ask"), false);
        }

        if (snap.state === "done" || snap.state === "failed") {
            finishJob(snap);
        }
    }

    function finishJob(snap) {
        if (STATE.job && STATE.job.timer) { global.clearTimeout(STATE.job.timer); }
        var kind = STATE.job ? STATE.job.kind : null;
        STATE.job = null;
        STATE.askedKey = null;
        setBusy(false);
        show($("#ask"), false);

        if (!snap) { toast(t("gui_job_failed"), "err"); return; }
        if (snap.state === "failed") { toast(t("gui_job_failed"), "err"); return; }

        renderResult(kind, snap.result || {});
    }

    /* =========================================================================
       8. ACTIONS
       data-act="domaine.verbe:argument" — un seul écouteur pour toute la page.
       ========================================================================= */

    var ACTIONS = {

        "goto": function (arg) { gotoView(arg); },

        "confirm": function (arg) { closeConfirm(arg === "yes"); },

        "job.answer": function (arg) { answerAsk(arg === "yes" ? "y" : "n"); },

        "job.start": function (kind) {
            if (kind === "save") {
                confirmDialog(t("gui_confirm_save", { src: val("wdir") })).then(function (ok) {
                    if (ok) { startJob("save", {}); }
                });
                return;
            }
            if (kind === "checkfiles") {
                startJob("checkfiles", { f1: val("f1"), f2: val("f2") });
                return;
            }
            if (kind === "checkfolder") {
                startJob("checkfolder", { d1: val("d1"), d2: val("d2") });
                return;
            }
            if (kind === "restore") {
                startRestore();
                return;
            }
            startJob(kind, {});
        },

        "status.refresh": function () { startJob("status", {}); },

        "ui.pick_folder": function (target) { pick("ui.pick_folder", target); },
        "ui.pick_file": function (target) { pick("ui.pick_file", target); },

        "config.set_locations": function () {
            call("config.set_wdir", { path: val("wdir") }).then(function () {
                return call("config.set_dir", { path: val("dir") });
            }).then(function () {
                return call("config.get");
            }).then(function (cfg) {
                fillConfig(cfg);
                toast(t("gui_locations_saved"), "ok");
            });
        },

        "config.set_threshold": function () {
            call("config.set_threshold", { value: Number(val("threshold")) }).then(function (res) {
                if (res && res.ok !== false) { toast(t("gui_threshold_saved"), "ok"); }
            });
        },

        "report.readme": function () { loadReport("report.readme", "gui_readme_empty"); },
        "report.close": function () { closeReport(); },
        "report.dryrun": function () { loadReport("report.dryrun", "gui_dryrun_empty"); },

        "manifest.list": function () { loadSaves(); },

        "manifest.unlink": function () {
            if (!STATE.sel.path) { toast(t("gui_untrack_select_first"), "warn"); return; }
            confirmDialog(t("gui_untrack_confirm", { path: STATE.sel.path })).then(function (ok) {
                if (!ok) { return; }
                call("manifest.unlink", { path: STATE.sel.path }).then(function (res) {
                    if (res && res.ok !== false) {
                        STATE.sel.path = null;
                        STATE.sel.slot = null;
                        loadSaves();
                    }
                });
            });
        },

        "pygnore.set_path": function () {
            call("pygnore.set_path", { path: val("pygnore_path") }).then(function (res) {
                if (res && res.ok !== false) { loadRules(); }
            });
        },

        "pygnore.add_rule": function () {
            var pattern = String(val("rule_pattern")).trim();
            show($("#rule-error"), pattern === "");
            if (pattern === "") { return; }
            call("pygnore.add_rule", {
                kind: val("rule_kind"),
                target: val("rule_target"),
                pattern: pattern
            }).then(function (res) {
                if (res && res.ok !== false) {
                    setVal("rule_pattern", "");
                    renderRules(res);
                }
            });
        },

        "pygnore.del_rule": function () {
            if (!STATE.sel.rule) { return; }
            call("pygnore.del_rule", STATE.sel.rule).then(function (res) {
                if (res && res.ok !== false) {
                    STATE.sel.rule = null;
                    renderRules(res);
                }
            });
        },

        "pygnore.test": function () {
            call("pygnore.test", { name: val("test_name"), is_dir: val("test_isdir") }).then(function (res) {
                if (!res || res.ok === false) { return; }
                var node = $("#test-result");
                node.className = "msg " + (res.included ? "ok" : "err");
                setKey(node, res.included ? "gui_test_included" : "gui_test_excluded");
                show(node, true);
            });
        },

        /* Une lecture, pas un job : get_child_list n'appelle jamais
           compute_hash, donc l'arbre reste explorable pendant une sauvegarde. */
        "tree.children": function () { loadTree(val("tree_path")); },

        "theme.accent_reset": function () { resetAccent(); }
    };

    function dispatch(raw) {
        var cut = raw.indexOf(":");
        var name = cut === -1 ? raw : raw.slice(0, cut);
        var arg = cut === -1 ? null : raw.slice(cut + 1);
        var fn = ACTIONS[name];
        if (fn) { fn(arg); }
    }

    function pick(endpoint, target) {
        call(endpoint, {}).then(function (res) {
            if (res && res.path) { setVal(target, res.path); }
        });
    }

    /* =========================================================================
       9. RENDUS PAR ÉCRAN
       ========================================================================= */

    var STATUS_TONE = {
        uptodate: "ok",
        changes: "warn",
        no_backup: "unknown",
        integrity_warn: "err",
        error: "err",
        restored: "ok",
        unknown: "unknown"
    };

    function renderStatus(res) {
        var status = res.status || "unknown";
        var node = $("#status-word");
        node.dataset.tone = STATUS_TONE[status] || "unknown";
        setKey(node, "gui_status_" + status, status === "changes" ? { n: res.n } : null);
    }

    function renderResult(kind, result) {
        if (kind === "status") { renderStatus(result); return; }

        if (kind === "save") {
            toast(t("gui_job_done"), "ok");
            startJob("status", {});
            return;
        }

        if (kind === "dryrun") {
            var found = (result.changes || []).length;
            renderStatus({ status: found ? "changes" : "uptodate", n: found });
            renderChanges($("#dryrun-changes"), result.changes || []);
            if (!found) { toast(t("gui_no_changes"), "ok"); }
            show($("#report-tools"), true);
            return;
        }

        if (kind === "restore") {
            var warn = result.changes && result.changes.length;
            toast(t(warn ? "gui_restore_integrity_warn" : "gui_restore_success"), warn ? "warn" : "ok");
            return;
        }

        if (kind === "checkfiles") {
            setKey($("#files-verdict"), result.identical ? "gui_files_identical" : "gui_files_different");
            show($("#files-result"), true);
            return;
        }

        if (kind === "checkfolder") {
            var changes = result.changes || [];
            renderChanges($("#folders-changes"), changes);
            show($("#folders-nodiff"), changes.length === 0);
            return;
        }
    }

    var CHANGE_SIGN = { created: "+", deleted: "-", modified: "~", moved: ">" };

    /* comparefolder est déjà mis à plat par le moteur en {kind, path} : le front
       ne connaît pas la position du None dans le tuple d'origine.
       Le signe est un symbole, pas du texte : il ne se traduit pas. Le mot, si. */
    function renderChanges(container, changes) {
        container.textContent = "";
        changes.forEach(function (c) {
            var line = el("li");
            line.dataset.kind = c.kind;
            line.dataset.sign = CHANGE_SIGN[c.kind] || "?";

            var kind = el("span", "change-kind");
            setKey(kind, "gui_change_" + c.kind);
            line.appendChild(kind);
            line.appendChild(el("span", "change-path", c.path));

            container.appendChild(line);
        });
    }

    function loadReport(endpoint, emptyKey) {
        call(endpoint, {}).then(function (res) {
            var node = $("#report");
            if (!res || res.ok === false || !res.text) { setKey(node, emptyKey); }
            else { node.removeAttribute("data-i18n"); node.textContent = res.text; }
            show(node, true);
            show($("#report-tools"), true);
        });
    }

    function closeReport() {
        show($("#report"), false);
        show($("#report-tools"), false);
        var list = $("#dryrun-changes");
        if (list) { list.textContent = ""; }
    }

    /* ---- sauvegardes suivies ---------------------------------------------- */

    function loadSaves() {
        call("manifest.list", {}).then(function (res) {
            if (!res || res.ok === false) { return; }
            renderSaves(res.sources || []);
        });
    }

    function renderSaves(sources) {
        var body = $("#saves-rows");
        body.textContent = "";
        show($("#saves-empty"), sources.length === 0);

        sources.forEach(function (s) {
            var row = document.createElement("tr");
            row.dataset.path = s.path;
            row.dataset.slot = s.slot;

            row.appendChild(el("td", null, s.path));

            var state = el("td");
            if (!s.has_current) { setKey(state, "gui_slot_incomplete"); }
            else if (s.last) { state.textContent = s.last; }
            else { setKey(state, "gui_value_none"); }
            row.appendChild(state);

            row.addEventListener("click", function () { selectSource(row, s); });
            body.appendChild(row);
        });
    }

    function selectSource(row, source) {
        $$("#saves-rows tr").forEach(function (r) { r.removeAttribute("aria-selected"); });
        row.setAttribute("aria-selected", "true");
        STATE.sel.path = source.path;
        STATE.sel.slot = source.slot;
        STATE.sel.archive = null;
        loadArchives(source.slot);
    }

    function loadArchives(slot) {
        call("manifest.archives", { slot: slot }).then(function (res) {
            if (!res || res.ok === false) { return; }
            renderArchives(res);
        });
    }

    function renderArchives(res) {
        var current = $("#archive-current");
        var older = $("#archive-older");
        current.textContent = "";
        older.textContent = "";

        var list = [];
        if (res.current) { list.push({ node: current, item: res.current, isOlder: false }); }
        (res.older || []).forEach(function (a) { list.push({ node: older, item: a, isOlder: true }); });

        show($("#archive-empty"), list.length === 0);

        list.forEach(function (entry) {
            var row = el("div", "archive-item");
            row.appendChild(el("span", null, entry.item.name));
            row.appendChild(el("span", "dim", entry.item.date || ""));
            row.addEventListener("click", function () {
                $$(".archive-item").forEach(function (r) { r.removeAttribute("aria-selected"); });
                row.setAttribute("aria-selected", "true");
                STATE.sel.archive = entry.item.name;
                STATE.sel.fromOlder = entry.isOlder;
                setVal("from_older", entry.isOlder);
            });
            entry.node.appendChild(row);
        });
    }

    /* Les deux pré-réponses se fabriquent ici : le job part avec tout ce que le
       cœur aurait demandé, et ne pose donc aucune question en vol. */
    function startRestore() {
        if (!STATE.sel.path) { toast(t("gui_restore_select_first"), "warn"); return; }
        startJob("restore", {
            source: STATE.sel.path,
            slot: STATE.sel.slot,
            dest: val("restore_dest"),
            from_older: val("from_older"),
            archive: STATE.sel.archive
        });
    }

    /* ---- filtres ----------------------------------------------------------- */

    function loadRules() {
        call("pygnore.get", {}).then(function (res) {
            if (!res || res.ok === false) { return; }
            renderRules(res);
        });
    }

    function renderRules(res) {
        if (res.path !== undefined) { setVal("pygnore_path", res.path); }
        renderRuleTable($("#rules-inc"), res.inc || [], "inc");
        renderRuleTable($("#rules-exc"), res.exc || [], "exc");
        STATE.sel.rule = null;
    }

    /* inc/exc arrivent en [typ, pat] : l'ordre est typ D'ABORD, et typ ne
       s'affiche jamais brut — "fi"/"fo" passent par les clés de langue. */
    function renderRuleTable(body, rules, kind) {
        body.textContent = "";
        rules.forEach(function (rule) {
            var target = rule[0];
            var pattern = rule[1];

            var row = document.createElement("tr");
            row.appendChild(el("td", null, pattern));

            var cell = el("td");
            setKey(cell, target === "fo" ? "gui_rule_target_folder" : "gui_rule_target_file");
            row.appendChild(cell);

            row.addEventListener("click", function () {
                $$("#rules-inc tr, #rules-exc tr").forEach(function (r) { r.removeAttribute("aria-selected"); });
                row.setAttribute("aria-selected", "true");
                STATE.sel.rule = { kind: kind, target: target, pattern: pattern };
            });
            body.appendChild(row);
        });
    }

    /* ---- arborescence ------------------------------------------------------ */

    function loadTree(path) {
        var root = $("#tree-root");
        root.textContent = "";
        openNode(path, root);
    }

    function openNode(path, container) {
        return call("tree.children", { path: path }).then(function (res) {
            if (!res || res.ok === false) { return; }

            if (res.error) {
                var msg = $("#tree-msg");
                setKey(msg, res.error === "denied" ? "gui_tree_denied" : "gui_tree_not_folder");
                show(msg, true);
                return;
            }

            var entries = res.entries || [];
            show($("#tree-msg"), entries.length === 0);
            if (entries.length === 0) { setKey($("#tree-msg"), "gui_tree_empty"); }

            entries.forEach(function (entry) {
                container.appendChild(treeNode(entry));
            });
        });
    }

    function treeNode(entry) {
        var li = document.createElement("li");
        var node = el("span", "node", entry.name);
        node.dataset.type = entry.is_dir ? "dir" : "file";
        li.appendChild(node);

        if (entry.is_dir) {
            node.setAttribute("aria-expanded", "false");
            node.addEventListener("click", function () {
                var open = node.getAttribute("aria-expanded") === "true";
                var sub = li.querySelector("ul");

                if (open) {
                    node.setAttribute("aria-expanded", "false");
                    if (sub) { sub.hidden = true; }
                    return;
                }
                node.setAttribute("aria-expanded", "true");
                if (sub) { sub.hidden = false; return; }

                sub = document.createElement("ul");
                li.appendChild(sub);
                openNode(entry.path, sub);       /* un niveau à la fois */
            });
        }
        return li;
    }

    /* =========================================================================
       10. THÈME ET ACCENT
       Le thème n'est qu'un fichier de variables : on change le href, la cascade
       fait le reste. L'accent utilisateur passe après, donc il gagne.
       ========================================================================= */

    /* Appliquer et enregistrer sont deux choses distinctes : le démarrage
       applique ce que la config contient, il ne le réécrit pas. */
    function applyTheme(name) {
        var node = $("#pg-theme");
        if (node) { node.setAttribute("href", "UI/themes/" + name + ".css"); }
    }

    function applyAccent(hex) {
        var node = $("#pg-accent");
        if (!node) { return; }

        var rgb = hexToRgb(hex);
        if (!rgb) { node.textContent = ""; return; }

        /* --pg-accent-dim et --pg-accent-text sont dérivées ici, sinon un accent
           clair donne du blanc sur blanc dans les boutons primaires. Aucune
           couleur en dur : le fond de mélange et les deux couleurs de texte
           viennent de la feuille en place, donc un thème sombre est suivi. */
        var surface = cssColor("--pg-surface") || [255, 255, 255];
        var dim = "rgb(" + mix(rgb[0], surface[0], .88) + ","
                         + mix(rgb[1], surface[1], .88) + ","
                         + mix(rgb[2], surface[2], .88) + ")";
        var luma = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255;

        node.textContent = ":root{"
            + "--pg-accent:" + hex + ";"
            + "--pg-accent-dim:" + dim + ";"
            + "--pg-accent-text:" + (luma > 0.62 ? "var(--pg-text)" : "var(--pg-text-invert)") + ";"
            + "}";
    }

    function saveTheme(name) {
        applyTheme(name);
        call("config.set_theme", { theme: name }).then(function (res) {
            if (res && res.ok !== false) { toast(t("gui_theme_saved"), "ok"); }
        });
    }

    function saveAccent(hex) {
        applyAccent(hex);
        call("config.set_accent", { accent: hex || "" });
    }

    function resetAccent() {
        var node = $("#pg-accent");
        if (node) { node.textContent = ""; }
        call("config.set_accent", { accent: "" }).then(function () {
            setVal("accent", currentAccent());
        });
    }

    /* Valeur affichée par le sélecteur quand la config n'en impose aucune :
       celle du thème en place, lue dans la cascade. Rien n'est écrit en dur. */
    function currentAccent() {
        var rgb = cssColor("--pg-accent");
        if (!rgb) { return "#000000"; }
        return "#" + rgb.map(function (c) {
            var h = c.toString(16);
            return h.length === 1 ? "0" + h : h;
        }).join("");
    }

    function cssColor(name) {
        var raw = global.getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        if (!raw) { return null; }
        var hex = hexToRgb(raw);
        if (hex) { return hex; }
        var m = /rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/.exec(raw);
        return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
    }

    function hexToRgb(hex) {
        var m = /^#?([0-9a-f]{6})$/i.exec(String(hex).trim());
        if (!m) { return null; }
        var n = parseInt(m[1], 16);
        return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }

    function mix(a, b, ratio) { return Math.round(a + (b - a) * ratio); }

    /* =========================================================================
       11. DÉMARRAGE
       ========================================================================= */

    function fillLangs(supported, current) {
        var select = $("#in-lang");
        select.textContent = "";
        (supported || []).forEach(function (code) {
            var option = el("option");
            option.value = code;
            /* lang_<code> vient du fichier de langue lui-même : chaque langue
               s'affiche dans sa propre écriture. */
            setKey(option, "lang_" + code);
            select.appendChild(option);
        });
        if (current) { select.value = current; }
    }

    function fillConfig(cfg) {
        if (!cfg || cfg.ok === false) { return; }
        setVal("wdir", cfg.wdir);
        setVal("dir", cfg.dir);
        setKey($("#spec-src"), "gui_value_none");
        setKey($("#spec-dir"), "gui_value_none");
        if (cfg.wdir) { $("#spec-src").removeAttribute("data-i18n"); text("#spec-src", cfg.wdir); }
        if (cfg.dir) { $("#spec-dir").removeAttribute("data-i18n"); text("#spec-dir", cfg.dir); }

        if (cfg.threshold !== undefined) {
            setVal("threshold", cfg.threshold);
            setKey($("#threshold-label"), "gui_threshold_label", { value: cfg.threshold });
        }
        if (cfg.pygnore_path !== undefined) { setVal("pygnore_path", cfg.pygnore_path); }

        if (cfg.theme) { applyTheme(cfg.theme); setVal("theme", cfg.theme); }
        if (cfg.accent) { applyAccent(cfg.accent); }
        setVal("accent", cfg.accent || currentAccent());
    }

    function switchLang(code) {
        call("config.set_lang", { lang: code }).then(function (res) {
            if (!res || res.ok === false || !res.strings) { return; }
            STR = res.strings;
            applyStrings();                 /* aucun rechargement, aucun DOM reconstruit */
            show($("#lang-msg"), true);
            global.setTimeout(function () { show($("#lang-msg"), false); }, 3000);
        });
    }

    /* Un écouteur sur un nœud absent ne doit pas faire tomber tout le
       démarrage : sans ce garde-fou, un seul id manquant laisse l'interface
       entière non traduite et sans navigation, pour une ligne. */
    function on(selector, type, handler) {
        var node = $(selector);
        if (node) { node.addEventListener(type, handler); }
    }

    function bindEvents() {
        document.addEventListener("click", function (event) {
            var source = event.target;
            if (!source || typeof source.closest !== "function") { return; }
            var target = source.closest("[data-act], [data-goto]");
            if (!target) { return; }
            if (target.hasAttribute("data-goto")) { gotoView(target.getAttribute("data-goto")); return; }
            dispatch(target.getAttribute("data-act"));
        });

        on("#in-lang", "change", function (e) { switchLang(e.target.value); });
        on("#in-theme", "change", function (e) { saveTheme(e.target.value); });
        /* input applique en direct pendant qu'on glisse dans le nuancier,
           change n'arrive qu'au relâchement : on n'écrit dans la config que
           là, sinon on réécrit le fichier cent fois par seconde. */
        on("#in-accent", "input", function (e) { applyAccent(e.target.value); });
        on("#in-accent", "change", function (e) { saveAccent(e.target.value); });

        on("#in-threshold", "input", function (e) {
            setKey($("#threshold-label"), "gui_threshold_label", { value: e.target.value });
        });
    }

    function boot() {
        bindEvents();

        call("i18n.bootstrap", {}).then(function (res) {
            if (res && res.strings) {
                STR = res.strings;
                fillLangs(res.supported, res.current);
            }
            applyStrings();
            return call("config.get", {});
        }).then(function (cfg) {
            fillConfig(cfg);
            return call("app.info", {});
        }).then(function (info) {
            if (info && info.version) { text("#about-version", info.version); }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }

    /* Exposé pour la console de développement uniquement. */
    global.PyGit = { t: t, applyStrings: applyStrings, renderRich: renderRich, state: STATE };

}(window));