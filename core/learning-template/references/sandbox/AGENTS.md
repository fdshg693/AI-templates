このフォルダの概要は [README.md](README.md) を参照。

## 構成

- `sandbox/`
  - ローカル検証プロジェクトまとめ
- `sandbox/{topic}`
  - 各テーマ配下の検証プロジェクトまとめ
- `sandbox/{topic}/{project}`
  - 各プロジェクトの検証用フォルダ

`sandbox/{topic}` 配下のファイル構成（`AGENTS.md`／`HISTORY.md`／`PLAN.md` の役割分担）は、
ルートの [AGENTS.md](../AGENTS.md) の「ドキュメント管理」にある `study/{topic}/` と同じルールに従う。

## `sandbox/{topic}/{project}` 配下に置くファイル

各プロジェクト共通のファイル構成は、ルートの [AGENTS.md](../AGENTS.md) の「各プロジェクト共通ファイル構成」に準じる
（`justfile`／複雑なら `Taskfile` で操作をまとめ、`README.md` で手順と学習の流れ、`KNOWLEDGE.md` で
新出用語、必要なら `MERMAID.md`／`PLAN.md`）。

ただし、このフォルダは外部の有料リソース・クラウドを使わないため、環境構築用の IaC 設定ファイルは
置かない。代わりに、そのプロジェクトの実行に必要な最小限のソース一式
（例: `Dockerfile*`／`compose.yaml`／題材アプリの `app/` など）を置く。
