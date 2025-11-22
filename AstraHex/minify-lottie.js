import fs from "fs";

const input = "Spiral-flatten.json";
const output = "Spiral-flatten-opt.json";

// 读取原始文件
const raw = JSON.parse(fs.readFileSync(input, "utf8"));

// 函数：递归去掉重复 keyframes / 空数组 / null 值
function clean(obj) {
  if (Array.isArray(obj)) {
    return obj
      .map(clean)
      .filter((v, i, a) => v != null && JSON.stringify(v) !== JSON.stringify(a[i - 1]));
  } else if (typeof obj === "object" && obj !== null) {
    const newObj = {};
    for (const [k, v] of Object.entries(obj)) {
      if (v == null || (Array.isArray(v) && v.length === 0)) continue;
      newObj[k] = clean(v);
    }
    return newObj;
  }
  return obj;
}

// 删除 metadata 和未使用 assets
delete raw.assets?.meta;
if (raw.assets) {
  raw.assets = raw.assets.filter(a => a && a.p);
}

console.time("Optimize");
const optimized = clean(raw);
fs.writeFileSync(output, JSON.stringify(optimized));
console.timeEnd("Optimize");

console.log(`✅ 优化完成: ${output}`);
