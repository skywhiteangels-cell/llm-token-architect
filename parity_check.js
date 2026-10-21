/**
 * Quote Parity Guardrail
 * Author: SkyAngel
 * Purpose: Pre-flight terminal command verification to prevent interactive shell deadlocks (>> in PowerShell/Bash).
 *
 * Usage:
 *   As a module:
 *     const { verifyQuoteParity } = require('./parity_check');
 *     const isSafe = verifyQuoteParity("your shell command here");
 *
 *   As a CLI tool:
 *     node parity_check.js -c "powershell -Command \"Write-Output 'Hello'\""
 *     node parity_check.js --command "dir 'C:\\Program Files'"
 *
 * Exit codes:
 *     0 — parity OK (safe to execute)
 *     1 — parity VIOLATION (odd quote count detected, block execution)
 */

function countUnescaped(text, char) {
    // Matches quotes not preceded by an unescaped backslash
    const regex = new RegExp(`(?<!\\\\)${char === '"' ? '"' : "'"}`, 'g');
    const matches = text.match(regex);
    return matches ? matches.length : 0;
}

function verifyQuoteParity(command) {
    if (typeof command !== 'string') return false;
    const singleQuotes = countUnescaped(command, "'");
    const doubleQuotes = countUnescaped(command, '"');

    return (singleQuotes % 2 === 0) && (doubleQuotes % 2 === 0);
}

function runCli() {
    const args = process.argv.slice(2);

    if (args.length === 0) {
        // Built-in self-tests
        const testOk = "powershell -Command \"Write-Output 'Hello World'\"";
        const testEscaped = "it\\'s a valid string with escaped quote";
        const testFail = "powershell -Command \"Write-Output 'Hello World\""; // intentionally broken

        console.log("=== Built-in Tests ===");
        console.log("Test OK       :", verifyQuoteParity(testOk));       // true
        console.log("Test Escaped  :", verifyQuoteParity(testEscaped));  // true
        console.log("Test Fail     :", verifyQuoteParity(testFail));     // false
        return;
    }

    let command = "";
    for (let i = 0; i < args.length; i++) {
        if (args[i] === "-c" || args[i] === "--command") {
            command = args[i + 1] || "";
            break;
        } else if (!args[i].startsWith("-")) {
            command = args[i];
            break;
        }
    }

    if (!command) {
        console.error("Error: No command provided to verify.");
        console.error("Usage: node parity_check.js -c \"your command string\"");
        process.exit(1);
    }

    const single = countUnescaped(command, "'");
    const double = countUnescaped(command, '"');

    if (verifyQuoteParity(command)) {
        console.log("PARITY OK — command is safe to execute.");
        process.exit(0);
    } else {
        console.error("PARITY VIOLATION — odd quote count detected. Command blocked before shell execution!");
        console.error(`  Single quotes (unescaped): ${single} (${single % 2 === 0 ? 'EVEN' : 'ODD'})`);
        console.error(`  Double quotes (unescaped): ${double} (${double % 2 === 0 ? 'EVEN' : 'ODD'})`);
        process.exit(1);
    }
}

if (require.main === module) {
    runCli();
}

module.exports = { verifyQuoteParity, countUnescaped };
