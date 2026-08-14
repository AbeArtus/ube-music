"use client";

import { useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";

const PYGBAG_CDN = "https://pygame-web.github.io/cdn/0.9.3/pythons.js";
const GAME_HTML_URL = "/build/web/catsemblem.html";

// The game (thumbox.py) reads WASD for the d-pad and , / . for the B/A
// buttons via pygame's key state, so on-screen buttons just need to fire
// real keydown/keyup events with the matching physical key `code`.
type KeyName = "up" | "down" | "left" | "right" | "a" | "b";

const KEYS: Record<KeyName, { key: string; code: string; keyCode: number }> = {
  up: { key: "w", code: "KeyW", keyCode: 87 },
  down: { key: "s", code: "KeyS", keyCode: 83 },
  left: { key: "a", code: "KeyA", keyCode: 65 },
  right: { key: "d", code: "KeyD", keyCode: 68 },
  a: { key: ".", code: "Period", keyCode: 190 },
  b: { key: ",", code: "Comma", keyCode: 188 },
};

const CODE_TO_NAME: Record<string, KeyName> = Object.fromEntries(
  (Object.entries(KEYS) as [KeyName, (typeof KEYS)[KeyName]][]).map(
    ([name, binding]) => [binding.code, name]
  )
);

const EMPTY_PRESSED: Record<KeyName, boolean> = {
  up: false,
  down: false,
  left: false,
  right: false,
  a: false,
  b: false,
};

// The game (ThumbySaves in thumbox.py) writes saves to
// "Saves/CatsEmblem/persistent.json" relative to its cwd. The bootstrap
// in catsemblem.html calls os.chdir(tempfile.gettempdir()) = "/tmp", so
// the actual absolute path is below. The emscripten MEMFS is wiped on
// every reload, so we mirror the file to/from localStorage ourselves.
const SAVE_PATH = "/tmp/Saves/CatsEmblem/persistent.json";
const STORAGE_KEY = "catsemblem-save";

// pygbag sets window.python = vm (the emscripten Module) in its postRun
// hook, and emscripten attaches FS to that module object.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getEmscriptenFS(): any {
  const w = window as unknown as {
    python?: { FS?: unknown };
    FS?: unknown;
  };
  return w.python?.FS ?? w.FS ?? null;
}

// Waits for the CPython WASM interpreter's filesystem to become available,
// restores any previously saved data into the file before the game's lazy
// setName() call reads it, then periodically mirrors saves back to
// localStorage. Returns a cleanup function.
async function setupPersistentSaves(isCancelled: () => boolean) {
  let FS = getEmscriptenFS();
  const deadline = Date.now() + 30000;
  while (!isCancelled() && !FS && Date.now() < deadline) {
    await new Promise<void>((resolve) => setTimeout(resolve, 100));
    FS = getEmscriptenFS();
  }
  if (isCancelled() || !FS) {
    if (!isCancelled()) {
      console.warn("Persistent saves: emscripten FS never became ready");
    }
    return () => {};
  }

  // Restore any existing save into the MEMFS file before the game's lazy
  // ThumbySaves.setName() reads it. The game only calls setName() when the
  // user opens the main menu, so we have plenty of time.
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      FS.mkdirTree("/tmp/Saves/CatsEmblem");
      FS.writeFile(SAVE_PATH, saved, { encoding: "utf8" });
    } catch (err) {
      console.error("Persistent saves: restore failed", err);
    }
  }

  const flush = () => {
    try {
      const data: string = FS.readFile(SAVE_PATH, { encoding: "utf8" });
      if (data && data !== "{}") {
        localStorage.setItem(STORAGE_KEY, data);
      }
    } catch {
      // File not written yet — normal during early load
    }
  };

  const interval = setInterval(flush, 3000);
  const handleVisibility = () => {
    if (document.visibilityState === "hidden") flush();
  };
  window.addEventListener("pagehide", flush);
  document.addEventListener("visibilitychange", handleVisibility);

  return () => {
    flush();
    clearInterval(interval);
    window.removeEventListener("pagehide", flush);
    document.removeEventListener("visibilitychange", handleVisibility);
  };
}

function dispatchKey(type: "keydown" | "keyup", name: KeyName) {
  const binding = KEYS[name];
  const event = new KeyboardEvent(type, {
    key: binding.key,
    code: binding.code,
    bubbles: true,
    cancelable: true,
  });
  // keyCode/which are normally read-only getters that return 0 unless the
  // browser was told otherwise; SDL's emscripten keyboard handler reads
  // these, so they're overridden here to match a real key press.
  Object.defineProperty(event, "keyCode", { get: () => binding.keyCode });
  Object.defineProperty(event, "which", { get: () => binding.keyCode });
  document.getElementById("canvas")?.focus();
  document.dispatchEvent(event);
}

export default function GameEmbed() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mountedRef = useRef(false);
  const persistCleanupRef = useRef<(() => void) | null>(null);
  const [pressed, setPressed] = useState<Record<KeyName, boolean>>(
    EMPTY_PRESSED
  );

  // Keep the on-screen buttons visually depressed while the matching
  // physical keyboard key (WASD / , / .) is actually held down, not just
  // while the on-screen button itself is being pressed.
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const name = CODE_TO_NAME[e.code];
      if (name) setPressed((prev) => ({ ...prev, [name]: true }));
    }
    function handleKeyUp(e: KeyboardEvent) {
      const name = CODE_TO_NAME[e.code];
      if (name) setPressed((prev) => ({ ...prev, [name]: false }));
    }
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  useEffect(() => {
    if (mountedRef.current) return;
    mountedRef.current = true;

    let cancelled = false;

    async function mountGame() {
      const res = await fetch(GAME_HTML_URL);
      const html = await res.text();

      const match = html.match(
        /<script[^>]*id="__main__"[^>]*>([\s\S]*)<\/script>/
      );
      if (!match || cancelled || !containerRef.current) return;

      const container = containerRef.current;

      // pythons.js looks up these elements by id (getElementById) and, if
      // missing, creates and appends them straight to document.body. Pre-
      // creating them here means it reuses ours, keeping the whole game UI
      // (canvas, 3d canvas, loading overlay) scoped inside GameEmbed instead
      // of leaking out under <body>.
      for (const id of ["canvas", "canvas3d", "html"]) {
        if (document.getElementById(id)) continue;
        const el = document.createElement(
          id === "canvas" || id === "canvas3d" ? "canvas" : "div"
        );
        el.id = id;
        container.appendChild(el);
      }

      const script = document.createElement("script");
      script.src = PYGBAG_CDN;
      script.type = "module";
      script.id = "__main__";
      // "vtx" (the xterm.js debug console) is intentionally omitted so no
      // terminal UI is created; stdout/stderr just fall back to the
      // browser console instead of an on-page console.
      script.dataset.os = "fs,gui";
      script.async = true;
      script.defer = true;
      // Raw encoded payload from pygbag's --html build; must stay byte-exact.
      script.text = match[1];

      // pythons.js's own bootstrap (auto_start) registers
      // window.addEventListener("load", onload) to kick off the actual VM
      // startup. Since we inject this script long after the page's "load"
      // event already fired, that listener would otherwise never run.
      // Re-dispatch "load" once the module has finished loading/executing.
      script.onload = () => {
        window.dispatchEvent(new Event("load"));
      };

      container.appendChild(script);

      setupPersistentSaves(() => cancelled).then((cleanup) => {
        if (cancelled) {
          cleanup();
        } else {
          persistCleanupRef.current = cleanup;
        }
      });
    }

    mountGame();

    return () => {
      cancelled = true;
      persistCleanupRef.current?.();
    };
  }, []);

  function press(name: KeyName) {
    setPressed((prev) => ({ ...prev, [name]: true }));
    dispatchKey("keydown", name);
  }

  function release(name: KeyName) {
    setPressed((prev) => ({ ...prev, [name]: false }));
    dispatchKey("keyup", name);
  }

  function buttonHandlers(name: KeyName) {
    return {
      onPointerDown: (e: ReactPointerEvent<HTMLButtonElement>) => {
        e.preventDefault();
        e.currentTarget.setPointerCapture(e.pointerId);
        press(name);
      },
      onPointerUp: (e: ReactPointerEvent<HTMLButtonElement>) => {
        e.preventDefault();
        release(name);
      },
      onPointerCancel: () => release(name),
      onLostPointerCapture: () => release(name),
      onContextMenu: (e: ReactPointerEvent<HTMLButtonElement>) =>
        e.preventDefault(),
    };
  }

  return (
    <div className="catsemblem-wrapper">
      <div ref={containerRef} className="catsemblem-embed" />
      <div className="catsemblem-controls">
        <div className="catsemblem-dpad">
          <button
            type="button"
            className={`dpad-btn dpad-up${pressed.up ? " pressed" : ""}`}
            aria-label="Up"
            {...buttonHandlers("up")}
          />
          <button
            type="button"
            className={`dpad-btn dpad-left${pressed.left ? " pressed" : ""}`}
            aria-label="Left"
            {...buttonHandlers("left")}
          />
          <div className="dpad-center dpad-btn" />
          <button
            type="button"
            className={`dpad-btn dpad-right${pressed.right ? " pressed" : ""}`}
            aria-label="Right"
            {...buttonHandlers("right")}
          />
          <button
            type="button"
            className={`dpad-btn dpad-down${pressed.down ? " pressed" : ""}`}
            aria-label="Down"
            {...buttonHandlers("down")}
          />
        </div>
        <div className="catsemblem-abbuttons">
          <button
            type="button"
            className={`ab-btn btn-b${pressed.b ? " pressed" : ""}`}
            aria-label="B"
            {...buttonHandlers("b")}
          />
          <button
            type="button"
            className={`ab-btn btn-a${pressed.a ? " pressed" : ""}`}
            aria-label="A"
            {...buttonHandlers("a")}
          />
        </div>
      </div>
    </div>
  );
}
