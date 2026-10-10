import assert from "node:assert/strict";
import test from "node:test";

import { translate } from "../src/i18n.tsx";

test("Chinese locale translates interface copy", () => {
  assert.equal(translate("Knowledge Explorer", "zh-CN"), "知识探索");
  assert.equal(translate("Search graph nodes", "zh-CN"), "搜索图谱节点");
  assert.equal(translate("Edge Labels", "zh-CN"), "关系标签");
});

test("English locale keeps the original interface copy", () => {
  assert.equal(translate("Knowledge Explorer", "en-US"), "Knowledge Explorer");
});

test("technical graph values remain unchanged", () => {
  for (const value of ["calls", "declared_in", "implements", "JsthoController", "source_path"]) {
    assert.equal(translate(value, "zh-CN"), value);
  }
});
