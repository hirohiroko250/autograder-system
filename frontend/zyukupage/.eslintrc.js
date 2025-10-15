module.exports = {
  root: true,
  extends: [
    'next/core-web-vitals',
    'prettier',
  ],
  rules: {
    'no-console': 'warn',
    'no-debugger': 'warn',
    '@typescript-eslint/no-unused-vars': 'warn',
  },
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
};