/* =============================================================================
   PyGit — bridge.js
   -----------------------------------------------------------------------------
   SEUL fichier du front qui sait que pywebview existe. Tout le reste de
   l'interface passe par Bridge.call("domaine.verbe", payload) et ne connaît
   que des objets JSON.

   C'est ce fichier, et lui seul, qu'il faudra réécrire le jour où le backend
   change (HTTP local, Rust, autre webview). Si un `pywebview` apparaît ailleurs
   que dans ce fichier, la propriété est perdue.

   Contraintes de la cible (WebKitGTK, page chargée en file://) :
     - pas de `import` / `export` : les modules ES sont bloqués par CORS en
       file:// selon les moteurs. Script classique, un objet global.
     - pas de `fetch` : même raison.
     - un seul argument par appel. `job.start` -> `api.job_start(payload)`, où
       payload est un objet. Côté Python la signature est donc toujours
       `def job_start(self, params)`.
   ============================================================================= */

(function (global) {
    "use strict";

    /* pywebview injecte window.pywebview.api puis émet `pywebviewready`. Selon
       la vitesse de la fenêtre, l'API peut déjà être là quand ce script tourne :
       les deux cas doivent être couverts, sinon on attend un évènement déjà
       passé et l'interface reste vide sans erreur. */
    var READY_TIMEOUT = 8000;

    var readyPromise = null;

    function waitForApi() {
        return new Promise(function (resolve) {
            if (global.pywebview && global.pywebview.api) {
                resolve(true);
                return;
            }
            var settled = false;
            function done(value) {
                if (settled) { return; }
                settled = true;
                resolve(value);
            }
            global.addEventListener("pywebviewready", function () {
                done(!!(global.pywebview && global.pywebview.api));
            }, { once: true });

            /* Pas de backend au bout du délai : on ne bloque pas l'interface.
               C'est ce qui permet d'ouvrir index.html dans un navigateur pour
               travailler le CSS — les appels répondent no_backend au lieu de
               rester en suspens pour toujours. */
            global.setTimeout(function () { done(false); }, READY_TIMEOUT);
        });
    }

    function ready() {
        if (readyPromise === null) {
            readyPromise = waitForApi();
        }
        return readyPromise;
    }

    /* "domaine.verbe" côté front, "domaine_verbe" côté Python. Cette ligne est
       tout le mapping. */
    function methodName(endpoint) {
        return String(endpoint).replace(".", "_");
    }

    /* Un appel ne lève JAMAIS. Toute erreur devient un objet de la même forme
       que les refus du moteur ({ok:false, reason}), ce qui évite un try/catch
       autour de chacun des vingt-cinq appels d'app.js. */
    function call(endpoint, payload) {
        return ready().then(function (available) {
            if (!available) {
                return { ok: false, reason: "no_backend", endpoint: endpoint };
            }
            var api = global.pywebview.api;
            var fn = api[methodName(endpoint)];
            if (typeof fn !== "function") {
                return { ok: false, reason: "unknown_endpoint", endpoint: endpoint };
            }
            return Promise.resolve(fn(payload === undefined ? {} : payload))
                .then(function (raw) {
                    if (raw === null || raw === undefined) {
                        return { ok: false, reason: "empty", endpoint: endpoint };
                    }
                    /* pywebview sérialise déjà en objet, mais un moteur qui
                       renverrait la chaîne JSON brute reste supporté. */
                    if (typeof raw === "string") {
                        try {
                            return JSON.parse(raw);
                        } catch (err) {
                            return { ok: false, reason: "bad_json", endpoint: endpoint, detail: raw };
                        }
                    }
                    return raw;
                })
                .catch(function (err) {
                    return { ok: false, reason: "bridge", endpoint: endpoint, detail: String(err) };
                });
        });
    }

    function hasBackend() {
        return !!(global.pywebview && global.pywebview.api);
    }

    global.Bridge = {
        ready: ready,
        call: call,
        hasBackend: hasBackend
    };

}(window));
