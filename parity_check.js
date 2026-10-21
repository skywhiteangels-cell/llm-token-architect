/**
 * Quote Parity Guardrail  (v2 — context-aware state machine)
 * Author: SkyAngel  (rewritten for correctness)
 * Purpose: Pre-flight terminal command verification to prevent interactive shell
 *          deadlocks (the '>>' prompt) caused by UNTERMINATED quotes.
 *
 * WHY v2 (what was wrong in v1):
 *   v1 counted single and double quotes independently with a regex and required
 *   each count to be even. That FALSE-POSITIVES on valid commands like
 *   echo "it's a test" (odd single-quote count) and ignores backticks entirely.
 *   It also mis-handled a double backslash before a quote (\\").
 *
 *   The correct check is the shell lexer state at end-of-string: if we are still
 *   inside a quote/backtick at EOF, the shell will hang. A state machine answers
 *   that and naturally accepts "it's" while still catching dangling quotes.
 *
 *   Limitation: guardrail, not a full POSIX/bash parser. No heredocs, no $'...',
 *   no backtick-nested-inside-double. Deliberately conservative about hanging.
 *
 * Usage:
 *   const { verifyQuoteParity } = require('./parity_check');
 *   const isSafe = verifyQuoteParity("your shell command here");
 *   node parity_check.js -c "powershell -Command \"Write-Output 'Hello'\""
 *
 * Exit codes: 0 — safe, 1 — unterminated quote/backtick detected.
 */

function verifyQuoteParity(command) {
    if (typeof command !== 'string') return false;

    let state = 'NORMAL'; // NORMAL | SINGLE | DOUBLE | BACKTICK
    let i = 0;
    const n = command.length;
    while (i < n) {
        const c = command[i];
        if (state === 'NORMAL') {
            if (c === "'") state = 'SINGLE';
            else if (c === '"') state = 'DOUBLE';
            else if (c === '`') state = 'BACKTICK';
            else if (c === '\\') { i += 2; continue; } // escaped char
        } else if (state === 'SINGLE') {
            if (c === "'") state = 'NORMAL';           // backslash is literal inside ''
        } else if (state === 'DOUBLE') {
            if (c === '"') state = 'NORMAL';
            else if (c === '\\') { i += 2; continue; } // \" is a literal quote
        } else if (state === 'BACKTICK') {
            if (c === '`') state = 'NORMAL';
            else if (c === '\\') { i += 2; continue; }
        }
        i += 1;
    }
    return state === 'NORMAL';
}

function runCli() {
    const args = process.argv.slice(2);

    if (args.length === 0) {
        // Built-in self-tests (same signature as v1 -> drop-in)
        const cases = [
            ['echo "it\'s a test"',                       true],  // valid, was FALSE in v1
            ['powershell -Command "Write-Output \'Hello World\'"', true],
            ['it\\\'s a valid string with escaped quote',  true],
            ['powershell -Command "Write-Output \'Hello',  false], // real dangling (outer " never closed -> shell hangs)
            ['echo "hi',                                   false], // dangling double
            ['cat `unterminated',                          false], // dangling backtick
            ['echo "a\\""',                                true],  // escaped quote literal
            ['dir "C:\\temp"',                             true],
        ];
        console.log('=== Built-in Tests (v2) ===');
        let allOk = true;
        for (const [cmd, expected] of cases) {
            const got = verifyQuoteParity(cmd);
            const mark = got === expected ? 'OK  ' : 'FAIL';
            if (got !== expected) allOk = false;
            console.log(`  [${mark}] expected=${String(expected).padEnd(5)} got=${String(got).padEnd(5)}  ${cmd}`);
        }
        console.log(allOk ? 'ALL PASS' : 'SOME FAILED');
        return;
    }

    let command = '';
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '-c' || args[i] === '--command') {
            command = args[i + 1] || '';
            break;
        } else if (!args[i].startsWith('-')) {
            command = args[i];
            break;
        }
    }

    if (!command) {
        console.error('Error: No command provided to verify.');
        console.error('Usage: node parity_check.js -c "your command string"');
        process.exit(1);
    }

    if (verifyQuoteParity(command)) {
        console.log('PARITY OK — command is safe to execute.');
        process.exit(0);
    } else {
        console.error('PARITY VIOLATION — unterminated quote/backtick detected. Command blocked before shell execution!');
        process.exit(1);
    }
}

if (require.main === module) {
    runCli();
}

module.exports = { verifyQuoteParity };
