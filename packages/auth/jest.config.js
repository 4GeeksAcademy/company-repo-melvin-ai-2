/** @type {import("jest").Config} */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  testMatch: ["**/*.test.ts"],
  collectCoverageFrom: ["token.ts", "client.ts"],
  coveragePathIgnorePatterns: ["/node_modules/"],
};
