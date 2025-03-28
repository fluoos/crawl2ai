module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2021: true,
  },
  extends: [
    'plugin:vue/vue3-recommended',
    'eslint:recommended',
  ],
  parserOptions: {
    ecmaVersion: 2021,
  },
  plugins: [
    'vue',
    'unused-imports'
  ],
  rules: {
    'vue/multi-word-component-names': 'off',
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'unused-imports/no-unused-imports': 'error',
    'unused-imports/no-unused-vars': [
      'warn',
      { 'vars': 'all', 'varsIgnorePattern': '^_', 'args': 'after-used', 'argsIgnorePattern': '^_' }
    ],
    'no-unused-vars': ['error', { 
      'vars': 'all', 
      'args': 'after-used', 
      'ignoreRestSiblings': false 
    }],
    'vue/no-unused-components': 'error',
  },
}; 