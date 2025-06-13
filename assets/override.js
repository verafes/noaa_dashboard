console.log("override.js loaded!");

const originalWarn = console.warn;
console.warn = function(...args) {
  if (/defaultProps|componentWillMount|componentWillReceiveProps/.test(args[0])) {
    return;
  }
  originalWarn.apply(console, args);
};

console.warn = function () {};
console.error = function () {};