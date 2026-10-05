---
name: flutter-core
description: Flutter/Dart 核心技术速查手册
version: 1.0.0
category: imported
tags: ["flutter", "dart", "widget", "state-management", "async", "isolate"]
metadata:
  hermes:
    tags: ["flutter", "dart", "widget", "state-management", "async", "isolate"]
    source: IMA 知识库导入
---

# flutter-core

> Flutter/Dart 核心技术速查手册。涵盖 Dart 类型系统、异步编程、Isolate 并发、Widget 体系、状态管理、性能优化、混合开发、全栈集成（API+存储+推送）。当用户问 Flutter/Dart 相关问题、需要 Flutter 代码、状态管理、性能优化、全栈集成时激活。

# Flutter/Dart 核心技术速查手册

> 从 6 个学习模块中精炼提取，覆盖 Flutter 技术栈核心知识，附实战全栈集成模式。

## 快速导航

| **模块**       | **知识点**                              | **速查**                        |
| ------------ | ------------------------------------ | ----------------------------- |
| M1 Dart 进阶   | 类型系统、泛型、异步、Isolate                   | [展开](#m1-dart-语言进阶)           |
| M2 Widget 体系 | Stateless/Stateful、生命周期、BuildContext | [展开](#m2-widget-体系)           |
| M3 状态管理      | Provider、Riverpod、BLoC、GetX          | [展开](#m3-状态管理)                |
| M4 性能优化      | 渲染管线、const 构造、RepaintBoundary        | [展开](#m4-性能优化)                |
| M5 混合开发      | Platform Channel、FFI、WebView         | [展开](#m5-混合开发)                |
| M6 工程化       | 路由、依赖注入、CI/CD                        | [展开](#m6-工程化)                 |
| M7 全栈集成      | API 联调、本地存储、推送通知                     | [展开](#m7-全栈集成api--本地存储--推送通知) |

***

## M1: Dart 语言进阶

### 类型系统速查

```dart
// 空安全
String? nullable;   // 可以为 null
String nonNull;     // 不能为 null
int! lateVar;       // late 初始化

// 类型推断 + 泛型
var list = <String>[];  // 推断为 List<String>
Map<String, int> scores = {};

// Dart 3 Record
(int, String) pair = (42, 'hello');
({int x, int y}) point = (x: 3, y: 5);

// Dart 3 Pattern
switch (obj) {
  case int n when n > 0: print('positive $n');
  case String s: print('string $s');
  case (int x, int y): print('point ($x,$y)');
  default: print('unknown');
}
```

### 异步编程

```dart
// Future
Future<String> fetchData() async {
  final response = await http.get(Uri.parse(url));
  return response.body;
}

// Stream
Stream<int> countStream(int max) async* {
  for (int i = 0; i < max; i++) {
    await Future.delayed(Duration(seconds: 1));
    yield i;
  }
}

// 并发等待
final (users, posts) = await Future.wait([
  fetchUsers(),
  fetchPosts(),
]);

// Stream 操作
stream
  .where((e) => e.isValid)
  .map((e) => e.toJson())
  .listen(onData);
```

### Isolate 并发

```dart
// 计算密集型任务用 Isolate
Future<HeavyResult> computeHeavy(HeavyInput input) async {
  return await Isolate.run(() => heavyComputation(input));
}

// 长运行 Isolate
final receivePort = ReceivePort();
await Isolate.spawn(isolatedWorker, receivePort.sendPort);
receivePort.listen((msg) => print('from isolate: $msg'));
```

***

## M2: Widget 体系

### Widget 分类速查

| **类型**               | **特点**  | **场景**           |
| -------------------- | ------- | ---------------- |
| `StatelessWidget`    | 无状态,纯展示 | 文本、图标、静态布局       |
| `StatefulWidget`     | 有状态,可变  | 计数器、表单、动画        |
| `InheritedWidget`    | 向下传递数据  | Theme、MediaQuery |
| `RenderObjectWidget` | 自定义渲染   | 自定义绘制            |

### StatefulWidget 生命周期

```
createState() → initState() → didChangeDependencies()
→ build() → [状态变化 → didUpdateWidget() → build()]
→ deactivate() → dispose()
```

**关键规则：**

* `initState`：初始化一次的操作（订阅、初始化数据）
* `didUpdateWidget`：父 Widget 重建，配置变化时响应
* `dispose`：清理资源（取消订阅、关闭控制器）
* **不要在 build 中做耗时操作或修改状态**

### BuildContext 使用

```dart
// ✅ 正确: 在回调中使用
ElevatedButton(
  onPressed: () {
    Navigator.of(context).push(...);  // 回调中用 context
  },
)

// ❌ 错误: 在 build 中直接使用 context 做复杂操作
@override
Widget build(BuildContext context) {
  final media = MediaQuery.of(context);  // ✅ 读取数据
  Navigator.of(context).push(...);  // ❌ 不要在 build 中导航
  return ...;
}
```

***

## M3: 状态管理

### 方案对比

| **方案**       | **复杂度** | **性能** | **场景**    |
| ------------ | ------- | ------ | --------- |
| **setState** | ⭐       | ✅ 高    | 局部状态      |
| **Provider** | ⭐⭐      | ✅ 高    | 官方推荐,中等项目 |
| **Riverpod** | ⭐⭐      | ✅ 高    | 编译安全,大型项目 |
| **BLoC**     | ⭐⭐⭐     | ✅ 高    | 复杂业务逻辑    |
| **GetX**     | ⭐       | ⚠️ 中   | 快速开发,小项目  |

### Provider 模式

```dart
// 定义
class CounterNotifier extends ChangeNotifier {
  int _count = 0;
  int get count => _count;
  void increment() { _count++; notifyListeners(); }
}

// 提供
ChangeNotifierProvider(
  create: (_) => CounterNotifier(),
  child: MyApp(),
)

// 消费
Consumer<CounterNotifier>(
  builder: (_, counter, __) => Text('${counter.count}'),
)
```

### BLoC 模式

```dart
// 事件 → 状态
class CounterBloc extends Bloc<CounterEvent, int> {
  CounterBloc() : super(0) {
    on<Increment>((event, emit) => emit(state + 1));
    on<Decrement>((event, emit) => emit(state - 1));
  }
}

// 使用
BlocBuilder<CounterBloc, int>(
  builder: (_, count) => Text('$count'),
)
```

***

## M4: 性能优化

### 渲染管线优化

```
Widget → Element → RenderObject → Layer → GPU
  ↑         ↑          ↑
重建代价: 低    中      高
```

### 优化清单

```dart
// 1. const 构造（最大优化）
const Text('Hello')     // 只创建一次
Text('Hello')           // 每次 build 都创建

// 2. RepaintBoundary（隔离重绘）
RepaintBoundary(
  child: ComplexWidget(),  // 子树重绘不影响父树
)

// 3. ListView.builder（懒加载）
ListView.builder(
  itemCount: 10000,
  itemBuilder: (_, i) => ListTile(title: Text('Item $i')),
)

// 4. 避免不必要的 rebuild
// 用 Selector 替代 Consumer（Riverpod）
Selector<User, String>(
  selector: (_, user) => user.name,
  builder: (_, name, __) => Text(name),
)

// 5. 图片优化
Image.network(url, cacheWidth: 300, cacheHeight: 200)  // 指定缓存尺寸
cachedNetworkImageProvider(url)  // cached_network_image
```

### 性能检查命令

```bash
# 性能面板
flutter run --profile

# 检查 rebuild 次数
flutter run --track-widget-creation

# DevTools
flutter run --start-paited
# 打开 DevTools → Performance / Memory / Widget Ins
```

## 触发条件

Flutter/Dart 核心技术速查手册。涵盖 Dart 类型系统、异步编程、Isolate 并发、Widget 体系、状态管理、性能优化、混合开发、全栈集成（API+存储+推送）。当用户问 Flutter/Dart 相关问题、需要 Flutter 代码、状态管理、性能优化、全栈集成时激活。
## 验证

- [ ] 按上述步骤执行成功
- [ ] 输出符合预期，无报错
