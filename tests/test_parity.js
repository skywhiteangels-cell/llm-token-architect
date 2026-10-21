/**
 * Test suite for Quote Guard v3 (Node.js).
 *
 * No dependencies: plain `node tests/test_parity.js`.
 * Exit code 0 = all green, 1 = failures.
 */

const path = require('path');
const { verifyQuoteParity, analyze, SHELLS } = require(path.join(__dirname, '..', 'parity_check.js'));

const failures = [];
let checks = 0;

function check(label, got, expected) {
    checks += 1;
    if (JSON.stringify(got) !== JSON.stringify(expected)) {
        failures.push(`${label}\n     expected: ${JSON.stringify(expected)}\n     got:      ${JSON.stringify(got)}`);
    }
}

// ---------------------------------------------------------------------------
// 1. Grammar tables per shell   [shell, command, expectedSafe, why]
// ---------------------------------------------------------------------------
const GRAMMAR_CASES = [
    // --- posix -------------------------------------------------------------
    ['posix', 'echo "it\'s a test"', true, 'single quote is literal inside double quotes'],
    ['posix', 'echo "hi', false, 'unterminated double quote'],
    ['posix', "echo 'hi", false, 'unterminated single quote'],
    ['posix', 'cat `unterminated', false, 'unterminated command substitution'],
    ['posix', 'echo "a\\""', true, 'escaped quote inside double quotes is literal'],
    ['posix', 'dir "C:\\temp"', true, 'backslash before a normal char is harmless'],
    ['posix', 'dir "C:\\"', false, 'backslash escapes the closing quote -> hangs'],
    ['posix', "echo 'it'\\''s'", true, 'classic POSIX literal-quote idiom'],
    ['posix', 'echo foo\\', false, 'trailing backslash is a line continuation'],
    ['posix', 'echo "a" && echo "b"', true, 'two balanced pairs'],
    // --- powershell --------------------------------------------------------
    ['powershell', 'dir "C:\\"', true, 'backslash is LITERAL in PowerShell (v2 bug)'],
    ['powershell', 'dir "C:\\temp\\"', true, 'trailing backslash is literal'],
    ['powershell', 'echo "a`"b"', true, 'backtick escapes the quote'],
    ['powershell', 'echo "hi', false, 'unterminated double quote'],
    ['powershell', "echo 'it''s'", true, "'' is a literal quote in PS"],
    ['powershell', "echo 'it's'", false, "second ' opens a new unterminated string"],
    ['powershell', 'Write-Output "unterminated', false, 'unterminated double quote'],
    ['powershell', 'echo `n', true, 'escape sequence, no quote context'],
    ['powershell', 'echo hi`', false, 'trailing backtick is a line continuation'],
    ['powershell', 'powershell -Command "echo `"hi`""', true, 'nested backtick escapes'],
    // --- cmd ---------------------------------------------------------------
    ['cmd', 'echo "hi', false, 'unterminated double quote'],
    ['cmd', 'echo "a\\"', true, 'backslash is literal in cmd'],
    ['cmd', 'echo ^"hi', true, '^ escapes the quote'],
    ['cmd', 'echo hi^', false, 'trailing caret is a line continuation'],
];

for (const [shell, cmd, expected, why] of GRAMMAR_CASES) {
    check(`[${shell}] ${cmd}  (${why})`, verifyQuoteParity(cmd, shell), expected);
}

// ---------------------------------------------------------------------------
// 2. Same string, different shells, different verdicts — the point of v3.
// ---------------------------------------------------------------------------
check('posix  dir "C:\\" is unsafe', verifyQuoteParity('dir "C:\\"', 'posix'), false);
check('powershell dir "C:\\" is safe', verifyQuoteParity('dir "C:\\"', 'powershell'), true);

// ---------------------------------------------------------------------------
// 3. analyze() contract
// ---------------------------------------------------------------------------
let r = analyze('echo "hi', 'posix');
check('analyze returns safe=false', r.safe, false);
check('analyze reports the state', r.state, 'DOUBLE');
check('analyze reports the offset', r.offset, 5);
check('analyze echoes the shell', r.shell, 'posix');
check('analyze has a reason string', typeof r.reason === 'string' && r.reason.length > 0, true);

r = analyze('echo foo\\', 'posix');
check('dangling escape has its own state', r.state, 'ESCAPE');

r = analyze('echo hi', 'powershell');
check('clean command is NORMAL', r.state, 'NORMAL');
check('clean command has no offset', r.offset, null);

// ---------------------------------------------------------------------------
// 4. Defensive behaviour
// ---------------------------------------------------------------------------
check('non-string input is refused', verifyQuoteParity(null), false);
check('empty string is safe', verifyQuoteParity(''), true);

let threw = false;
try { analyze('echo hi', 'fish'); } catch (e) { threw = true; }
check('unknown shell throws', threw, true);

check('SHELLS is stable', SHELLS, ['posix', 'powershell', 'cmd']);

// ---------------------------------------------------------------------------
// 5. Idempotence
// ---------------------------------------------------------------------------
const sample = 'powershell -Command "Write-Output \'Hello\'"';
const results = new Set(Array.from({ length: 50 }, () => verifyQuoteParity(sample, 'powershell')));
check('idempotent over 50 runs', results.size, 1);

// ---------------------------------------------------------------------------
if (failures.length) {
    console.log(`=== FAILED: ${failures.length} of ${checks} checks ===`);
    for (const f of failures) console.log('  - ' + f);
    process.exit(1);
}

console.log(`=== ALL PASS: ${checks} checks across ${GRAMMAR_CASES.length} grammar cases ===`);
process.exit(0);
