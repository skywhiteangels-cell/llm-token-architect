/**
 * Quote Guard  (v3 — context-aware state machine, multi-shell)
 * Author: SkyAngel
 * License: MIT
 *
 * Purpose
 * -------
 * Pre-flight verification of a terminal command string BEFORE it is handed to a
 * shell. Prevents the interactive-prompt deadlock: when a command ends inside an
 * unterminated quote / backtick / escape context, PowerShell, CMD and bash all
 * assume the user is still typing, print a continuation prompt (`>>` or `>`),
 * and wait forever. For an autonomous agent this is an unrecoverable hang —
 * there is no stderr to read, no error code to self-correct from.
 *
 * WHAT CHANGED IN v3
 * ------------------
 * v2 asked the right question ("is the lexer still inside a quote at end of
 * string?") but answered it with POSIX rules only. On Windows PowerShell that is
 * the wrong grammar: PowerShell escapes with a BACKTICK, not a backslash, so
 * `dir "C:\"` and `echo "a`"b"` are both valid there — and v2 blocked them.
 * A guardrail that blocks valid commands gets bypassed, and then it protects
 * nothing. v3 takes the shell as an explicit parameter.
 *
 *   'posix'       bash / sh / zsh / Git Bash  — backslash escapes, backtick quotes
 *   'powershell'  PowerShell 5.1 / 7+         — backtick escapes, '' and "" double
 *   'cmd'         cmd.exe                     — ^ escapes, only " quotes
 *
 * Also new: a dangling escape at end-of-string (trailing \, ` or ^) is reported.
 * Not a quote problem, but the same hang — those are line continuations.
 *
 * Limitations: heredoc bodies are masked for POSIX (an unterminated heredoc is
 * reported as a hang); not modelled: POSIX $'...', PowerShell $(...) inside
 * double quotes, and heredocs nested inside $(...). A guardrail, not a parser.
 * See README.md.
 *
 * Usage:
 *   const { verifyQuoteParity, analyze } = require('./parity_check');
 *   verifyQuoteParity('echo "hi', 'powershell');        // false
 *   node parity_check.js -c "echo hi" --shell posix
 *   node parity_check.js --selftest
 *
 * Exit codes: 0 — safe, 1 — would hang the shell, 2 — usage error.
 */

const SHELLS = ['posix', 'powershell', 'cmd'];

/**
 * Inspect a command string and report whether it can hang a shell.
 * @param {string} command
 * @param {'posix'|'powershell'|'cmd'} shell
 * @returns {{safe:boolean,state:string,shell:string,reason:string,offset:(number|null)}}
 */
/**
 * Blank heredoc bodies, keeping length and newlines (so offsets stay valid).
 * Returns { masked, bad }: bad is the offset of an unterminated heredoc, or null.
 *
 * A heredoc body is read verbatim by the shell, so quotes inside it open
 * nothing. Without masking, a legitimate `cat <<EOF` script is blocked by a
 * line-level lexer; with it, only what actually executes is checked.
 *
 * Limits (deliberate): the first heredoc on a line is handled; the terminator
 * must be a line exactly equal to the delimiter (leading tabs allowed for
 * `<<-`); heredocs nested inside `$(...)` are not recognised.
 */
function maskHeredocs(command) {
    const n = command.length;
    const out = command.split('');
    let state = 'NORMAL';
    let i = 0;

    const blank = (start, end) => {
        for (let x = start; x < end; x++) if (command[x] !== '\n') out[x] = ' ';
    };

    while (i < n) {
        const c = command[i];

        if (state === 'NORMAL') {
            if (c === '\\') { i += 2; continue; }
            if (c === "'") { state = 'SINGLE'; i += 1; continue; }
            if (c === '"') { state = 'DOUBLE'; i += 1; continue; }
            if (c === '`') { state = 'BACKTICK'; i += 1; continue; }
            if (command.startsWith('<<', i)) {
                let j = i + 2;
                let stripTabs = false;
                if (command[j] === '-') { stripTabs = true; j += 1; }
                while (j < n && (command[j] === ' ' || command[j] === '\t')) j += 1;
                let quote = null;
                if (command[j] === "'" || command[j] === '"') { quote = command[j]; j += 1; }
                let k = j;
                while (k < n && /[A-Za-z0-9_-]/.test(command[k])) k += 1;
                const delim = command.slice(j, k);
                if (quote && command[k] === quote) k += 1;
                if (!delim) { i += 2; continue; }        // `<<<` here-string: no body
                const eol = command.indexOf('\n', k);
                if (eol === -1) return { masked: out.join(''), bad: i };
                const pos = eol + 1;
                let found = -1;
                let p = pos;
                while (p <= n) {
                    const le = command.indexOf('\n', p);
                    const lineEnd = le === -1 ? n : le;
                    const line = command.slice(p, lineEnd);
                    const cand = stripTabs ? line.replace(/^\t+/, '') : line;
                    if (cand === delim) { found = p; break; }
                    if (le === -1) break;
                    p = le + 1;
                }
                if (found === -1) { blank(pos, n); return { masked: out.join(''), bad: i }; }
                blank(pos, found);
                const le = command.indexOf('\n', found);
                i = le === -1 ? n : le + 1;
                continue;
            }
            i += 1;
            continue;
        }

        if (state === 'SINGLE') {
            if (c === "'") state = 'NORMAL';
            i += 1;
            continue;
        }

        if (state === 'DOUBLE') {
            if (c === '\\') { i += 2; continue; }
            if (c === '"') state = 'NORMAL';
            i += 1;
            continue;
        }

        if (state === 'BACKTICK') {
            if (c === '\\') { i += 2; continue; }
            if (c === '`') state = 'NORMAL';
            i += 1;
            continue;
        }
    }

    return { masked: out.join(''), bad: null };
}

function analyze(command, shell = 'posix') {
    if (!SHELLS.includes(shell)) {
        throw new Error(`unknown shell '${shell}'; expected one of ${SHELLS.join(', ')}`);
    }
    if (typeof command !== 'string') {
        return { safe: false, state: 'INVALID', shell, reason: 'command is not a string', offset: null };
    }

    if (shell === 'posix') {
        // Heredoc bodies are read verbatim: mask them, and report an
        // unterminated heredoc as the hang it is.
        const m = maskHeredocs(command);
        if (m.bad !== null) {
            return {
                safe: false,
                state: 'HEREDOC',
                shell,
                reason: `heredoc opened at ${m.bad} is never terminated (shell waits for the delimiter)`,
                offset: m.bad,
            };
        }
        command = m.masked;
    }

    let state = 'NORMAL';
    let openedAt = null;
    let i = 0;
    const n = command.length;

    const openContext = (s, at) => { state = s; openedAt = at; };
    const closeContext = () => { state = 'NORMAL'; openedAt = null; };
    const danglingEscape = (at) => ({
        safe: false,
        state: 'ESCAPE',
        shell,
        reason: 'dangling escape at end-of-string (line continuation, shell waits for more input)',
        offset: at,
    });

    while (i < n) {
        const c = command[i];

        if (state === 'NORMAL') {
            if (shell === 'powershell') {
                if (c === '`') {                       // backtick is THE escape char
                    if (i + 1 >= n) return danglingEscape(i);
                    i += 2; continue;
                }
                if (c === "'") openContext('SINGLE', i);
                else if (c === '"') openContext('DOUBLE', i);

            } else if (shell === 'cmd') {
                if (c === '^') {                       // cmd escape outside quotes
                    if (i + 1 >= n) return danglingEscape(i);
                    i += 2; continue;
                }
                if (c === '"') openContext('DOUBLE', i);

            } else {                                   // posix
                if (c === '\\') {
                    if (i + 1 >= n) return danglingEscape(i);
                    i += 2; continue;
                }
                if (c === "'") openContext('SINGLE', i);
                else if (c === '"') openContext('DOUBLE', i);
                else if (c === '`') openContext('BACKTICK', i);
            }

        } else if (state === 'SINGLE') {
            if (shell === 'powershell') {
                if (c === "'") {
                    if (i + 1 < n && command[i + 1] === "'") { i += 2; continue; } // '' literal
                    closeContext();
                }
            } else {                                   // posix: everything literal here
                if (c === "'") closeContext();
            }

        } else if (state === 'DOUBLE') {
            if (shell === 'powershell') {
                if (c === '`') {
                    if (i + 1 >= n) return danglingEscape(i);
                    i += 2; continue;
                }
                if (c === '"') {
                    if (i + 1 < n && command[i + 1] === '"') { i += 2; continue; } // "" literal
                    closeContext();
                }
            } else if (shell === 'cmd') {
                if (c === '"') closeContext();
            } else {
                if (c === '\\') {
                    if (i + 1 >= n) return danglingEscape(i);
                    i += 2; continue;
                }
                if (c === '"') closeContext();
            }

        } else if (state === 'BACKTICK') {             // posix only
            if (c === '`') closeContext();
            else if (c === '\\') {
                if (i + 1 >= n) return danglingEscape(i);
                i += 2; continue;
            }
        }

        i += 1;
    }

    if (state === 'NORMAL') {
        return { safe: true, state: 'NORMAL', shell, reason: 'lexer closed at end-of-string', offset: null };
    }
    return {
        safe: false,
        state,
        shell,
        reason: `unterminated ${state.toLowerCase()} context opened at offset ${openedAt}`,
        offset: openedAt,
    };
}

/**
 * Drop-in replacement for the v1/v2 signature.
 * @returns {boolean} true when the command will NOT hang an interactive shell.
 */
function verifyQuoteParity(command, shell = 'posix') {
    return analyze(command, shell).safe;
}

// [shell, command, expectedSafe]
const CASES = [
    // --- posix -------------------------------------------------------------
    ['posix', 'echo "it\'s a test"', true],
    ['posix', 'echo "hi', false],
    ['posix', 'cat `unterminated', false],
    ['posix', 'echo "a\\""', true],
    ['posix', 'dir "C:\\temp"', true],
    ['posix', 'dir "C:\\"', false],              // bash: the backslash escapes the quote
    ['posix', "echo 'it'\\''s'", true],
    ['posix', 'echo foo\\', false],              // trailing backslash = line continuation
    ['posix', 'echo "a" && echo "b"', true],
    // --- powershell --------------------------------------------------------
    ['powershell', 'dir "C:\\"', true],          // <-- the v2 bug
    ['powershell', 'dir "C:\\temp\\"', true],
    ['powershell', 'echo "a`"b"', true],         // backtick escapes the quote
    ['powershell', 'echo "hi', false],
    ['powershell', "echo 'it''s'", true],        // '' is a literal quote in PS
    ['powershell', "echo 'it's'", false],
    ['powershell', 'Write-Output "unterminated', false],
    ['powershell', 'echo `n', true],
    ['powershell', 'echo hi`', false],           // trailing backtick = line continuation
    ['powershell', 'powershell -Command "echo `"hi`""', true],
    // --- cmd ---------------------------------------------------------------
    ['cmd', 'echo "hi', false],
    ['cmd', 'echo "a\\"', true],
    ['cmd', 'echo ^"hi', true],
    ['cmd', 'echo hi^', false],
];

function runSelftest() {
    console.log('=== Quote Guard v3 — built-in tests ===');
    let failed = 0;
    for (const [shell, cmd, expected] of CASES) {
        const got = verifyQuoteParity(cmd, shell);
        const ok = got === expected;
        if (!ok) failed += 1;
        console.log(`  [${ok ? 'OK  ' : 'FAIL'}] ${shell.padEnd(10)} expected=${String(expected).padEnd(5)} got=${String(got).padEnd(5)}  ${cmd}`);
    }
    if (failed) {
        console.log(`\n${failed}/${CASES.length} FAILED`);
        return 1;
    }
    console.log(`\nALL PASS (${CASES.length} cases)`);
    return 0;
}

function runCli() {
    const args = process.argv.slice(2);

    if (args.length === 0 || args.includes('--selftest')) {
        process.exit(runSelftest());
    }

    let command = null;
    let shell = 'posix';
    let asJson = false;
    let fromStdin = false;

    for (let i = 0; i < args.length; i++) {
        const a = args[i];
        if (a === '-c' || a === '--command') command = args[++i] ?? '';
        else if (a === '--shell') shell = args[++i] ?? 'posix';
        else if (a === '--json') asJson = true;
        else if (a === '--stdin') fromStdin = true;
    }

    if (!SHELLS.includes(shell)) {
        console.error(`Error: unknown shell '${shell}'. Use one of: ${SHELLS.join(', ')}`);
        process.exit(2);
    }

    if (fromStdin) {
        command = require('fs').readFileSync(0, 'utf8').replace(/[\r\n]+$/, '');
    }

    if (command === null) {
        console.error('Error: no command provided.');
        console.error('Usage: node parity_check.js -c "your command" [--shell posix|powershell|cmd] [--json]');
        process.exit(2);
    }

    const result = analyze(command, shell);

    if (asJson) {
        console.log(JSON.stringify(result));
    } else if (result.safe) {
        console.log('PARITY OK — command is safe to execute.');
    } else {
        console.error(`PARITY VIOLATION — ${result.reason}. Command blocked before shell execution!`);
    }

    process.exit(result.safe ? 0 : 1);
}

if (require.main === module) {
    runCli();
}

module.exports = { verifyQuoteParity, analyze, SHELLS };
