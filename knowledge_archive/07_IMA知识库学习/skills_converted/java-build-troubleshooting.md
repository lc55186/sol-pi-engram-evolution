---
name: java-build-troubleshooting
description: 针对 Java 多模块 Maven 项目的常见编译错误、测试失败、依赖管理问题的系统化排查方法
version: 1.0.0
category: devops
tags: ["Java", "Maven", "编译错误", "测试失败", "Mockito", "enforcer"]
metadata:
  hermes:
    tags: ["Java", "Maven", "编译错误", "测试失败", "Mockito", "enforcer"]
    source: IMA 知识库导入
---

# java-build-troubleshooting

> 针对 Java 多模块 Maven 项目的常见编译错误、测试失败、依赖管理问题的系统化排查方法。覆盖 enforcer 插件版本冲突、Missing Symbol 错误、Mockito mock 不完整、jar 类加载冲突等典型故障模式。当用户遇到 mvn compile/test 失败、找不到符号、测试 mock NPE、多模块依赖链构建问题时激活。

# Java/Maven 多模块项目构建问题排查手册

## 快速诊断流程

```bash
1. 编译失败 → mvn compile -Denforcer.skip=true 2>&1 | grep -E "ERROR|找不到"
2. 测试失败 → mvn test -pl <module> -Denforcer.skip=true 2>&1 | grep -E "FAIL|ERROR|Tests run"
3. 安装失败 → mvn install -pl <module> -DskipTests -Djacoco.skip=true
4. 依赖链 → mvn install -N && mvn install -pl ai-apm-ingest -am -DskipTests
```

## 常见故障模式

### 1. Missing Symbol（找不到符号）

**现象**: `mvn compile` 报 `找不到符号: 变量 AlertNotifier`**根因**: 新文件引用了未实现的类 / import 路径错误 / 类存在于另一模块但未添加依赖

**排查**:

```bash
mvn compile 2>&1 | grep -E "ERROR" -A5
find . -name "AlertNotifier.java" -not -path "*/target/*"
```

**修复**: 创建缺失类 或 确认 pom.xml 包含对应模块依赖

### 2. Mockito Mock 不完整导致 NPE

**现象**: 单元测试通过编译但运行时报 `NullPointerException`**根因**: ResultSet 等方法的部分列未被 mock，返回 null

**修复**:

```java
// ✅ 补全所有列或使用通配符
when(rs.getTimestamp(anyString())).thenReturn(null);
// 或
when(rs.getTimestamp("updated_at")).thenReturn(null);
```

### 3. maven-enforcer-plugin 版本冲突

**现象**: `mvn test` 报 `RequireJavaVersion failed`**根因**: POM 硬编码 `[17,18)` 但环境是 JDK 21

**修复**:

```bash
mvn test -Denforcer.skip=true  # 临时
# 或修改 pom.xml: <version>[17,)</version>  # 正式
```

**关键认知**: enforcer 是编译期检查，不影响运行时。

### 4. 多模块依赖链构建失败

**修复顺序**:

```bash
mvn install -N -DskipTests           # 父 POM
cd ai-apm-common && mvn install -DskipTests -Djacoco.skip=true
cd ../ai-apm-ingest && mvn install -DskipTests -Djacoco.skip=true
# 或一次性:
mvn install -pl ai-apm-ingest -am -DskipTests
```

### 5. Fat JAR 类加载冲突

**现象**: 启动报 `NoClassDefFoundError`**修复**: 完整重新打包 `mvn clean package -DskipTests -pl springboot -am`，不要单独替换子模块 class

## Pitfalls 检查清单

- [ ] 编译错误 → 先确认 java -version 和 enforcer 配置

- [ ] 测试失败 → 检查 mock 是否覆盖所有 DB 列

- [ ] 多模块构建 → 按依赖顺序安装：父 POM → common → 下游

- [ ] Fat JAR 冲突 → 完整 repackage，不单独替换子模块

- [ ] 依赖缺失 → grep -r "import.*Classname" src/ 定位引用

## 相关 Skill 引用

* **deployment-troubleshooting**: 第 25/25a 节（多模块 Maven 构建、enforcer 插件版本）
* **deployment-troubleshooting**: 第 13/14 节（maven-dependency-plugin unpack 冲突）
* **self-heal**: 修复后验证模式（`jar tf` 检查类存在性）

## 触发条件

针对 Java 多模块 Maven 项目的常见编译错误、测试失败、依赖管理问题的系统化排查方法。覆盖 enforcer 插件版本冲突、Missing Symbol 错误、Mockito mock 不完整、jar 类加载冲突等典型故障模式。当用户遇到 mvn compile/test 失败、找不到符号、测试 mock NPE、多模块依赖链构建问题时激活。
