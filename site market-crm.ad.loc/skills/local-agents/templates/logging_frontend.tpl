// Frontend logging helper (small wrapper for console while developing)
// Usage:
//   import { makeLogger } from './logging_frontend.tpl'
//   const logger = makeLogger('ClientTable')
//   logger.info('render', { rows: data.length })

export function makeLogger(component) {
  function format(msg, meta) {
    return `${component} — ${msg}`
  }

  return {
    info: (msg, meta = {}) => console.info(format(msg, meta), meta),
    warn: (msg, meta = {}) => console.warn(format(msg, meta), meta),
    error: (msg, meta = {}) => console.error(format(msg, meta), meta),
  }
}

// Example: in a React component
// const logger = makeLogger('TableTemplate')
// logger.info('mounted', { pageSize })
