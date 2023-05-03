'use strict';

// Naming conventions
function validInline(validArgument) { return validArgument; }
let validVariable = validInline(1);
function validWithArrow() {
    return (validArgument) => validArgument;
}

// Control flows
// and multiline comments
if (validVariable) validVariable = validInline(2);

if (validVariable === 1) {
    validVariable = validWithArrow()(2);
} else if (validVariable === 3) {
    validVariable = 4;
}
