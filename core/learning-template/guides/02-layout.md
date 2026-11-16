# トップフォルダの分け方と使い分け

[01-philosophy.md](./01-philosophy.md) の原則1（目的でトップフォルダを分ける）を、具体的な
フォルダパターンに落とし込む。`references/` には、ここで挙げる5パターンすべての最小構成例を置いてあるが、
**自分の学習目的に合わないパターンは採用しなくてよい**。最初は1〜2個から始めて、必要になったら増やす。

| フォルダ例 | 目的 | 中の構成 | `references/` 内の主要ファイル |
|---|---|---|---|
| `study/{topic}/{project}` | 実装して試しながら学ぶ | トピック→プロジェクト（ステップ）の二段階 | [study/AGENTS.md](../references/study/AGENTS.md)、[study/{topic}/AGENTS.md](../references/study/{topic}/AGENTS.md)、[PLAN.md](../references/study/{topic}/PLAN.md)、[{project}/README.md](../references/study/{topic}/{project}/README.md)、[KNOWLEDGE.md](../references/study/{topic}/{project}/KNOWLEDGE.md)、[questions/](../references/study/{topic}/{project}/questions/{question}.md) |
| `reading/{topic}/` | 座学・読み物として整理する（実装しない） | `overview/`（必須）＋`details/`（任意）＋`questions/`（任意） | [reading/AGENTS.md](../references/reading/AGENTS.md)、[{topic}/overview/README.md](../references/reading/{topic}/overview/README.md)、[01-{concept}.md](../references/reading/{topic}/overview/01-{concept}.md) |
| `sandbox/{topic}/{project}` | 外部の有料リソース・クラウドを使わず、ローカルだけで検証する | `study/` と同じ二段階構成 | [sandbox/AGENTS.md](../references/sandbox/AGENTS.md) |
| `build/{project}` | 学習の枠を超えて、実際に使うものを本気で作る | 標準構成をベースにしつつ自由度を認める（今後の拡張は `PLAN.md` ではなく `BACKLOG.md`） | [build/AGENTS.md](../references/build/AGENTS.md)、[{project}/README.md](../references/build/{project}/README.md)、[BACKLOG.md](../references/build/{project}/BACKLOG.md)、[NOTES.md](../references/build/{project}/NOTES.md) |
| `cheatsheet/{tool}/` | 学習記録ではない、素早く引ける操作リファレンス | ツール別サブフォルダ＋操作単位のファイル | [cheatsheet/AGENTS.md](../references/cheatsheet/AGENTS.md) |

`references/` はコピー先と同じ構造で並べてあるので、`references/` 内のパスがそのままコピー先のパスになる
（対応表と手順は [04-adapting.md](./04-adapting.md)）。

フォルダ名はあくまで例。ドメインに合わせて自由に変えてよい（例: `study/` の代わりに `practice/` や
`labs/`、`reading/` の代わりに `docs/` や `notes/` 等）。重要なのは名前ではなく、
**「実装するか／読むだけか」「クラウド等の外部依存があるか／ないか」「学習用か／実用目的か」を
フォルダの時点で分離する**という構造そのもの。

## 各パターンの選び方の目安

- まず `study/{topic}/{project}` だけで始めるのが最も汎用的。多くの学習リポジトリはこれだけで足りる。
- 座学的なインプット（公式ドキュメント整理・用語の座学まとめ）が実装作業と混ざって読みにくくなってきたら
  `reading/` を切り出す。
- 学習対象が有料クラウドや大掛かりな外部環境を要求し、「お金をかけずに動作原理だけ確認したい」需要が
  出てきたら `sandbox/` を切り出す。
- 学習の延長で実際に使い続けたいものができたら `build/` に移す。ここは標準構成に縛られすぎず、
  必要なドキュメント（例: 運用メモ、コスト記録、トラブルシューティング）を自由に増やしてよい
  （詳細は [`build/AGENTS.md`](../references/build/AGENTS.md)）。
- コマンドの叩き方をすぐ引きたいだけなら `cheatsheet/` に逃がす。**学習の経緯や解説を書かない**のが
  他のフォルダとの違い（書くと `study/` の役割と重複し、更新も二重管理になる）。

## ルート直下に必ず置くもの

トップフォルダの構成に関わらず、リポジトリのルート直下には次の3つを置く。

- `README.md` — 上表のようなトップフォルダの索引（人間向け）
- `AGENTS.md` — リポジトリ全体のルール（詳細は [03-agent-instructions.md](./03-agent-instructions.md)）
- `CLAUDE.md` — `AGENTS.md` への1行 import のみ

## 必須ファイル

採用したパターンごとに、各階層に置くファイルと置かないファイルは次のとおり。この表が正本で、
`lint_learning_repo.py` はこの表どおりかを検査する（表を変えたらスクリプトの `LAYOUT` も合わせる）。
任意のファイル（`PLAN.md`・`HISTORY.md`・`MERMAID.md`・`questions/`・`details/` など）は検査しない。

| 場所 | 必須 | 置かない |
|---|---|---|
| ルート | `README.md`・`AGENTS.md`・`CLAUDE.md` | |
| 採用したトップフォルダ（`study/` など） | `AGENTS.md`・`CLAUDE.md` | |
| `study/{topic}/`・`sandbox/{topic}/` | `AGENTS.md`・`CLAUDE.md` | |
| `study/{topic}/{project}/`・`sandbox/{topic}/{project}/` | `README.md`・`KNOWLEDGE.md` | `AGENTS.md`・`CLAUDE.md` |
| `reading/{topic}/` | `overview/README.md` | |
| `build/{project}/` | `README.md` | |

`study/{topic}/PLAN.md` は、`AGENTS.md` が長くなって分割するときに作るファイルなので必須にしない
（[03-agent-instructions.md](./03-agent-instructions.md)）。`build/{project}/BACKLOG.md` は推奨だが必須ではない。
