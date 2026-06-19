import js from "@eslint/js";
import nextPlugin from "eslint-config-next";
import globals from "globals";
import tseslint from "typescript-eslint";

const config = [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...nextPlugin,
  {
    files: ["**/*.{ts,tsx,js,jsx}"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },
  {
    ignores: [".next/**", "node_modules/**"],
  },
];

export default config;
